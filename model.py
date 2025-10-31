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
    def __init__(self, x, y, rio=None):
        self.x = x
        self.y = y
        self.rio = rio
        self.energia = 50
        self.fue_comido = False
        self.velocidad = 1
        self.direccion = random.uniform(0, 2 * math.pi)

    def moverse(self):
        if self.fue_comido:
            return
            
        # Cambiar dirección ocasionalmente
        if random.random() < 0.05:
            self.direccion += random.uniform(-0.3, 0.3)

        # Calcular nuevo movimiento
        nuevo_x = self.x + math.cos(self.direccion) * self.velocidad
        nuevo_y = self.y + math.sin(self.direccion) * self.velocidad

        # Mantener dentro del río
        if self.rio:
            rect = self.rio.rect
            nuevo_x = max(rect.left + 5, min(rect.right - 5, nuevo_x))
            nuevo_y = max(rect.top + 5, min(rect.bottom - 5, nuevo_y))
            
            # Rebotar en los bordes
            if nuevo_x in (rect.left + 5, rect.right - 5):
                self.direccion = math.pi - self.direccion
            if nuevo_y in (rect.top + 5, rect.bottom - 5):
                self.direccion = -self.direccion

        self.x = nuevo_x
        self.y = nuevo_y

class Rio(Terreno):
    def __init__(self, rect):
        super().__init__(rect)
        self.max_peces = 20
        self.peces = []
        self._generar_peces_iniciales()

    def _generar_peces_iniciales(self):
        for _ in range(10):
            x = random.randint(self.rect.left + 5, self.rect.right - 5)
            y = random.randint(self.rect.top + 5, self.rect.bottom - 5)
            pez = Pez(x, y, self)
            self.peces.append(pez)

    def crecer_recursos(self, factor_crecimiento):
        if len(self.peces) < 50:
            if random.random() < 0.1 * factor_crecimiento:
                x = random.randint(self.rect.left + 5, self.rect.right - 5)
                y = random.randint(self.rect.top + 5, self.rect.bottom - 5)
                self.peces.append(Pez(x, y, self))

    def actualizar(self):
        # Mover peces existentes
        for pez in self.peces:
            pez.moverse()
        
        # Limpiar peces comidos
        self.peces = [pez for pez in self.peces if not pez.fue_comido]
        
        # Regenerar peces
        if len(self.peces) < self.max_peces and random.random() < 0.1:
            x = random.randint(self.rect.left + 5, self.rect.right - 5)
            y = random.randint(self.rect.top + 5, self.rect.bottom - 5)
            self.peces.append(Pez(x, y, self))

class Selva(Terreno):
    def __init__(self, rect):
        super().__init__(rect)
        self.bayas = 25

    def crecer_recursos(self, factor_crecimiento):
        self.bayas += int(3 * factor_crecimiento)

