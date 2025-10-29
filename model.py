from abc import ABC, abstractmethod
import pygame # Necesario para usar pygame.Rect
import json
import math
import random

# --- Constantes de la Simulación ---
# Estas constantes definen los límites del área donde los animales pueden moverse.
SIM_WIDTH = 800
SCREEN_HEIGHT = 700

# --- Constantes de Comportamiento Animal ---
COSTE_MOVIMIENTO = 2          # Energía perdida al moverse
AUMENTO_SED_MOVIMIENTO = 1    # Sed ganada al moverse
VELOCIDAD_ANIMAL = 5          # Píxeles por paso de simulación
UMBRAL_SED_BEBER = 60         # Nivel de sed para buscar agua activamente
UMBRAL_HAMBRE_CARNIVORO = 70  # Nivel de energía para empezar a cazar
UMBRAL_HAMBRE_OMNIVORO = 60   # Nivel de energía para buscar comida
ENERGIA_HIERBA = 15
ENERGIA_CAZA = 50
ENERGIA_BAYAS = 25
COSTE_BUSCAR_COMIDA = 10      # Energía perdida si no se encuentra comida
PROBABILIDAD_REPRODUCCION = 0.07 # 7% de probabilidad por día

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

class Pradera(Terreno):
    """Zona fértil que genera más hierba."""
    pass

class Santuario(Terreno):
    """Zona segura donde no se puede cazar y la reproducción es más fácil."""
    pass

class Carcasa:
    """Representa los restos de un animal muerto, una fuente de comida."""
    def __init__(self, x, y, energia_restante=60):
        self.x = x
        self.y = y
        self.energia_restante = energia_restante
        self.dias_descomposicion = 0

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
            self._energia -= COSTE_MOVIMIENTO
            self._sed += AUMENTO_SED_MOVIMIENTO

            dx, dy = 0, 0

            # --- Lógica de movimiento inteligente ---
            # Prioridad 0: Huir si hay un depredador cerca (para presas)
            if isinstance(self, (Herbivoro, Omnivoro)):
                depredador_cercano = ecosistema.encontrar_depredador_cercano(self)
                if depredador_cercano:
                    log_huida = "" # Inicializar por si acaso
                    # Huir en dirección opuesta
                    dx = self.x - depredador_cercano.x
                    dy = self.y - depredador_cercano.y
                    log_huida = f" {self._nombre} huye de {depredador_cercano.nombre}."


            # Prioridad 1: Beber si tiene mucha sed
            if self._sed > UMBRAL_SED_BEBER:
                rio_cercano = ecosistema.encontrar_rio_cercano(self.x, self.y, self.rango_vision)
                if rio_cercano:
                    # Moverse hacia el borde del río
                    punto_cercano = min(
                        [(rio_cercano.rect.left, self.y), (rio_cercano.rect.right, self.y), (self.x, rio_cercano.rect.top), (self.x, rio_cercano.rect.bottom)],
                        key=lambda p: self._distancia_a(p[0], p[1])
                    )
                    dx = punto_cercano[0] - self.x
                    dy = punto_cercano[1] - self.y

            # Prioridad 1.5: Buscar refugio si la energía es baja
            if dx == 0 and dy == 0 and self._energia < 40:
                santuario_cercano = ecosistema.encontrar_santuario_cercano(self.x, self.y, self.rango_vision)
                if santuario_cercano:
                    dx = santuario_cercano.rect.centerx - self.x
                    dy = santuario_cercano.rect.centery - self.y

            # Prioridad 2: Buscar comida si tiene hambre (lógica específica en subclases)
            if dx == 0 and dy == 0:
                dx, dy = self._buscar_comida(ecosistema)
            
            # Si no hay un objetivo claro (agua), moverse aleatoriamente
            # (La lógica de olfato de los depredadores anulará esto)
            if dx == 0 and dy == 0:
                dx = random.randint(-10, 10)
                dy = random.randint(-10, 10)

            # Normalizar el vector de movimiento para que la velocidad sea constante
            dist = math.sqrt(dx**2 + dy**2)
            if dist > 0:
                dx = (dx / dist) * VELOCIDAD_ANIMAL
                dy = (dy / dist) * VELOCIDAD_ANIMAL
            
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
            return log + self.verificar_estado(ecosistema)
        return ""

    def envejecer(self, ecosistema: 'Ecosistema') -> str:
        """Incrementa la edad y reduce energía. Devuelve un log."""
        if self._esta_vivo:
            self._edad += 1
            # El coste de envejecer depende de la estación
            coste_energia = ecosistema.estaciones[ecosistema.estacion_actual]['coste_energia']
            self._energia -= coste_energia

            log = f"{self._nombre} ha envejecido. E: {self._energia}, S: {self._sed}"
            return log + self.verificar_estado(ecosistema)
        return ""

    def verificar_estado(self, ecosistema: 'Ecosistema') -> str:
        """Comprueba si el animal sigue vivo. Devuelve log si muere."""
        if self._esta_vivo and (self._energia <= 0 or self._sed >= 150 or self._edad > 25): # Muerte por vejez
            self._esta_vivo = False
            # Al morir, deja una carcasa
            ecosistema.agregar_carcasa(self.x, self.y) # Corregido: 'ecosistema' ahora está definido
            return f" -> ¡{self._nombre} ha muerto!"
        return ""

    def reproducirse(self, ecosistema) -> str:
        """Intenta reproducirse si tiene suficiente energía y edad. Devuelve un log."""
        probabilidad = PROBABILIDAD_REPRODUCCION
        # Si está en un santuario, la probabilidad de reproducción aumenta
        if ecosistema.esta_en_santuario(self.x, self.y):
            probabilidad *= 2

        if self._esta_vivo and self._energia > ENERGIA_REPRODUCCION and self._edad > EDAD_ADULTA:
            # Probabilidad de reproducción para no saturar el ecosistema
            if random.random() < probabilidad:
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
            self._energia += ENERGIA_HIERBA
            self._energia = min(self._energia, self.genes['max_energia'])
            return f"{self._nombre} (Herbívoro) ha comido hierba. Energía: {self._energia}"
        # Si no hay hierba, simplemente no come. No hay penalización extra.
        return f"{self._nombre} (Herbívoro) no encontró hierba para comer."

    def _buscar_comida(self, ecosistema):
        """Los herbívoros no buscan activamente, pastan donde están."""
        return 0, 0 # Movimiento aleatorio

