from abc import ABC, abstractmethod
import pygame
import json
import math
import random

# --- Constantes de la Simulación ---
SIM_WIDTH = 800
SCREEN_HEIGHT = 700

# --- Constantes para la Gestión de Recursos ---
CELL_SIZE = 20
MAX_HIERBA_NORMAL = 70
MAX_HIERBA_PRADERA = 120

# --- Clases del Entorno ---

class Terreno:
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)

class Carcasa:
    def __init__(self, x, y, energia_restante=60):
        self.x = x
        self.y = y
        self.energia_restante = energia_restante
        self.dias_descomposicion = 0

class Pez:
    def __init__(self, rio_origen):
        self.rio = rio_origen
        self.x = random.randint(self.rio.rect.left, self.rio.rect.right)
        self.y = random.randint(self.rio.rect.top, self.rio.rect.bottom)
        self.velocidad = 2

    def moverse(self):
        self.x += random.randint(-self.velocidad, self.velocidad)
        self.y += random.randint(-self.velocidad, self.velocidad)
        self.x = max(self.rio.rect.left, min(self.x, self.rio.rect.right))
        self.y = max(self.rio.rect.top, min(self.y, self.rio.rect.bottom))

class Rio(Terreno):
    def __init__(self, rect):
        super().__init__(rect)
        self.peces: list[Pez] = []
        for _ in range(15):
            self.peces.append(Pez(self))

    def crecer_recursos(self, factor_crecimiento):
        if len(self.peces) < 50:
            for _ in range(int(1 * factor_crecimiento)):
                self.peces.append(Pez(self))

class Selva(Terreno):
    def __init__(self, rect):
        super().__init__(rect)
        self.bayas = 25

    def crecer_recursos(self, factor_crecimiento):
        self.bayas += int(2 * factor_crecimiento)

class Pradera(Terreno):
    pass


# --- Clases del Modelo ---

class Animal(ABC):
    contador = 0

    def __init__(self, nombre: str, x: int, y: int, edad: int = 0, energia: int = 100, max_energia=None):
        self._nombre = nombre
        self.x = x
        self.y = y
        self._edad = max(0, edad)
        self._energia = max(0, min(energia, 100))
        self._sed = 0
        if max_energia is None:
            max_energia = max(80, min(120, 100 + random.randint(-10, 10)))
        self.max_energia = max_energia
        self._esta_vivo = True
        type(self).contador = getattr(type(self), 'contador', 0) + 1

    @property
    def nombre(self):
        return self._nombre

    @property
    def edad(self):
        return self._edad

    @property
    def energia(self):
        return self._energia

    @property
    def esta_vivo(self):
        return self._esta_vivo

    @abstractmethod
    def comer(self, ecosistema) -> str:
        pass

    def moverse(self, ecosistema: 'Ecosistema') -> str:
        # Movimiento aleatorio simple
        dx = random.randint(-5, 5)
        dy = random.randint(-5, 5)
        
        nuevo_x = max(0, min(self.x + dx, SIM_WIDTH - 1))
        nuevo_y = max(0, min(self.y + dy, SCREEN_HEIGHT - 1))

        # Evitar chocar con obstáculos (simplificado)
        if not ecosistema.choca_con_terreno(nuevo_x, nuevo_y):
            self.x = nuevo_x
            self.y = nuevo_y

        # Consumir energía por moverse
        coste_movimiento = 1 + ecosistema.estaciones[ecosistema.estacion_actual]['coste_energia']
        self._energia -= coste_movimiento
        self._sed += 1
        return ""

    def envejecer(self, ecosistema: 'Ecosistema') -> str:
        self._edad += 1
        # Penalización de energía por envejecer
        self._energia -= 2
        return self.verificar_estado(ecosistema)

    def verificar_estado(self, ecosistema: 'Ecosistema') -> str:
        if self._esta_vivo and (
            self._energia <= 0 or 
            self._sed >= 150 or 
            self._edad > 100 or
            not 0 <= self.x < SIM_WIDTH or 
            not 0 <= self.y < SCREEN_HEIGHT  # Añadir verificación de límites
        ):
            self._esta_vivo = False
            ecosistema.agregar_carcasa(self.x, self.y)
            return f" -> ¡{self._nombre} ha muerto!"
        return ""

    def reproducirse(self, ecosistema: 'Ecosistema') -> str:
        # Condición simple para reproducirse
        if self.edad > 5 and self.energia > self.max_energia * 0.8 and random.random() < 0.1:
            # Crear una cría del mismo tipo
            cría = type(self)(f"{self.nombre} Jr.", self.x, self.y)
            ecosistema.animales_nuevos.append(cría)
            self._energia -= 40 # Coste energético de la reproducción
            return f"{self.nombre} se ha reproducido."
        return ""

    def __str__(self):
        estado = "Vivo" if self._esta_vivo else "Muerto"
        return f"Animal: {self._nombre}, Tipo: {self.__class__.__name__}, Edad: {self._edad}, Energía: {self._energia}, Estado: {estado}"