class Pradera(Terreno):
    def __init__(self, rect):
        super().__init__(rect)
        self.max_hierba = MAX_HIERBA_PRADERA
        self.tasa_crecimiento = 2
        

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
        self.objetivo = None  # Para un movimiento más inteligente
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

    @abstractmethod
    def beber(self, ecosistema) -> str:
        pass

    def moverse(self, ecosistema: 'Ecosistema') -> str:
        # Si no hay objetivo o se ha alcanzado, buscar uno nuevo
        if self.objetivo is None or math.sqrt((self.x - self.objetivo[0])**2 + (self.y - self.objetivo[1])**2) < 10:
            self.objetivo = None
            # Buscar comida si tiene hambre
            if self.energia < self.max_energia * 0.7:
                if isinstance(self, Herbivoro):
                    self.objetivo = self._encontrar_hierba_cercana(ecosistema)
                elif isinstance(self, Carnivoro):
                    presa = self._encontrar_presa_cercana(ecosistema)
                    if presa:
                        self.objetivo = (presa.x, presa.y)
            # Prioridad 2: Buscar agua si tiene sed
            elif self._sed > 80:
                rio_cercano = self._encontrar_rio_cercano(ecosistema)
                if rio_cercano:
                    self.objetivo = (rio_cercano.rect.centerx, rio_cercano.rect.centery)
            
            # Si no hay objetivo de comida, deambular
            if self.objetivo is None:
                self.objetivo = (
                    self.x + random.randint(-50, 50),
                    self.y + random.randint(-50, 50)
                )

        # Moverse hacia el objetivo
        if self.objetivo:
            dx = self.objetivo[0] - self.x
            dy = self.objetivo[1] - self.y
        else: # Fallback por si acaso
            dx = random.randint(-1, 1)
            dy = random.randint(-1, 1)
        
        # Normalizar el movimiento
        magnitud = math.sqrt(dx*dx + dy*dy)
        if magnitud > 0:
            # Reducir la velocidad de 5 a 2 para un movimiento más natural
            velocidad = 2
            dx = int((dx/magnitud) * velocidad)
            dy = int((dy/magnitud) * velocidad)
        
        nuevo_x = max(0, min(self.x + dx, SIM_WIDTH - 1))
        nuevo_y = max(0, min(self.y + dy, SCREEN_HEIGHT - 1))

        if not ecosistema.choca_con_terreno(nuevo_x, nuevo_y):
            self.x = nuevo_x
            self.y = nuevo_y

        coste_movimiento = 0.2 + ecosistema.estaciones[ecosistema.estacion_actual]['coste_energia'] * 0.3
        self._energia -= coste_movimiento
        self._sed += 0.2
        return ""

    def _encontrar_hierba_cercana(self, ecosistema):
        grid_x = int(self.x // CELL_SIZE)
        grid_y = int(self.y // CELL_SIZE)
        mejor_pos = None
        mejor_valor = 0
        
        # Buscar en un radio de 5 celdas
        for dx in range(-5, 6):
            for dy in range(-5, 6):
                gx, gy = grid_x + dx, grid_y + dy
                if (0 <= gx < ecosistema.grid_width and 
                    0 <= gy < ecosistema.grid_height and 
                    ecosistema.grid_hierba[gx][gy] > mejor_valor):
                    mejor_valor = ecosistema.grid_hierba[gx][gy]
                    # Moverse a un punto aleatorio dentro de la celda, no al centro
                    mejor_pos = (gx * CELL_SIZE + random.randint(0, CELL_SIZE), 
                                 gy * CELL_SIZE + random.randint(0, CELL_SIZE))
        return mejor_pos

    def _encontrar_presa_cercana(self, ecosistema):
        presas_cercanas = ecosistema.obtener_animales_cercanos(self.x, self.y, 5)
        mejor_presa = None
        menor_distancia = float('inf')
        
        for presa in presas_cercanas:
            if (presa is not self and 
                not isinstance(presa, Carnivoro) and 
                presa.esta_vivo):
                dist = math.sqrt((self.x - presa.x)**2 + (self.y - presa.y)**2)
                if dist < menor_distancia:
                    menor_distancia = dist
                    mejor_presa = presa
        return mejor_presa

    def _encontrar_rio_cercano(self, ecosistema):
        mejor_rio = None
        menor_distancia = float('inf')
        for rio in ecosistema.terreno["rios"]:
            # Usamos la distancia al centro del rectángulo del río como aproximación
            dist = math.sqrt((self.x - rio.rect.centerx)**2 + (self.y - rio.rect.centery)**2)
            if dist < menor_distancia:
                menor_distancia = dist
                mejor_rio = rio
        return mejor_rio

    def envejecer(self, ecosistema: 'Ecosistema') -> str:
        self._edad += 1
        # Reducir el coste de envejecimiento de 2 a 0.5
        self._energia -= 0.5
        # Aumentar el coste de envejecimiento para hacer la supervivencia más difícil
        self._energia -= 1.5
        return self.verificar_estado(ecosistema)

    def verificar_estado(self, ecosistema: 'Ecosistema') -> str:
        if self._esta_vivo and (
            self._energia <= 0 or 
            self._sed >= 150 or  # Límite de sed
            self._edad > 365 or
            not 0 <= self.x < SIM_WIDTH or 
            not 0 <= self.y < SCREEN_HEIGHT
        ):
            self._esta_vivo = False
            ecosistema.agregar_carcasa(self.x, self.y)
            return f" -> ¡{self._nombre} ha muerto!"
        return ""

    def reproducirse(self, ecosistema: 'Ecosistema') -> str:
        # Ajustar condiciones de reproducción
        if (self.edad > 30 and  # Aumentar edad de madurez
            self.energia > self.max_energia * 0.85 and  # Aumentar requisito de energía
            random.random() < 0.02):  # Reducir probabilidad de reproducción
            # Crear una cría del mismo tipo
            cría = type(self)(f"{self.nombre} Jr.", self.x, self.y)
            ecosistema.animales_nuevos.append(cría)
            self._energia -= 20  # Reducir el coste de reproducción
            return f"{self.nombre} se ha reproducido."
        return ""

    def __str__(self):
        estado = "Vivo" if self._esta_vivo else "Muerto"
        return f"Animal: {self._nombre}, Tipo: {self.__class__.__name__}, Edad: {self._edad}, Energía: {self._energia}, Estado: {estado}"

class Herbivoro(Animal):
    def comer(self, ecosistema) -> str:
        # Los herbívoros comen hierba si tienen hambre
        if self.energia < self.max_energia * 0.9:  # Hacer que coman más frecuentemente
            grid_x = int(self.x // CELL_SIZE)
            grid_y = int(self.y // CELL_SIZE)
            
            # Asegurarse de que las coordenadas están dentro de los límites del grid
            if 0 <= grid_x < ecosistema.grid_width and 0 <= grid_y < ecosistema.grid_height:
                if ecosistema.grid_hierba[grid_x][grid_y] > 0:
                    comido = min(ecosistema.grid_hierba[grid_x][grid_y], 15)  # Aumentar cantidad que comen
                    self._energia += comido * 4  # Aumentar energía obtenida
                    self._sed -= 5  # Reducir sed al comer hierba
                    self._energia = min(self._energia, self.max_energia)
                    ecosistema.grid_hierba[grid_x][grid_y] -= comido
                    return f"{self.nombre} comió hierba."
        return ""

    def beber(self, ecosistema) -> str:
        if self._sed > 50:
            for rio in ecosistema.terreno["rios"]:
                if rio.rect.collidepoint(self.x, self.y):
                    self._sed = max(0, self._sed - 75)
                    return f"{self.nombre} bebió agua."
        return ""

class Carnivoro(Animal):
    def comer(self, ecosistema) -> str:
        # Los carnívoros cazan otros animales si tienen hambre
        if self.energia < self.max_energia * 0.8:
            # Optimización: en lugar de comprobar todos, comprueba una muestra aleatoria de presas cercanas.
            posibles_presas = random.sample(ecosistema.animales, min(len(ecosistema.animales), 15))
            for presa in posibles_presas:
                # No se cazan a sí mismos, ni a otros carnívoros, y la presa debe estar viva
                if presa is not self and not isinstance(presa, Carnivoro) and presa.esta_vivo:
                    distancia = math.sqrt((self.x - presa.x)**2 + (self.y - presa.y)**2)
                    # Si la presa está lo suficientemente cerca
                    if distancia < 20:  # Aumentar rango de caza
                        presa._esta_vivo = False # La presa muere
                        ecosistema.agregar_carcasa(presa.x, presa.y)
                        self._energia += 80  # Más energía por caza
                        self._sed -= 10  # Reducir sed al comer presas
                        self._energia = min(self._energia, self.max_energia)
                        return f"{self.nombre} cazó a {presa.nombre}."
            # Lógica de caza mejorada: buscar la presa más cercana en lugar de una aleatoria
            presa_objetivo = self._encontrar_presa_cercana(ecosistema)
            if presa_objetivo:
                distancia = math.sqrt((self.x - presa_objetivo.x)**2 + (self.y - presa_objetivo.y)**2)
                # Si la presa está lo suficientemente cerca
                if distancia < 20:  # Rango de caza
                    presa_objetivo._esta_vivo = False # La presa muere
                    ecosistema.agregar_carcasa(presa_objetivo.x, presa_objetivo.y)
                    self._energia += 80  # Más energía por caza
                    self._sed -= 10  # Reducir sed al comer presas
                    self._energia = min(self._energia, self.max_energia)
                    return f"{self.nombre} cazó a {presa_objetivo.nombre}."
        return ""

    def beber(self, ecosistema) -> str:
        if self._sed > 50:
            for rio in ecosistema.terreno["rios"]:
                if rio.rect.collidepoint(self.x, self.y):
                    self._sed = max(0, self._sed - 75)
                    return f"{self.nombre} bebió agua."
        return ""

class Omnivoro(Animal):
    def comer(self, ecosistema) -> str:
        if self.energia < self.max_energia * 0.7:
            # Intentar comer bayas primero
            for selva in ecosistema.terreno["selvas"]:
                if selva.rect.collidepoint(self.x, self.y) and selva.bayas > 0:
                    energia_ganada = min(30, selva.bayas * 2)  # Aumentar energía de bayas
                    self._energia = min(self.max_energia, self._energia + energia_ganada)
                    selva.bayas = max(0, selva.bayas - 10)
                    return f"{self.nombre} comió bayas."
            
            # Si no hay bayas, intentar cazar
            animales_cercanos = ecosistema.obtener_animales_cercanos(self.x, self.y)
            for presa in animales_cercanos:
                if self._puede_cazar(presa):
                    distancia = math.sqrt((self.x - presa.x)**2 + (self.y - presa.y)**2)
                    if distancia < 15:
                        presa._esta_vivo = False
                        ecosistema.agregar_carcasa(presa.x, presa.y)
                        self._energia = min(self.max_energia, self._energia + 60)  # Aumentar energía de caza
                        return f"{self.nombre} cazó a {presa.nombre}."
        return ""

    def _puede_cazar(self, presa):
        return (presa is not self and not isinstance(presa, (Carnivoro, Omnivoro)) and presa.esta_vivo and self.energia > 30)

    def beber(self, ecosistema) -> str:
        if self._sed > 50:
            for rio in ecosistema.terreno["rios"]:
                if rio.rect.collidepoint(self.x, self.y):
                    self._sed = max(0, self._sed - 75)
                    return f"{self.nombre} bebió agua."
        return ""

# --- Clases de Animales Específicos ---

# --- Herbívoros ---
class Conejo(Herbivoro):
    def __init__(self, nombre: str, x: int, y: int, edad: int = 0, energia: int = 100, max_energia=None):
        if max_energia is None:
            max_energia = max(70, min(90, 80 + random.randint(-5, 5)))
        super().__init__(nombre, x, y, edad, energia, max_energia)

class Cabra(Herbivoro):
    def __init__(self, nombre: str, x: int, y: int, edad: int = 0, energia: int = 100, max_energia=None):
        if max_energia is None:
            max_energia = max(90, min(110, 100 + random.randint(-5, 5)))
        super().__init__(nombre, x, y, edad, energia, max_energia)
        
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
    def __init__(self, nombre: str, x: int, y: int, edad: int = 0, energia: int = 100, max_energia=None):
        if max_energia is None:
            max_energia = max(100, min(120, 110 + random.randint(-5, 5)))
        super().__init__(nombre, x, y, edad, energia, max_energia)

class Gato(Carnivoro):
    def __init__(self, nombre: str, x: int, y: int, edad: int = 0, energia: int = 100, max_energia=None):
        if max_energia is None:
            max_energia = max(75, min(95, 85 + random.randint(-5, 5)))
        super().__init__(nombre, x, y, edad, energia, max_energia)
        
class Halcon(Carnivoro):
    def __init__(self, nombre: str, x: int, y: int, edad: int = 0, energia: int = 100, max_energia=None):
        if max_energia is None:
            max_energia = max(70, min(90, 80 + random.randint(-5, 5)))
        super().__init__(nombre, x, y, edad, energia, max_energia)
        
# --- Omnívoros ---
class Cerdo(Omnivoro):
    def __init__(self, nombre: str, x: int, y: int, edad: int = 0, energia: int = 100, max_energia=None):
        if max_energia is None:
            max_energia = max(110, min(130, 120 + random.randint(-5, 5)))
        super().__init__(nombre, x, y, edad, energia, max_energia)
        
class Mono(Omnivoro):
    def __init__(self, nombre: str, x: int, y: int, edad: int = 0, energia: int = 100, max_energia=None):
        if max_energia is None:
            max_energia = max(80, min(100, 90 + random.randint(-5, 5)))
        super().__init__(nombre, x, y, edad, energia, max_energia)
        
class Ecosistema:
    def __init__(self):
        # Lista de todas las clases de animales para el rescate anti-extinción
        self.tipos_de_animales = [Conejo, Raton, Cabra, Leopardo, Gato, Cerdo, Mono, Halcon, Insecto]


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
                    max_val = MAX_HIERBA_PRADERA # Se mantiene para la inicialización aleatoria
                self.grid_hierba[gx][gy] = random.randint(0, max_val)

        # --- Estaciones y Clima ---
        self.dia_total = 1
        self.hora_actual = 0
        self.dias_por_estacion = 20
        self.estacion_actual = "Primavera"
        self.estaciones = {
            "Primavera": {"crecimiento": 2.0, "coste_energia": 0.1}, # Crecimiento moderado
            "Verano":    {"crecimiento": 1.5, "coste_energia": 0.4}, # Menos crecimiento, más coste
            "Otoño":     {"crecimiento": 0.5, "coste_energia": 0.7}, # Poco crecimiento, alto coste
            "Invierno":  {"crecimiento": 0.1, "coste_energia": 1.5}  # Invierno muy duro
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

    def _rescate_extincion(self):
        """
        Si una especie se extingue, reintroduce un pequeño número de individuos
        para simular inmigración y evitar un colapso total.
        """
        # No ejecutar si no hay animales en absoluto
        if not self.animales:
            return

        for tipo_animal in self.tipos_de_animales:
            conteo = sum(1 for a in self.animales if isinstance(a, tipo_animal))
            if conteo == 0:
                print(f"¡Rescate anti-extinción! Reintroduciendo {tipo_animal.__name__}.")
                for _ in range(4): # Reintroducir 4 individuos
                    self.agregar_animal(tipo_animal)

    def simular_hora(self):
        self._actualizar_grid_animales()

        self.hora_actual += 1

        random.shuffle(self.animales)
        for animal in self.animales:
            if animal.esta_vivo:
                animal.comer(self)
                animal.beber(self)
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
                    tasa_crecimiento_base = 1
                    
                    pradera_actual = next((p for p in self.terreno["praderas"] if p.rect.collidepoint(gx * CELL_SIZE, gy * CELL_SIZE)), None)
                    if pradera_actual:
                        max_capacidad = pradera_actual.max_hierba
                        tasa_crecimiento_base = pradera_actual.tasa_crecimiento
                    self.grid_hierba[gx][gy] += int(tasa_crecimiento_base * factor_crecimiento)
                    self.grid_hierba[gx][gy] = min(self.grid_hierba[gx][gy], max_capacidad)
            
            for selva in self.terreno["selvas"]: selva.crecer_recursos(factor_crecimiento)
            for rio in self.terreno["rios"]: rio.crecer_recursos(factor_crecimiento)

            for c in self.recursos["carcasas"]: c.dias_descomposicion += 1
            self.recursos["carcasas"] = [c for c in self.recursos["carcasas"] if c.dias_descomposicion < 5]

            self.animales_nuevos = []
            for animal in self.animales:
                if animal.esta_vivo:
                    # 1. Envejecimiento y posible muerte por edad/hambre
                    animal.envejecer(self)
                    # 2. Reproducción si sobrevive y cumple condiciones
                    animal.reproducirse(self)

        self.animales = [animal for animal in self.animales if animal.esta_vivo]
        self.animales.extend(self.animales_nuevos)
        
        # Al final del día, comprobar si alguna especie se ha extinguido
        if self.hora_actual == 0: self._rescate_extincion()

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
                x = random.randint(rio.rect.left + 5, rio.rect.right - 5)
                y = random.randint(rio.rect.top + 5, rio.rect.bottom - 5)
                rio.peces.append(Pez(x, y, rio))

        self.animales = []
        tipos = {"Herbivoro": Herbivoro, "Carnivoro": Carnivoro, "Omnivoro": Omnivoro, "Conejo": Conejo, "Raton": Raton, "Cabra": Cabra, "Leopardo": Leopardo, "Gato": Gato, "Cerdo": Cerdo, "Mono": Mono, "Halcon": Halcon, "Insecto": Insecto}
        for a_data in estado["animales"]:
            tipo_clase = tipos.get(a_data["tipo"])
            if tipo_clase:
                animal = tipo_clase(a_data["nombre"], a_data["x"], a_data["y"], a_data["edad"], a_data["energia"], max_energia=a_data.get("max_energia"))
                animal._sed = a_data.get("sed", 0)
                self.animales.append(animal)