from abc import ABC, abstractmethod
import pygame # Necesario para usar pygame.Rect
import json
import math
import random

# --- Constantes de la Simulación ---
# Estas constantes definen los límites del área donde los animales pueden moverse.
SIM_WIDTH = 800
SCREEN_HEIGHT = 700

# Constantes para la reproducción
ENERGIA_REPRODUCCION = 80 # Energía mínima para poder reproducirse
EDAD_ADULTA = 3 # Edad mínima para poder reproducirse

# --- Clases del Entorno ---

class Terreno:
    """Clase base para elementos del entorno como ríos o montañas."""
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)

class Montana(Terreno):
    """Una barrera infranqueable."""
    pass

class Rio(Terreno):
    """Otra barrera infranqueable."""
    pass

# --- Clases del Modelo ---

class Animal(ABC):
    """Clase base para todos los animales. Contiene la lógica y los datos."""
    def __init__(self, nombre: str, x: int, y: int, edad: int = 0, energia: int = 100, genes=None):
        self._nombre = nombre
        self.x = x
        self.y = y
        self._edad = edad
        self._energia = energia
        self._sed = 0 # Nueva necesidad: 0 es saciado, 100 es sediento
        # --- Genética ---
        if genes is None:
            genes = {'max_energia': 100 + random.randint(-10, 10), 'rango_vision': 100 + random.randint(-20, 20)}
        self.genes = genes
        self.rango_vision = self.genes['rango_vision']
        self._esta_vivo = True
        # Contador para nombres únicos de crías
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
        """Método abstracto para que el animal se alimente. Devuelve un log."""
        pass

    def _distancia_a(self, x, y):
        """Calcula la distancia a un punto."""
        return math.sqrt((self.x - x)**2 + (self.y - y)**2)

    def moverse(self, ecosistema) -> str:
        """Lógica de movimiento, búsqueda de recursos y reducción de energía."""
        if self._esta_vivo:
            self._energia -= 5 # Reducimos menos para que la simulación dure más
            self._sed += 5 # El movimiento da sed

            dx, dy = 0, 0

            # --- Lógica de movimiento inteligente ---
            # Prioridad 1: Beber si tiene mucha sed
            if self._sed > 60:
                rio_cercano = ecosistema.encontrar_rio_cercano(self.x, self.y, self.rango_vision)
                if rio_cercano:
                    # Moverse hacia el borde del río
                    punto_cercano = min(
                        [(rio_cercano.rect.left, self.y), (rio_cercano.rect.right, self.y), (self.x, rio_cercano.rect.top), (self.x, rio_cercano.rect.bottom)],
                        key=lambda p: self._distancia_a(p[0], p[1])
                    )
                    dx = punto_cercano[0] - self.x
                    dy = punto_cercano[1] - self.y

            # Prioridad 2: Buscar comida si tiene hambre (lógica específica en subclases)
            if dx == 0 and dy == 0:
                dx, dy = self._buscar_comida(ecosistema)
            
            # Si no hay un objetivo claro (agua), moverse aleatoriamente
            if dx == 0 and dy == 0:
                dx = random.randint(-10, 10)
                dy = random.randint(-10, 10)

            # Normalizar el vector de movimiento para que la velocidad sea constante
            dist = math.sqrt(dx**2 + dy**2)
            if dist > 0:
                dx = (dx / dist) * 7 # Velocidad de 7 píxeles por paso
                dy = (dy / dist) * 7
            
            nueva_x = max(0, min(self.x + dx, SIM_WIDTH - 10))
            nueva_y = max(0, min(self.y + dy, SCREEN_HEIGHT - 10))

            # Comprobar colisiones con el terreno antes de moverse
            if not ecosistema.choca_con_terreno(nueva_x, nueva_y):
                self.x = nueva_x
                self.y = nueva_y

            # Comprobar si está cerca de un río para beber
            if ecosistema.esta_cerca_de_rio(self.x, self.y):
                self._sed = max(0, self._sed - 50) # Bebe y reduce la sed
                log_bebida = f" {self._nombre} ha bebido agua."
            else:
                log_bebida = ""

            log = f"{self._nombre} se ha movido. Energía: {self._energia}, Sed: {self._sed}." + log_bebida
            return log + self.verificar_estado()
        return ""

    def envejecer(self, ecosistema) -> str:
        """Incrementa la edad y reduce energía. Devuelve un log."""
        if self._esta_vivo:
            self._edad += 1
            # El coste de envejecer depende de la estación
            coste_energia = ecosistema.estaciones[ecosistema.estacion_actual]['coste_energia']
            self._energia -= coste_energia

            if self._sed > 80: # Si está muy sediento, pierde energía extra
                self._energia -= 10

            log = f"{self._nombre} ha envejecido. E: {self._energia}, S: {self._sed}"
            return log + self.verificar_estado()
        return ""

    def verificar_estado(self) -> str:
        """Comprueba si el animal sigue vivo. Devuelve log si muere."""
        if self._esta_vivo and (self._energia <= 0 or self._sed >= 150):
            self._esta_vivo = False
            return f" -> ¡{self._nombre} ha muerto!"
        return ""

    def reproducirse(self, ecosistema) -> str:
        """Intenta reproducirse si tiene suficiente energía y edad. Devuelve un log."""
        if self._esta_vivo and self._energia > ENERGIA_REPRODUCCION and self._edad > EDAD_ADULTA:
            # Probabilidad de reproducción para no saturar el ecosistema
            if random.random() < 0.2: # 20% de probabilidad cada día
                self._energia -= 40 # Coste energético de la reproducción

                # --- Lógica de Herencia Genética ---
                nuevos_genes = {
                    'max_energia': self.genes['max_energia'] + random.randint(-5, 5),
                    'rango_vision': self.genes['rango_vision'] + random.randint(-10, 10)
                }

                # Crear una cría del mismo tipo
                tipo_animal = type(self)
                nombre_cria = f"{tipo_animal.__name__.rstrip('o')} {getattr(tipo_animal, 'contador', 0) + 1}"
                cria = tipo_animal(nombre_cria, self.x, self.y, genes=nuevos_genes)
                ecosistema.animales_nuevos.append(cria) # Añadir a una lista temporal
                return f"¡{self._nombre} se ha reproducido! Nace {nombre_cria}."
        return ""

    def __str__(self):
        estado = "Vivo" if self._esta_vivo else "Muerto"
        return f"Animal: {self._nombre}, Tipo: {self.__class__.__name__}, Edad: {self._edad}, Energía: {self._energia}, Estado: {estado}"