class Herbivoro(Animal):
    def comer(self, ecosistema) -> str:
        # Los herbívoros comen hierba si tienen hambre
        if self.energia < self.max_energia * 0.8:
            grid_x = int(self.x // CELL_SIZE)
            grid_y = int(self.y // CELL_SIZE)
            
            # Asegurarse de que las coordenadas están dentro de los límites del grid
            if 0 <= grid_x < ecosistema.grid_width and 0 <= grid_y < ecosistema.grid_height:
                if ecosistema.grid_hierba[grid_x][grid_y] > 0:
                    comido = min(ecosistema.grid_hierba[grid_x][grid_y], 10)
                    self._energia += comido * 2 # La hierba da energía
                    self._energia = min(self._energia, self.max_energia)
                    ecosistema.grid_hierba[grid_x][grid_y] -= comido
                    return f"{self.nombre} comió hierba."
        return ""

class Carnivoro(Animal):
    def comer(self, ecosistema) -> str:
        # Los carnívoros cazan otros animales si tienen hambre
        if self.energia < self.max_energia * 0.7:
            # Optimización: en lugar de comprobar todos, comprueba una muestra aleatoria de presas cercanas.
            posibles_presas = random.sample(ecosistema.animales, min(len(ecosistema.animales), 15))
            for presa in posibles_presas:
                # No se cazan a sí mismos, ni a otros carnívoros, y la presa debe estar viva
                if presa is not self and not isinstance(presa, Carnivoro) and presa.esta_vivo:
                    distancia = math.sqrt((self.x - presa.x)**2 + (self.y - presa.y)**2)
                    # Si la presa está lo suficientemente cerca
                    if distancia < 15: # Rango de caza
                        presa._esta_vivo = False # La presa muere
                        ecosistema.agregar_carcasa(presa.x, presa.y)
                        self._energia += 50  # Ganancia de energía por cazar
                        self._energia = min(self._energia, self.max_energia)
                        return f"{self.nombre} cazó a {presa.nombre}."
        return ""

class Omnivoro(Animal):
    def comer(self, ecosistema) -> str:
        if self.energia < self.max_energia * 0.7:
            # Intentar comer bayas primero
            for selva in ecosistema.terreno["selvas"]:
                if selva.rect.collidepoint(self.x, self.y) and selva.bayas > 0:
                    energia_ganada = min(20, selva.bayas * 2)
                    self._energia = min(self.max_energia, self._energia + energia_ganada)
                    selva.bayas = max(0, selva.bayas - 10)
                    return f"{self.nombre} comió bayas."
            
            # Si no hay bayas, intentar cazar
            animales_cercanos = ecosistema.obtener_animales_cercanos(self.x, self.y)
            for presa in animales_cercanos:
                if (presa is not self and not isinstance(presa, (Carnivoro, Omnivoro)) 
                    and presa.esta_vivo and self._puede_cazar(presa)):
                    presa._esta_vivo = False
                    ecosistema.agregar_carcasa(presa.x, presa.y)
                    self._energia = min(self.max_energia, self._energia + 40)
                    return f"{self.nombre} cazó a {presa.nombre}."
        return ""

    def _puede_cazar(self, presa):
        distancia = math.sqrt((self.x - presa.x)**2 + (self.y - presa.y)**2)
        return distancia < 15 and self.energia > 30

# --- Clases de Animales Específicos ---

# --- Herbívoros ---
class Conejo(Herbivoro):
    pass

class Cabra(Herbivoro):
    pass

class Raton(Herbivoro):
    def __init__(self, nombre: str, x: int, y: int, edad: int = 0, energia: int = 100, max_energia=None):
        if max_energia is None:
            max_energia = max(30, min(50, 40 + random.randint(-5, 5)))
        super().__init__(nombre, x, y, edad, energia, max_energia)

class Insecto(Herbivoro):
    def __init__(self, nombre: str, x: int, y: int, edad: int = 0, energia: int = 100, max_energia=None):
        if max_energia is None:
            max_energia = max(30, min(50, 40 + random.randint(-5, 5)))
        super().__init__(nombre, x, y, edad, energia, max_energia)

# --- Carnívoros ---
class Leopardo(Carnivoro):
    pass

class Gato(Carnivoro):
    pass

class Halcon(Carnivoro):
    pass

# --- Omnívoros ---
class Cerdo(Omnivoro):
    pass

class Mono(Omnivoro):
    pass

class Ecosistema:
    def __init__(self):
        self.animales: list[Animal] = []
        self.terreno = {
            "praderas": [
                Pradera((20, 400, 150, 150)),
                Pradera((300, 50, 250, 100)),
                Pradera((50, 50, 100, 150)),
                Pradera((600, 400, 150, 120)),
                Pradera((250, 200, 200, 50)),
                Pradera((20, 560, 180, 120)),
                Pradera((650, 550, 130, 130))  # Nueva pradera en la esquina inferior derecha
            ],
            "rios": [
                Rio((150, 0, 40, 300)),
                Rio((150, 150, 100, 40)),
                Rio((450, 0, 40, 250)),
                Rio((450, 210, 200, 40)),
                Rio((610, 210, 40, 490)),     # Río principal vertical
                Rio((0, 400, 610, 40))       # Afluente oeste
            ],
            "selvas": [
                Selva((200, 450, 250, 180)),
                Selva((20, 20, 100, 100)),
                Selva((500, 250, 150, 100)),
                Selva((700, 20, 80, 250)),
                Selva((550, 50, 200, 200)),
                Selva((20, 200, 120, 150))
            ],
            "arboles": [],
            "plantas": [],
        }
        # --- Nuevo sistema de recursos ---
        self.recursos = {
            "carcasas": []
        }
        self.grid_width = SIM_WIDTH // CELL_SIZE
        self.grid_height = SCREEN_HEIGHT // CELL_SIZE
        self.grid_hierba = [[0 for _ in range(self.grid_height)] for _ in range(self.grid_width)]

        for gx in range(self.grid_width):
            for gy in range(self.grid_height):
                max_val = MAX_HIERBA_NORMAL
                if any(p.rect.collidepoint(gx * CELL_SIZE, gy * CELL_SIZE) for p in self.terreno["praderas"]):
                    max_val = MAX_HIERBA_PRADERA
                self.grid_hierba[gx][gy] = random.randint(0, max_val)

        # --- Estaciones y Clima ---
        self.dia_total = 0
        self.hora_actual = 0
        self.dias_por_estacion = 20
        self.estacion_actual = "Primavera"
        self.estaciones = {
            "Primavera": {"crecimiento": 2.0, "coste_energia": 0},
            "Verano":    {"crecimiento": 1.0, "coste_energia": 0.5},
            "Otoño":     {"crecimiento": 0.5, "coste_energia": 1},
            "Invierno":  {"crecimiento": 0.1, "coste_energia": 1.5}
        }
        self.clima_actual = "Normal"

        self.animales_nuevos = []

        self.grid_animales = {}  # Añadir diccionario para grid de animales

        self._poblar_decoraciones()

    def choca_con_terreno(self, x, y):
        radio_tronco = 5
        return any(math.sqrt((ax - x)**2 + (ay - y)**2) < radio_tronco for ax, ay in self.terreno["arboles"])

    def agregar_carcasa(self, x, y):
        if not self.choca_con_terreno(x, y):
            nueva_carcasa = Carcasa(x, y)
            self.recursos["carcasas"].append(nueva_carcasa)
    
    def _es_posicion_valida_para_vegetacion(self, x, y, decoraciones_existentes, min_dist):
        if any(rio.rect.collidepoint(x, y) for rio in self.terreno["rios"]):
            return False
        return self._es_posicion_decoracion_valida(x, y, decoraciones_existentes, min_dist)

    def _es_posicion_decoracion_valida(self, x, y, decoraciones_existentes, min_dist):
        for dx, dy in decoraciones_existentes:
            dist = math.sqrt((x - dx)**2 + (y - dy)**2)
            if dist < min_dist:
                return False
        return True

    def _poblar_decoraciones(self):
        self.terreno["arboles"].clear()
        self.terreno["plantas"].clear()
        
        decoraciones_todas = []
        intentos_max = 80
        margen = 5

        for selva in self.terreno["selvas"]:
            for _ in range(35):
                for _ in range(intentos_max):
                    x = random.randint(selva.rect.left + margen, selva.rect.right - margen)
                    y = random.randint(selva.rect.top + margen, selva.rect.bottom - margen)
                    if self._es_posicion_valida_para_vegetacion(x, y, decoraciones_todas, min_dist=35):
                        self.terreno["arboles"].append((x, y)); decoraciones_todas.append((x, y))
                        break

        zonas_alimento = self.terreno["praderas"] + self.terreno["selvas"]
        for zona in zonas_alimento:
            for _ in range(35):
                for _ in range(intentos_max):
                    x = random.randint(zona.rect.left + margen, zona.rect.right - margen)
                    y = random.randint(zona.rect.top + margen, zona.rect.bottom - margen)
                    if self._es_posicion_valida_para_vegetacion(x, y, decoraciones_todas, min_dist=20):
                        self.terreno["plantas"].append((x, y)); decoraciones_todas.append((x, y))
                        break

        for _ in range(120):
            for _ in range(intentos_max):
                x, y = random.randint(0, SIM_WIDTH), random.randint(0, SCREEN_HEIGHT)
                if not self.choca_con_terreno(x,y) and self._es_posicion_valida_para_vegetacion(x, y, decoraciones_todas, min_dist=20):
                    self.terreno["plantas"].append((x, y)); decoraciones_todas.append((x, y))
                    break

    def _actualizar_estacion(self):
        indice_estacion = (self.dia_total // self.dias_por_estacion) % 4
        self.estacion_actual = list(self.estaciones.keys())[indice_estacion]

    def _actualizar_clima(self):
        if random.random() < 0.05:
            self.clima_actual = "Sequía"
        else:
            self.clima_actual = "Normal"

    def _actualizar_grid_animales(self):
        """Actualiza el grid de animales para optimizar colisiones"""
        self.grid_animales.clear()
        for animal in self.animales:
            grid_x = int(animal.x // CELL_SIZE)
            grid_y = int(animal.y // CELL_SIZE)
            key = (grid_x, grid_y)
            if key not in self.grid_animales:
                self.grid_animales[key] = []
            self.grid_animales[key].append(animal)

    def obtener_animales_cercanos(self, x, y, radio=2):
        """Obtiene los animales cercanos a una posición"""
        grid_x = int(x // CELL_SIZE)
        grid_y = int(y // CELL_SIZE)
        cercanos = []
        for dx in range(-radio, radio + 1):
            for dy in range(-radio, radio + 1):
                key = (grid_x + dx, grid_y + dy)
                if key in self.grid_animales:
                    cercanos.extend(self.grid_animales[key])
        return cercanos

    def simular_hora(self):
        self._actualizar_grid_animales()

        self.hora_actual += 1

        random.shuffle(self.animales)
        for animal in self.animales:
            if animal.esta_vivo:
                animal.comer(self)
                animal.moverse(self)

        for rio in self.terreno["rios"]:
            for pez in rio.peces:
                pez.moverse()

        if self.hora_actual >= 24:
            self.hora_actual = 0
            self.dia_total += 1
            self._actualizar_estacion()
            self._actualizar_clima()

            factor_crecimiento = self.estaciones[self.estacion_actual]['crecimiento']
            if self.clima_actual == "Sequía":
                factor_crecimiento *= 0.1

            for gx in range(self.grid_width):
                for gy in range(self.grid_height):
                    max_capacidad = MAX_HIERBA_NORMAL
                    tasa_crecimiento = 1
                    if any(p.rect.collidepoint(gx * CELL_SIZE, gy * CELL_SIZE) for p in self.terreno["praderas"]):
                        max_capacidad = MAX_HIERBA_PRADERA
                        tasa_crecimiento = 2
                    self.grid_hierba[gx][gy] += int(tasa_crecimiento * factor_crecimiento)
                    self.grid_hierba[gx][gy] = min(self.grid_hierba[gx][gy], max_capacidad)
            
            for selva in self.terreno["selvas"]: selva.crecer_recursos(factor_crecimiento)
            for rio in self.terreno["rios"]: rio.crecer_recursos(factor_crecimiento)

            for c in self.recursos["carcasas"]: c.dias_descomposicion += 1
            self.recursos["carcasas"] = [c for c in self.recursos["carcasas"] if c.energia_restante > 0 and c.dias_descomposicion < 5]

            self.animales_nuevos = []
            for animal in self.animales:
                if animal.esta_vivo:
                    animal.envejecer(self)
                    animal.reproducirse(self)

        self.animales = [animal for animal in self.animales if animal.esta_vivo]
        self.animales.extend(self.animales_nuevos)

    def agregar_animal(self, tipo_animal, nombre=None):
        if nombre is None:
            nombre = f"{tipo_animal.__name__} {getattr(tipo_animal, 'contador', 0) + 1}"

        while True:
            x = random.randint(20, SIM_WIDTH - 20)
            y = random.randint(20, SCREEN_HEIGHT - 20)
            if not self.choca_con_terreno(x, y):
                break
        nuevo_animal = tipo_animal(nombre, x, y)
        self.animales.append(nuevo_animal)

    def guardar_estado(self, archivo="save_state.json"):
        estado = {
            "dia_total": self.dia_total,
            "grid_hierba": self.grid_hierba,
            "selvas": [{"rect": list(s.rect), "bayas": s.bayas} for s in self.terreno["selvas"]],
            "rios": [{"rect": list(r.rect), "num_peces": len(r.peces)} for r in self.terreno["rios"]],
            "animales": [
                {
                    "tipo": a.__class__.__name__,
                    "nombre": a.nombre, "x": a.x, "y": a.y, "edad": a.edad,
                    "energia": a.energia, "sed": a._sed, "max_energia": a.max_energia
                }
                for a in self.animales
            ]
        }
        with open(archivo, 'w') as f:
            json.dump(estado, f, indent=4)

    def cargar_estado(self, archivo="save_state.json"):
        with open(archivo, 'r') as f:
            estado = json.load(f)

        self.dia_total = estado["dia_total"]
        self.grid_hierba = estado.get("grid_hierba", self.grid_hierba)
        for i, s_data in enumerate(estado["selvas"]):
            self.terreno["selvas"][i].bayas = s_data["bayas"]
        for i, r_data in enumerate(estado.get("rios", [])):
            rio = self.terreno["rios"][i]
            rio.peces = []
            for _ in range(r_data.get("num_peces", 20)):
                rio.peces.append(Pez(rio))

        self.animales = []
        tipos = {"Herbivoro": Herbivoro, "Carnivoro": Carnivoro, "Omnivoro": Omnivoro, "Conejo": Conejo, "Raton": Raton, "Cabra": Cabra, "Leopardo": Leopardo, "Gato": Gato, "Cerdo": Cerdo, "Mono": Mono, "Halcon": Halcon, "Insecto": Insecto}
        for a_data in estado["animales"]:
            tipo_clase = tipos.get(a_data["tipo"])
            if tipo_clase:
                animal = tipo_clase(a_data["nombre"], a_data["x"], a_data["y"], a_data["edad"], a_data["energia"], max_energia=a_data.get("max_energia"))
                animal._sed = a_data.get("sed", 0)
                self.animales.append(animal)