class Carnivoro(Animal):
    """Animal que come otros animales."""
    def comer(self, ecosistema) -> str:
        if not self._esta_vivo:
            return ""
        
        # Los depredadores no pueden cazar dentro de un santuario
        if ecosistema.esta_en_santuario(self.x, self.y):
            self._energia -= COSTE_BUSCAR_COMIDA / 2 # Pierde menos energía
            return f"{self._nombre} está en un santuario y no puede cazar."

        # Prioridad 1: Cazar presas vivas
        presa = ecosistema.encontrar_presa_cercana(self)
        if presa:
            self._energia += ENERGIA_CAZA
            self._energia = min(self._energia, self.genes['max_energia'])
            presa._energia = 0 # La presa muere instantáneamente
            # La presa cazada no deja carcasa, es consumida directamente.
            log_muerte = presa.verificar_estado(ecosistema)
            return f"{self._nombre} (Carnívoro) ha cazado y comido a {presa.nombre}." + log_muerte

        # Prioridad 2: Buscar carroña
        carcasa = ecosistema.comer_carcasa(self)
        if carcasa:
            energia_ganada = min(carcasa.energia_restante, 30) # No puede comer más de 30 de una vez
            self._energia += energia_ganada
            carcasa.energia_restante -= energia_ganada
            return f"{self._nombre} (Carnívoro) ha comido carroña. Energía: {self._energia}"

        # La penalización por no encontrar comida se aplica solo si no hay objetivo.
        # Esto se gestiona ahora en _buscar_comida.
        # Si llega aquí, significa que no tenía nada al alcance para comer en este turno.
        return f"{self._nombre} (Carnívoro) está buscando comida."


    def _buscar_comida(self, ecosistema):
        """Busca la presa más cercana y se mueve hacia ella."""
        # Un depredador siempre está buscando presas, no solo cuando tiene hambre.
        presa_cercana = ecosistema.encontrar_presa_cercana(self)
        if presa_cercana:
            dx = presa_cercana.x - self.x
            dy = presa_cercana.y - self.y
            return dx, dy
        
        # Si no ve presas, usa el "olfato" para moverse en la dirección general de la presa más cercana
        presa_lejana = ecosistema.encontrar_presa_mas_cercana_global(self)
        if presa_lejana:
            dx = presa_lejana.x - self.x
            dy = presa_lejana.y - self.y
            return dx, dy

        # Si no hay presas en absoluto, busca carroña
        carcasa_cercana = ecosistema.encontrar_carcasa_cercana(self.x, self.y, self.rango_vision * 2) # Olfato de carroña más amplio
        if carcasa_cercana:
            dx = carcasa_cercana.x - self.x
            dy = carcasa_cercana.y - self.y
            return dx, dy

        # Si no hay absolutamente nada que comer en el mapa, se mueve aleatoriamente y pierde energía.
        self._energia -= COSTE_BUSCAR_COMIDA
        self.verificar_estado(ecosistema) # Comprobar si muere de hambre
        return 0, 0 # Devuelve 0,0 para que se mueva aleatoriamente