class Herbivoro(Animal):
    """Animal que solo come plantas."""
    def comer(self, ecosistema) -> str:
        if self._esta_vivo and self._energia < self.genes['max_energia'] and ecosistema.recursos['hierba'] > 0:
            ecosistema.recursos['hierba'] -= 1
            self._energia += 15 # La hierba da menos energía
            self._energia = min(self._energia, self.genes['max_energia'])
            return f"{self._nombre} (Herbívoro) ha comido hierba. Energía: {self._energia}"
        self._energia -= 5 # Pierde energía buscando
        return f"{self._nombre} (Herbívoro) no encontró hierba."

    def _buscar_comida(self, ecosistema):
        """Los herbívoros no buscan activamente, pastan donde están."""
        return 0, 0 # Movimiento aleatorio

class Carnivoro(Animal):
    """Animal que come otros animales."""
    def comer(self, ecosistema) -> str:
        if not self._esta_vivo:
            return ""
        
        presa = ecosistema.encontrar_presa_cercana(self)
        if presa:
            self._energia += 50
            self._energia = min(self._energia, self.genes['max_energia'])
            presa._energia = 0 # La presa muere instantáneamente
            log_muerte = presa.verificar_estado()
            return f"{self._nombre} (Carnívoro) ha cazado y comido a {presa.nombre}." + log_muerte
        else:
            self._energia -= 15
            log = f"{self._nombre} (Carnívoro) no encontró presas y perdió energía."
            return log + self.verificar_estado()

    def _buscar_comida(self, ecosistema):
        """Busca la presa más cercana y se mueve hacia ella."""
        if self._energia < 70: # Solo caza si tiene hambre
            presa_cercana = ecosistema.encontrar_presa_cercana(self)
            if presa_cercana:
                dx = presa_cercana.x - self.x
                dy = presa_cercana.y - self.y
                return dx, dy
        return 0, 0


class Omnivoro(Animal):
    """Animal que puede comer tanto plantas como otros animales."""
    def comer(self, ecosistema) -> str:
        if not self._esta_vivo:
            return ""
        
        presa = ecosistema.encontrar_presa_cercana(self) # Busca una presa una sola vez
        intentar_cazar = random.choice([True, False]) # Decide si prefiere cazar
        
        if intentar_cazar and presa:
            # Opción 1: Prefiere cazar y encuentra una presa.
            self._energia += 50
            self._energia = min(self._energia, self.genes['max_energia'])
            presa._energia = 0
            log_muerte = presa.verificar_estado()
            return f"{self._nombre} (Omnívoro) ha cazado y comido a {presa.nombre}." + log_muerte
        elif ecosistema.comer_bayas(self):
            # Opción 2: No cazó, pero encontró y comió bayas en una selva.
            self._energia += 25
            self._energia = min(self._energia, self.genes['max_energia'])
            return f"{self._nombre} (Omnívoro) ha comido bayas. Energía: {self._energia}"

        elif presa:
            # Opción 3: No hay plantas, pero sí hay una presa. La caza por necesidad.
            self._energia += 50
            self._energia = min(self._energia, self.genes['max_energia'])
            presa._energia = 0
            log_muerte = presa.verificar_estado()
            return f"{self._nombre} (Omnívoro) ha cazado y comido a {presa.nombre}." + log_muerte
        # Opción 4: No encontró nada que comer.
        self._energia -= 10 # Pierde algo de energía buscando
        log = f"{self._nombre} (Omnívoro) no encontró nada que comer."
        return log + self.verificar_estado()

    def _buscar_comida(self, ecosistema):
        """Los omnívoros buscan selvas si tienen hambre."""
        if self._energia < 60:
            selva_cercana = ecosistema.encontrar_selva_cercana(self.x, self.y, self.rango_vision)
            if selva_cercana:
                dx = selva_cercana.rect.centerx - self.x
                dy = selva_cercana.rect.centery - self.y
                return dx, dy
        return 0, 0