class Omnivoro(Animal):
    """Animal que puede comer tanto plantas como otros animales."""
    def comer(self, ecosistema) -> str:
        if not self._esta_vivo:
            return ""
        
        # Los depredadores no pueden cazar dentro de un santuario
        if ecosistema.esta_en_santuario(self.x, self.y):
            # Pero sí pueden buscar bayas si están en una selva dentro del santuario
            return self._intentar_comer_bayas(ecosistema)

        # Decisión más inteligente: ¿qué está más cerca, bayas o presas?
        presa_cercana = ecosistema.encontrar_presa_cercana(self)
        selva_cercana = ecosistema.encontrar_selva_cercana(self.x, self.y, self.rango_vision)

        dist_presa = self._distancia_a(presa_cercana.x, presa_cercana.y) if presa_cercana else float('inf')
        dist_selva = ecosistema._distancia_a_rect(self.x, self.y, selva_cercana.rect) if selva_cercana else float('inf')

        # Opción 1: Cazar si la presa está más cerca (o no hay selvas) y hay presa.
        if presa_cercana and dist_presa <= dist_selva:
            self._energia += ENERGIA_CAZA
            self._energia = min(self._energia, self.genes['max_energia'])
            presa_cercana._energia = 0
            log_muerte = presa_cercana.verificar_estado(ecosistema)
            return f"{self._nombre} (Omnívoro) ha cazado a {presa_cercana.nombre}." + log_muerte

        # Opción 1.5: Comer carroña si está más cerca que las bayas
        carcasa_cercana = ecosistema.encontrar_carcasa_cercana(self.x, self.y, self.rango_vision)
        dist_carcasa = self._distancia_a(carcasa_cercana.x, carcasa_cercana.y) if carcasa_cercana else float('inf')

        if carcasa_cercana and dist_carcasa < dist_selva:
            if ecosistema.comer_carcasa(self):
                self._energia += 20 # Ganan un poco menos que los carnívoros de la carroña
                return f"{self._nombre} (Omnívoro) ha comido carroña. Energía: {self._energia}"

        # Opción 2: Comer bayas si está en una selva.
        return self._intentar_comer_bayas(ecosistema)

    def _intentar_comer_bayas(self, ecosistema):
        """Lógica separada para comer bayas, reutilizable."""
        if ecosistema.comer_bayas(self):
            self._energia += ENERGIA_BAYAS
            self._energia = min(self._energia, self.genes['max_energia'])
            return f"{self._nombre} (Omnívoro) ha comido bayas. Energía: {self._energia}"
        else:
            # Si llega aquí, es porque no había bayas en la selva en la que está.
            # La penalización real por no encontrar comida se gestiona en _buscar_comida.
            return f"{self._nombre} (Omnívoro) buscó bayas sin éxito."

    def _buscar_comida(self, ecosistema):
        """Los omnívoros buscan selvas si tienen hambre."""
        # La lógica de búsqueda de comida ya está en comer(), aquí solo se mueve.
        # Podríamos hacer que se mueva hacia la comida más prometedora.
        selva_cercana = ecosistema.encontrar_selva_cercana(self.x, self.y, self.rango_vision)
        if selva_cercana:
            dx = selva_cercana.rect.centerx - self.x
            dy = selva_cercana.rect.centery - self.y
            return dx, dy

        # Olfato para presas si no hay selvas cerca
        presa_lejana = ecosistema.encontrar_presa_mas_cercana_global(self)
        if presa_lejana:
            dx = presa_lejana.x - self.x
            dy = presa_lejana.y - self.y
            return dx, dy

        # Si no hay objetivos, se mueve aleatoriamente y pierde energía.
        self._energia -= COSTE_BUSCAR_COMIDA
        self.verificar_estado(ecosistema)
        return 0, 0