class Selva(Terreno):
    """Zona donde crecen las bayas. No es una barrera."""
    def __init__(self, rect):
        super().__init__(rect)
        self.bayas = 15

    def crecer_recursos(self, factor_crecimiento):
        self.bayas += int(2 * factor_crecimiento)

class Ecosistema:
    """Gestiona el estado del entorno y los animales."""
    def __init__(self):
        self.animales: list[Animal] = []
        self.recursos = {
            "hierba": 100
        }
        self.terreno = {
            "montanas": [
                Montana((50, 50, 100, 150)),
                Montana((600, 400, 150, 120))
            ],
            "rios": [
                Rio((0, 300, 500, 40)),
                Rio((460, 100, 40, 240))
            ],
            "selvas": [
                Selva((200, 450, 250, 180))
            ]
        }
        # --- Estaciones y Clima ---
        self.dia_total = 0
        self.dias_por_estacion = 20
        self.estacion_actual = "Primavera"
        self.estaciones = {
            "Primavera": {"crecimiento": 1.5, "coste_energia": 2},
            "Verano":    {"crecimiento": 1.0, "coste_energia": 3},
            "Otoño":     {"crecimiento": 0.5, "coste_energia": 4},
            "Invierno":  {"crecimiento": 0.1, "coste_energia": 6}
        }
        self.clima_actual = "Normal"

        self.animales_nuevos = [] # Lista para las crías nacidas en el día

    def encontrar_presa_cercana(self, depredador):
        """Encuentra la presa más cercana dentro del rango de visión del depredador."""
        presas_posibles = [
            animal for animal in self.animales 
            if isinstance(animal, (Herbivoro, Omnivoro)) and animal.esta_vivo and animal != depredador and
            depredador._distancia_a(animal.x, animal.y) < depredador.rango_vision
        ]
        if not presas_posibles:
            return None
        # Devuelve la presa más cercana
        return min(presas_posibles, key=lambda p: depredador._distancia_a(p.x, p.y))

    def encontrar_rio_cercano(self, x, y, rango):
        """Encuentra el río más cercano dentro de un rango."""
        rios_cercanos = []
        for rio in self.terreno["rios"]:
            # Simplificación: comprobar si el centro del animal está cerca del rect del río
            if rio.rect.clipline((x - rango, y), (x + rango, y)) or \
               rio.rect.clipline((x, y - rango), (x, y + rango)):
                rios_cercanos.append(rio)
        
        if not rios_cercanos:
            return None
        
        # Devuelve el río cuyo centroide está más cerca (es una aproximación)
        return min(rios_cercanos, key=lambda r: math.sqrt((r.rect.centerx - x)**2 + (r.rect.centery - y)**2))

    def encontrar_selva_cercana(self, x, y, rango):
        """Encuentra la selva más cercana dentro de un rango."""
        selvas_cercanas = [s for s in self.terreno["selvas"] if self._distancia_a_rect(x, y, s.rect) < rango]
        if not selvas_cercanas:
            return None
        return min(selvas_cercanas, key=lambda s: self._distancia_a_rect(x, y, s.rect))

    def _distancia_a_rect(self, x, y, rect):
        """Calcula la distancia desde un punto al centro de un rectángulo."""
        return math.sqrt((rect.centerx - x)**2 + (rect.centery - y)**2)


    def choca_con_terreno(self, x, y):
        """Comprueba si una posición colisiona con una barrera."""
        punto = pygame.Rect(x, y, 1, 1)
        for montana in self.terreno["montanas"]:
            if montana.rect.colliderect(punto):
                return True
        for rio in self.terreno["rios"]:
            if rio.rect.colliderect(punto):
                return True
        return False

    def esta_cerca_de_rio(self, x, y, distancia_max=15):
        """Comprueba si un animal está suficientemente cerca de un río para beber."""
        animal_rect = pygame.Rect(x - distancia_max, y - distancia_max, distancia_max*2, distancia_max*2)
        for rio in self.terreno["rios"]:
            if rio.rect.colliderect(animal_rect):
                return True
        return False

    def comer_bayas(self, animal):
        """Permite a un animal comer bayas si está en una selva con bayas."""
        for selva in self.terreno["selvas"]:
            if selva.rect.collidepoint(animal.x, animal.y) and selva.bayas > 0:
                selva.bayas -= 1
                return True
        return False

    def _actualizar_estacion(self):
        """Actualiza la estación del año."""
        self.dia_total += 1
        indice_estacion = (self.dia_total // self.dias_por_estacion) % 4
        self.estacion_actual = list(self.estaciones.keys())[indice_estacion]

        # Lógica del clima
        if random.random() < 0.05: # 5% de probabilidad de sequía
            self.clima_actual = "Sequía"
        else:
            self.clima_actual = "Normal"

    def simular_dia(self) -> list[str]:
        """Ejecuta un ciclo de simulación y devuelve los logs del día."""
        logs_dia = []
        self._actualizar_estacion()

        factor_crecimiento = self.estaciones[self.estacion_actual]['crecimiento']
        if self.clima_actual == "Sequía":
            factor_crecimiento *= 0.1 # La sequía reduce drásticamente el crecimiento
            logs_dia.append("¡Una sequía azota la región!")

        self.recursos["hierba"] += int(15 * factor_crecimiento)
        for selva in self.terreno["selvas"]:
            selva.crecer_recursos(factor_crecimiento)
        
        logs_dia.append(f"Estación: {self.estacion_actual}. Clima: {self.clima_actual}.")
        bayas_totales = sum(s.bayas for s in self.terreno["selvas"])
        logs_dia.append(f"Recursos: {self.recursos['hierba']} hierba, {bayas_totales} bayas.")


        random.shuffle(self.animales)
        self.animales_nuevos = [] # Limpiar la lista de crías al inicio del día

        for animal in self.animales:
            if animal.esta_vivo:
                logs_dia.append(animal.envejecer(self))
                logs_dia.append(animal.moverse(self))
                logs_dia.append(animal.comer(self))
                logs_dia.append(animal.reproducirse(self)) # Nuevo comportamiento
        
        self.animales = [animal for animal in self.animales if animal.esta_vivo]
        self.animales.extend(self.animales_nuevos) # Añadir las crías a la lista principal

        return [log for log in logs_dia if log] # Filtra logs vacíos

    def agregar_animal(self, tipo_animal, nombre=None):
        """Crea un animal con un nombre único y lo añade al ecosistema."""
        # Si no se proporciona un nombre, se genera uno automáticamente.
        if nombre is None:
            nombre = f"{tipo_animal.__name__} {getattr(tipo_animal, 'contador', 0) + 1}"

        x = random.randint(20, SIM_WIDTH - 20)
        y = random.randint(20, SCREEN_HEIGHT - 20)
        nuevo_animal = tipo_animal(nombre, x, y)
        self.animales.append(nuevo_animal)

    def guardar_estado(self, archivo="save_state.json"):
        """Guarda el estado actual del ecosistema en un archivo JSON."""
        estado = {
            "dia_total": self.dia_total,
            "recursos": self.recursos,
            "selvas": [{"rect": list(s.rect), "bayas": s.bayas} for s in self.terreno["selvas"]],
            "animales": [
                {
                    "tipo": a.__class__.__name__,
                    "nombre": a.nombre, "x": a.x, "y": a.y, "edad": a.edad,
                    "energia": a.energia, "sed": a._sed, "genes": a.genes
                }
                for a in self.animales
            ]
        }
        with open(archivo, 'w') as f:
            json.dump(estado, f, indent=4)

    def cargar_estado(self, archivo="save_state.json"):
        """Carga el estado del ecosistema desde un archivo JSON."""
        with open(archivo, 'r') as f:
            estado = json.load(f)

        self.dia_total = estado["dia_total"]
        self.recursos = estado["recursos"]
        for i, s_data in enumerate(estado["selvas"]):
            self.terreno["selvas"][i].bayas = s_data["bayas"]

        self.animales = []
        tipos = {"Herbivoro": Herbivoro, "Carnivoro": Carnivoro, "Omnivoro": Omnivoro}
        for a_data in estado["animales"]:
            tipo_clase = tipos[a_data["tipo"]]
            animal = tipo_clase(a_data["nombre"], a_data["x"], a_data["y"], a_data["edad"], a_data["energia"], genes=a_data["genes"])
            animal._sed = a_data["sed"]
            self.animales.append(animal)