# --- Clases de Animales Específicos ---

class Conejo(Herbivoro):
    """Un herbívoro específico."""
    pass

class Raton(Herbivoro):
    """Un herbívoro específico."""
    pass

class Leopardo(Carnivoro):
    """Un carnívoro específico."""
    pass

class Gato(Carnivoro):
    """Un carnívoro específico."""
    pass

class Cerdo(Omnivoro):
    """Un omnívoro específico."""
    pass

class Mono(Omnivoro):
    """Un omnívoro específico."""
    pass

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
            "hierba": 100,
            "carcasas": []
        }
        self.terreno = {
            "montanas": [
                Montana((50, 50, 100, 150)),
                Montana((600, 400, 150, 120))
            ],
            "praderas": [
                Pradera((20, 400, 150, 150)) # Nueva pradera fértil
            ],
            "rios": [
                Rio((0, 300, 500, 40)),
                Rio((460, 100, 40, 240)),
                Rio((650, 600, 150, 30)) # Nuevo río pequeño
            ],
            "selvas": [
                Selva((200, 450, 250, 180)),
                Selva((20, 20, 100, 100)) # Nueva selva pequeña
            ],
            "santuarios": [
                Santuario((550, 50, 200, 200)),
                Santuario((20, 560, 180, 120)) # Nuevo santuario en la esquina
            ],
        }
        # --- Estaciones y Clima ---
        self.dia_total = 0
        self.dias_por_estacion = 20
        self.estacion_actual = "Primavera"
        self.estaciones = {
            "Primavera": {"crecimiento": 1.5, "coste_energia": 1},
            "Verano":    {"crecimiento": 1.0, "coste_energia": 2},
            "Otoño":     {"crecimiento": 0.5, "coste_energia": 3},
            "Invierno":  {"crecimiento": 0.1, "coste_energia": 4}
        }
        self.clima_actual = "Normal"

        self.animales_nuevos = [] # Lista para las crías nacidas en el día

    def encontrar_presa_cercana(self, depredador):
        """Encuentra la presa más cercana dentro del rango de visión del depredador."""
        presas_posibles = [
            animal for animal in self.animales 
            if isinstance(animal, (Herbivoro, Omnivoro)) and animal.esta_vivo and animal != depredador and
            depredador._distancia_a(animal.x, animal.y) < depredador.rango_vision and
            not self.esta_en_santuario(animal.x, animal.y) # No se puede cazar presas en santuarios
        ]
        if not presas_posibles:
            return None
        # Devuelve la presa más cercana
        return min(presas_posibles, key=lambda p: depredador._distancia_a(p.x, p.y))

    def encontrar_presa_mas_cercana_global(self, depredador):
        """Encuentra la presa más cercana en todo el mapa (olfato)."""
        presas_posibles = [
            animal for animal in self.animales 
            if isinstance(animal, (Herbivoro, Omnivoro)) and animal.esta_vivo and animal != depredador and
            not self.esta_en_santuario(animal.x, animal.y)
        ]
        if not presas_posibles:
            return None
        return min(presas_posibles, key=lambda p: depredador._distancia_a(p.x, p.y))

    def encontrar_depredador_cercano(self, presa):
        """Encuentra el carnívoro más cercano a una presa."""
        depredadores_cercanos = [
            animal for animal in self.animales
            if isinstance(animal, Carnivoro) and animal.esta_vivo and
            presa._distancia_a(animal.x, animal.y) < presa.rango_vision
        ]
        if not depredadores_cercanos:
            return None
        # Devuelve el depredador más cercano
        return min(depredadores_cercanos, key=lambda d: presa._distancia_a(d.x, d.y))

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

    def encontrar_santuario_cercano(self, x, y, rango):
        """Encuentra el santuario más cercano dentro de un rango."""
        santuarios_cercanos = [s for s in self.terreno["santuarios"] if self._distancia_a_rect(x, y, s.rect) < rango]
        if not santuarios_cercanos:
            return None
        return min(santuarios_cercanos, key=lambda s: self._distancia_a_rect(x, y, s.rect))

    def encontrar_carcasa_cercana(self, x, y, rango):
        """Encuentra la carcasa más cercana dentro de un rango."""
        carcasas_cercanas = [c for c in self.recursos["carcasas"] if self._distancia_a_rect(x, y, pygame.Rect(c.x, c.y, 1, 1)) < rango]
        if not carcasas_cercanas:
            return None
        return min(carcasas_cercanas, key=lambda c: self._distancia_a_rect(x, y, pygame.Rect(c.x, c.y, 1, 1)))


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

    def esta_en_santuario(self, x, y):
        """Comprueba si una posición está dentro de un santuario."""
        for santuario in self.terreno["santuarios"]:
            if santuario.rect.collidepoint(x, y):
                return True
        return False

    def comer_bayas(self, animal):
        """Permite a un animal comer bayas si está en una selva con bayas."""
        for selva in self.terreno["selvas"]:
            if selva.rect.collidepoint(animal.x, animal.y) and selva.bayas > 0:
                selva.bayas -= 1
                return True
        return False

    def comer_carcasa(self, animal):
        """Permite a un animal comer de una carcasa si está cerca."""
        for carcasa in self.recursos["carcasas"]:
            if animal._distancia_a(carcasa.x, carcasa.y) < 20 and carcasa.energia_restante > 0:
                return carcasa
        return None

    def agregar_carcasa(self, x, y):
        """Añade una nueva carcasa al ecosistema."""
        # No dejar carcasas dentro de los ríos o montañas
        if not self.choca_con_terreno(x, y):
            nueva_carcasa = Carcasa(x, y)
            self.recursos["carcasas"].append(nueva_carcasa)

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

        # Crecimiento base de hierba + bonus por praderas
        self.recursos["hierba"] += int(10 * factor_crecimiento)
        for pradera in self.terreno["praderas"]:
            self.recursos["hierba"] += int(10 * factor_crecimiento) # Bonus de la pradera

        for selva in self.terreno["selvas"]:
            selva.crecer_recursos(factor_crecimiento)
        
        # Descomposición de carcasas
        for carcasa in self.recursos["carcasas"]:
            carcasa.dias_descomposicion += 1
            carcasa.energia_restante -= 5 # Pierde 5 de energía cada día
        self.recursos["carcasas"] = [c for c in self.recursos["carcasas"] if c.energia_restante > 0 and c.dias_descomposicion < 5]


        logs_dia.append(f"Estación: {self.estacion_actual}. Clima: {self.clima_actual}.")
        bayas_totales = sum(s.bayas for s in self.terreno["selvas"])
        carcasas_activas = len(self.recursos['carcasas'])
        logs_dia.append(f"Recursos: {self.recursos['hierba']} hierba, {bayas_totales} bayas, {carcasas_activas} carcasas.")


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

        # Asegurarse de que el animal no aparezca en una barrera
        while True:
            x = random.randint(20, SIM_WIDTH - 20)
            y = random.randint(20, SCREEN_HEIGHT - 20)
            if not self.choca_con_terreno(x, y):
                break
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
        tipos = {"Herbivoro": Herbivoro, "Carnivoro": Carnivoro, "Omnivoro": Omnivoro, "Conejo": Conejo, "Raton": Raton, "Leopardo": Leopardo, "Gato": Gato, "Cerdo": Cerdo, "Mono": Mono}
        for a_data in estado["animales"]:
            tipo_clase = tipos.get(a_data["tipo"])
            if tipo_clase:
                animal = tipo_clase(a_data["nombre"], a_data["x"], a_data["y"], a_data["edad"], a_data["energia"], genes=a_data.get("genes"))
                # Restaurar sed si está en los datos guardados
                animal._sed = a_data.get("sed", 0)
                self.animales.append(animal)