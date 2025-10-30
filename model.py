from abc import ABC, abstractmethod
import pygame
import json
import math
import random
from collections import defaultdict

# --- Constantes de la Simulación ---
# Estas constantes definen los límites del área donde los animales pueden moverse.
SIM_WIDTH = 800
SCREEN_HEIGHT = 700

# --- Constantes de Comportamiento Animal (Ajustadas para mayor supervivencia) ---
COSTE_MOVIMIENTO = 0.3        # Reducido aún más para que el movimiento sea menos costoso.
AUMENTO_SED_MOVIMIENTO = 0.3  # Los animales se deshidratan más lentamente.
VELOCIDAD_ANIMAL = 5          # Píxeles por paso de simulación
UMBRAL_SED_BEBER = 60         # Nivel de sed para buscar agua activamente
UMBRAL_HAMBRE_CARNIVORO = 70  # Nivel de energía para empezar a cazar
UMBRAL_HAMBRE_OMNIVORO = 60   # Nivel de energía para buscar comida
ENERGIA_HIERBA = 30           # Aumentado: la hierba es más nutritiva.
ENERGIA_CAZA = 80             # Aumentado: la caza es más recompensante.
ENERGIA_BAYAS = 35            # Aumentado: las bayas son más nutritivas.
ENERGIA_PEZ = 30              # Aumentado: los peces son más nutritivos.
COSTE_BUSCAR_COMIDA = 5       # Reducido: fallar en la búsqueda es menos penalizante.
PROBABILIDAD_REPRODUCCION = 0.02 # BUG FIX: Reducido al 2% para una población más estable.

# Constantes para la reproducción
ENERGIA_REPRODUCCION = 60 # Reducido: se necesita menos energía para reproducirse.
EDAD_ADULTA = 2 # Reducido: los animales alcanzan la madurez sexual antes.
DISTANCIA_MANADA = 80 # Rango en píxeles para que los animales se consideren en la misma manada

# --- Constantes para la Gestión de Recursos (Hierba) ---
CELL_SIZE = 20 # Tamaño de celda para la hierba
MAX_HIERBA_NORMAL = 70
MAX_HIERBA_PRADERA = 120

# --- Constantes para Nuevas Mecánicas de Realismo ---
EDAD_INDEPENDENCIA = 2 # Edad a la que una cría deja de seguir a su madre.
DURACION_RASTRO_OLOR = 20 # En "horas" de simulación. Un rastro se desvanece después de este tiempo.
DISTANCIA_CAPTURA = 15 # Distancia a la que un depredador puede atrapar a su presa.
DISTANCIA_REPRODUCCION = 50 # Distancia máxima para encontrar pareja.

# --- Constantes de Optimización ---
GRID_CELL_SIZE = 100 # Tamaño de celda para la rejilla espacial de animales. Más grande = menos celdas, pero más animales por celda.

class RastroOlor:
    """Representa un rastro de olor dejado por un animal."""
    def __init__(self, x, y, emisor):
        self.x = x
        self.y = y
        self.emisor = emisor # El animal que dejó el rastro
        self.tiempo_vida = DURACION_RASTRO_OLOR

# --- Clases del Entorno ---

class Terreno:
    """Clase base para elementos del entorno como ríos o montañas."""
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)

class Montana(Terreno):
    """Una barrera infranqueable."""
    pass

class Pez:
    """Representa un pez individual que se mueve dentro de un río."""
    def __init__(self, rio_origen):
        self.rio = rio_origen
        self.x = random.randint(self.rio.rect.left, self.rio.rect.right)
        self.y = random.randint(self.rio.rect.top, self.rio.rect.bottom)
        self.velocidad = 2

    def moverse(self):
        """Mueve el pez aleatoriamente dentro de su río."""
        self.x += random.randint(-self.velocidad, self.velocidad)
        self.y += random.randint(-self.velocidad, self.velocidad)
        # Asegurarse de que el pez permanezca dentro del río
        self.x = max(self.rio.rect.left, min(self.x, self.rio.rect.right))
        self.y = max(self.rio.rect.top, min(self.y, self.rio.rect.bottom))

class Rio(Terreno):
    """Otra barrera infranqueable."""
    def __init__(self, rect):
        super().__init__(rect)
        self.peces: list[Pez] = [] # Ahora es una lista de objetos Pez
        for _ in range(15): # Reducido: Empezar con 15 peces
            self.peces.append(Pez(self))

    def crecer_recursos(self, factor_crecimiento):
        if len(self.peces) < 50: # Reducido: Limitar la población máxima de peces por río
            for _ in range(int(1 * factor_crecimiento)): # Reducido: Crecimiento más lento
                self.peces.append(Pez(self))

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
    """Clase base abstracta para todos los animales de la simulación."""
    contador = 0

    def __init__(self, nombre: str, x: int, y: int, edad: int = 0, energia: int = 100, genes=None, es_nocturno=False, madre=None, reproduction_cooldown=0):
        self._nombre = nombre
        self.x = x
        self.y = y
        self._edad = max(0, edad)  # Prevenir edades negativas
        self._energia = max(0, min(energia, 100))  # Limitar energía entre 0 y 100
        self._sed = 0  # Nueva necesidad: 0 es saciado, 100 es sediento
        # --- Genética ---
        if genes is None:
            genes = {
                'max_energia': max(80, min(120, 100 + random.randint(-10, 10))),  # Limitar entre 80 y 120
                'rango_vision': max(60, min(140, 100 + random.randint(-20, 20)))  # Limitar entre 60 y 140
            }
        self.genes = genes
        self.rango_vision = self.genes['rango_vision']
        self._esta_vivo = True
        self.es_nocturno = es_nocturno
        # --- Cuidado Parental ---
        self.madre = madre if edad < EDAD_INDEPENDENCIA else None
        self.objetivo_actual = None  # Para fijar presas o depredadores
        # --- Memoria y Territorio ---
        self.memoria = {
            "ultimo_rio_visto": None,
            "ultima_comida_vista": None  # Puede ser una selva, carcasa, etc.
        }
        self.territorio_centro = (x, y)  # Por defecto, su lugar de nacimiento
        # Cache para optimización
        self._last_pos = (x, y)  # Cache última posición
        self._cached_neighbors = None  # Cache de vecinos
        self._cached_neighbors_time = 0  # Tiempo de último cálculo de vecinos
        self.reproduction_cooldown = reproduction_cooldown
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
        if not self._esta_vivo:
            return ""

        # --- Lógica de actividad diurna/nocturna ---
        es_de_noche = 19 <= ecosistema.hora_actual or ecosistema.hora_actual <= 6
        esta_activo = (self.es_nocturno and es_de_noche) or (not self.es_nocturno and not es_de_noche)
        
        if not esta_activo:
            self._energia -= COSTE_MOVIMIENTO / 4
            self._sed += AUMENTO_SED_MOVIMIENTO / 4
            return f"{self._nombre} está descansando."

        # --- Comportamiento de Cría ---
        if self.madre and self.madre.esta_vivo:
            dist_a_madre = self._distancia_a(self.madre.x, self.madre.y)
            if dist_a_madre > 30:
                dx = self.madre.x - self.x
                dy = self.madre.y - self.y
            else:
                dx = random.randint(-5, 5)
                dy = random.randint(-5, 5)
        else:
            # --- Lógica de Adultos ---
            self._energia -= COSTE_MOVIMIENTO 
            self._sed += AUMENTO_SED_MOVIMIENTO
            
            dx, dy = 0, 0

            # --- Lógica de movimiento inteligente ---
            if isinstance(self, (Herbivoro, Omnivoro)):
                dx, dy = self._buscar_amenaza(ecosistema)

            if dx == 0 and dy == 0 and self._sed > UMBRAL_SED_BEBER:
                rio_cercano = ecosistema.encontrar_rio_cercano(self.x, self.y, self.rango_vision)
                if rio_cercano:
                    self.memoria["ultimo_rio_visto"] = rio_cercano.rect.center
                    punto_cercano = min(
                        [(rio_cercano.rect.left, self.y), (rio_cercano.rect.right, self.y), (self.x, rio_cercano.rect.top), (self.x, rio_cercano.rect.bottom)],
                        key=lambda p: self._distancia_a(p[0], p[1])
                    )
                    dx = punto_cercano[0] - self.x
                    dy = punto_cercano[1] - self.y
                elif self.memoria["ultimo_rio_visto"]:
                    dx = self.memoria["ultimo_rio_visto"][0] - self.x
                    dy = self.memoria["ultimo_rio_visto"][1] - self.y

            if dx == 0 and dy == 0:
                dx, dy = self._buscar_comida(ecosistema)
            
            if dx == 0 and dy == 0 and isinstance(self, Herbivoro):
                dx, dy = self._buscar_manada(ecosistema)

            if dx == 0 and dy == 0:
                if isinstance(self, Carnivoro) and self._distancia_a(*self.territorio_centro) > 150:
                    dx = self.territorio_centro[0] - self.x
                    dy = self.territorio_centro[1] - self.y
                else:
                    dx = random.randint(-10, 10)
                    dy = random.randint(-10, 10)

        dist = math.sqrt(dx**2 + dy**2)
        if dist > 0:
            dx = (dx / dist) * VELOCIDAD_ANIMAL
            dy = (dy / dist) * VELOCIDAD_ANIMAL
        
        nueva_x = self.x + dx
        nueva_y = self.y + dy

        margen = 10
        if nueva_x < margen or nueva_x > SIM_WIDTH - margen:
            self.x = max(margen, min(self.x, SIM_WIDTH - margen))
            dx *= -1
        if nueva_y < margen or nueva_y > SCREEN_HEIGHT - margen:
            self.y = max(margen, min(self.y, SCREEN_HEIGHT - margen))
            dy *= -1

        nueva_x = self.x + dx
        nueva_y = self.y + dy
        
        nueva_x = max(0, min(nueva_x, SIM_WIDTH - 1))
        nueva_y = max(0, min(nueva_y, SCREEN_HEIGHT - 1))

        if not ecosistema.choca_con_terreno(nueva_x, nueva_y):
            self.x = nueva_x
            self.y = nueva_y

        if ecosistema.esta_en_rio(self.x, self.y):
            self._sed = 0
            self._energia -= COSTE_MOVIMIENTO
            log_bebida = f" ¡{self._nombre} está cruzando un río!"
        else:
            log_bebida = ""

        if ecosistema.hora_actual % 2 == 0:
            ecosistema.agregar_rastro_olor(self.x, self.y, self)

        log = f"{self._nombre} se ha movido. Energía: {self._energia}, Sed: {self._sed}." + log_bebida
        return log + self.verificar_estado(ecosistema)

    def envejecer(self, ecosistema: 'Ecosistema') -> str:
        """Incrementa la edad y reduce energía. Devuelve un log."""
        if self._esta_vivo:
            self._edad += 1
            # El coste de envejecer depende de la estación
            coste_energia = ecosistema.estaciones[ecosistema.estacion_actual]['coste_energia']
            self._energia -= coste_energia

            # Comprobar si la cría se independiza
            if self.edad >= EDAD_INDEPENDENCIA:
                self.madre = None
            
            if self.reproduction_cooldown > 0: # BUG FIX: Reducir cooldown
                self.reproduction_cooldown -= 1

            log = f"{self._nombre} ha envejecido. E: {self._energia}, S: {self._sed}"
            return log + self.verificar_estado(ecosistema)
        return ""

    def verificar_estado(self, ecosistema: 'Ecosistema') -> str:
        """Comprueba si el animal sigue vivo. Devuelve log si muere."""
        if self._esta_vivo and (self._energia <= 0 or self._sed >= 150 or self._edad > 100): # Muerte por vejez (aumentado a 100)
            self._esta_vivo = False
            # Al morir, deja una carcasa
            ecosistema.agregar_carcasa(self.x, self.y) # Corregido: 'ecosistema' ahora está definido
            return f" -> ¡{self._nombre} ha muerto!"
        return ""

    def _crear_cria(self, ecosistema, pareja):
        """Lógica centralizada para crear una cría. Reutilizada por todas las clases."""
        # Verificar que ambos padres tengan suficiente energía
        if self._energia < 45 or pareja._energia < 45:
            return None
        
        self._energia = max(0, self._energia - 40)
        pareja._energia = max(0, pareja._energia - 40)

        # BUG FIX: Añadir cooldown de reproducción
        self.reproduction_cooldown = 15 # 15 días de espera
        pareja.reproduction_cooldown = 15

        # --- Lógica de Herencia Genética Sexual Mejorada ---
        nuevos_genes = {}
        for gen in ['max_energia', 'rango_vision']:
            # Herencia mezclada: promedio con variación aleatoria
            valor_base = (self.genes[gen] + pareja.genes[gen]) / 2
            variacion = random.uniform(-0.1, 0.1) * valor_base  # ±10% de variación
            nuevos_genes[gen] = valor_base + variacion
        
        # Limitar valores dentro de rangos razonables
        nuevos_genes['max_energia'] = max(80, min(120, nuevos_genes['max_energia']))
        nuevos_genes['rango_vision'] = max(60, min(140, nuevos_genes['rango_vision']))

        # Crear una cría del mismo tipo
        tipo_animal = type(self)
        nombre_cria = f"{tipo_animal.__name__.rstrip('o')} {getattr(tipo_animal, 'contador', 0) + 1}"
        cria = tipo_animal(nombre_cria, self.x, self.y, genes=nuevos_genes, es_nocturno=self.es_nocturno, madre=self)
        
        ecosistema.animales_nuevos.append(cria) # Añadir a una lista temporal
        return f"¡{self._nombre} y {pareja.nombre} se han reproducido! Nace {nombre_cria}."

    def reproducirse(self, ecosistema) -> str:
        """Intenta reproducirse si tiene suficiente energía y edad. Devuelve un log."""
        # BUG FIX: Comprobar cooldown
        if not (self._esta_vivo and self._energia > ENERGIA_REPRODUCCION and self._edad > EDAD_ADULTA and self.reproduction_cooldown == 0):
            return ""

        # Buscar una pareja cercana que también cumpla los requisitos
        pareja = ecosistema.encontrar_pareja_cercana(self)
        # BUG FIX: Comprobar también el cooldown de la pareja
        if pareja and pareja.reproduction_cooldown == 0:
            probabilidad = PROBABILIDAD_REPRODUCCION
            if ecosistema.esta_en_santuario(self.x, self.y):
                probabilidad *= 2 # Bonus del santuario

            if random.random() < probabilidad:
                return self._crear_cria(ecosistema, pareja)
        return ""

    def _buscar_amenaza(self, ecosistema):
        """Busca un depredador y lo fija como objetivo para huir."""
        depredador_cercano = ecosistema.encontrar_depredador_cercano(self)
        if depredador_cercano:
            self.objetivo_actual = depredador_cercano # Fija la amenaza
            # Huir en dirección opuesta
            dx = self.x - depredador_cercano.x
            dy = self.y - depredador_cercano.y
            return dx, dy
        return 0, 0

    def _evitar_bordes(self):
        """Si el animal está muy cerca de un borde, genera un vector de movimiento para alejarse o moverse en paralelo."""
        margen_borde = 50
        dx, dy = 0, 0

        if self.x < margen_borde:
            dx = 1 # Moverse a la derecha
        elif self.x > SIM_WIDTH - margen_borde:
            dx = -1 # Moverse a la izquierda

        if self.y < margen_borde:
            dy = 1 # Moverse hacia abajo
        elif self.y > SCREEN_HEIGHT - margen_borde:
            dy = -1 # Moverse hacia arriba
        
        return dx, dy

    def __str__(self):
        estado = "Vivo" if self._esta_vivo else "Muerto"
        return f"Animal: {self._nombre}, Tipo: {self.__class__.__name__}, Edad: {self._edad}, Energía: {self._energia}, Estado: {estado}"

class Herbivoro(Animal):
    """Animal que solo come plantas."""
    def comer(self, ecosistema) -> str:
        if self._esta_vivo and self._energia < self.genes['max_energia']:
            # Consume hierba de la celda actual
            if ecosistema.comer_hierba(self.x, self.y):
                self.memoria["ultima_comida_vista"] = (self.x, self.y) # Recuerda esta zona de pasto
                self._energia += ENERGIA_HIERBA
                self._energia = min(self._energia, self.genes['max_energia'])
                return f"{self._nombre} (Herbívoro) ha comido hierba. Energía: {self._energia}"
        return "" # No devuelve log si no come

    def _buscar_comida(self, ecosistema):
        """Los herbívoros ahora buscan las celdas con más hierba."""
        mejor_celda = ecosistema.encontrar_mejor_pasto_cercano(self.x, self.y, self.rango_vision)
        if mejor_celda:
            dest_x = mejor_celda[0]
            dest_y = mejor_celda[1]
            self.memoria["ultima_comida_vista"] = (dest_x, dest_y) # Guardar en memoria
            # Moverse hacia el centro de la mejor celda encontrada
            dx = dest_x - self.x
            dy = dest_y - self.y
            return dx, dy
        
        # Si no ve hierba pero recuerda un buen lugar, va hacia él
        elif self.memoria["ultima_comida_vista"]:
            dx = self.memoria["ultima_comida_vista"][0] - self.x
            dy = self.memoria["ultima_comida_vista"][1] - self.y
            return dx, dy
        
        # Si no ve hierba, se mueve aleatoriamente
        return 0, 0

    def reproducirse(self, ecosistema) -> str:
        """
        Los herbívoros tienen una mayor probabilidad de reproducción para mantener
        la base de la cadena alimenticia.
        """
        # Los herbívoros tienen una probabilidad de reproducción 1.5x mayor.
        # En lugar de modificar la constante global, calculamos la probabilidad aquí.
        if not (self._esta_vivo and self._energia > ENERGIA_REPRODUCCION and self._edad > EDAD_ADULTA):
            return ""

        pareja = ecosistema.encontrar_pareja_cercana(self)
        if pareja:
            # Usamos la probabilidad base y la multiplicamos por nuestro factor.
            probabilidad_aumentada = PROBABILIDAD_REPRODUCCION * 1.5
            if ecosistema.esta_en_santuario(self.x, self.y):
                probabilidad_aumentada *= 2 # Bonus del santuario

            if random.random() < probabilidad_aumentada:
                return self._crear_cria(ecosistema, pareja)
        return ""

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
        # La caza ahora es un proceso. 'comer' solo se ejecuta si la caza tiene éxito.
        if self.objetivo_actual and isinstance(self.objetivo_actual, (Herbivoro, Omnivoro)) and self._distancia_a(self.objetivo_actual.x, self.objetivo_actual.y) < DISTANCIA_CAPTURA:
            presa_atrapada = self.objetivo_actual
            self.territorio_centro = (self.x, self.y) # Actualiza el centro de su territorio a la ubicación de la caza exitosa
            self._energia += ENERGIA_CAZA
            self._energia = min(self._energia, self.genes['max_energia'])
            presa_atrapada._energia = 0 # La presa muere
            self.objetivo_actual = None # La caza ha terminado, limpiar objetivo
            log_muerte = presa_atrapada.verificar_estado(ecosistema)
            return f"{self._nombre} (Carnívoro) ha cazado y comido a {presa_atrapada.nombre}." + log_muerte

        # Prioridad 2: Buscar carroña
        carcasa = ecosistema.comer_carcasa(self)
        if carcasa:
            energia_ganada = min(carcasa.energia_restante, 30) # No puede comer más de 30 de una vez
            self.memoria["ultima_comida_vista"] = (carcasa.x, carcasa.y)
            self._energia += energia_ganada
            carcasa.energia_restante -= energia_ganada
            return f"{self._nombre} (Carnívoro) ha comido carroña. Energía: {self._energia}"

        # Última opción: Pescar si está cerca de un río
        # Solo pesca si tiene hambre y está cerca de un río.
        if self._energia < UMBRAL_HAMBRE_CARNIVORO and ecosistema.esta_en_rio(self.x, self.y):
            if ecosistema.comer_peces(self, self.rango_vision / 4): # Rango de pesca corto
                self._energia += ENERGIA_PEZ
                self._energia = min(self._energia, self.genes['max_energia'])
                return f"{self._nombre} (Carnívoro) ha pescado un pez. Energía: {self._energia}"

        # La penalización por no encontrar comida se aplica solo si no hay objetivo.
        # Esto se gestiona ahora en _buscar_comida.
        # Si llega aquí, significa que no tenía nada al alcance para comer en este turno.
        return f"{self._nombre} (Carnívoro) está buscando comida."


    def _buscar_comida(self, ecosistema):
        """Busca la presa más cercana y se mueve hacia ella."""
        # Si ya está cazando, no tiene hambre, o no hay presas, no busca.
        if self.objetivo_actual or self._energia > UMBRAL_HAMBRE_CARNIVORO or not ecosistema.presas_disponibles:
            return 0, 0

        # --- Lógica de Caza en Manada ---
        # La fuerza de grupo ya está pre-calculada en el ecosistema para este turno.
        fuerza_cazadores = ecosistema.fuerza_de_grupo.get(self, 1)
        presa_potencial = ecosistema.encontrar_presa_cercana(self, fuerza_cazadores)

        if presa_potencial:
            self.objetivo_actual = presa_potencial # ¡A cazar!
            # --- OPTIMIZACIÓN CRÍTICA: Usar la rejilla espacial para encontrar aliados ---
            aliados_cercanos = ecosistema._obtener_animales_cercanos(self)
            for aliado in aliados_cercanos:
                if isinstance(aliado, type(self)) and aliado is not self and self._distancia_a(aliado.x, aliado.y) < DISTANCIA_MANADA:
                    if not aliado.objetivo_actual: # No interrumpir si ya están cazando
                        aliado.objetivo_actual = presa_potencial
            return presa_potencial.x - self.x, presa_potencial.y - self.y
        
        # Si no ve presas, busca rastros de olor
        rastro_interesante = ecosistema.encontrar_rastro_cercano(self)
        if rastro_interesante:
            dx = rastro_interesante.x - self.x
            dy = rastro_interesante.y - self.y
            return dx, dy

        # Si no hay rastros, busca carroña
        carcasa_cercana = ecosistema.encontrar_carcasa_cercana(self.x, self.y, self.rango_vision * 2) # Olfato de carroña más amplio
        if carcasa_cercana:
            self.memoria["ultima_comida_vista"] = (carcasa_cercana.x, carcasa_cercana.y)
            dx = carcasa_cercana.x - self.x
            dy = carcasa_cercana.y - self.y
            return dx, dy

        # Si no hay nada de lo anterior, busca un río como último recurso
        rio_cercano = ecosistema.encontrar_rio_cercano(self.x, self.y, self.rango_vision * 2)
        if rio_cercano:
            self.memoria["ultimo_rio_visto"] = rio_cercano.rect.center
            dx = rio_cercano.rect.centerx - self.x
            dy = rio_cercano.rect.centery - self.y
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

        # --- Lógica de Caza Corregida ---
        # El método 'comer' ahora solo se activa si el depredador ya está sobre su objetivo.
        # La decisión de cazar y la persecución se gestionan en 'moverse' y '_buscar_comida'.
        if self.objetivo_actual and isinstance(self.objetivo_actual, (Herbivoro, Omnivoro)) and self._distancia_a(self.objetivo_actual.x, self.objetivo_actual.y) < DISTANCIA_CAPTURA:
            presa_atrapada = self.objetivo_actual
            self._energia += ENERGIA_CAZA
            self._energia = min(self._energia, self.genes['max_energia'])
            presa_atrapada._energia = 0
            self.objetivo_actual = None # La caza ha terminado, limpiar objetivo
            log_muerte = presa_atrapada.verificar_estado(ecosistema)
            return f"{self._nombre} (Omnívoro) ha cazado a {presa_atrapada.nombre}." + log_muerte

        # Opción 2: Comer carroña si está más cerca que las bayas
        carcasa_cercana = ecosistema.encontrar_carcasa_cercana(self.x, self.y, self.rango_vision)
        dist_carcasa = self._distancia_a(carcasa_cercana.x, carcasa_cercana.y) if carcasa_cercana else float('inf')

        if carcasa_cercana and dist_carcasa < 20: # Si está muy cerca de una carcasa
            if ecosistema.comer_carcasa(self):
                self._energia += 20 # Ganan un poco menos que los carnívoros de la carroña
                return f"{self._nombre} (Omnívoro) ha comido carroña. Energía: {self._energia}"

        # Opción 3: Comer bayas si está en una selva.
        log_bayas = self._intentar_comer_bayas(ecosistema)
        if "ha comido bayas" in log_bayas:
            return log_bayas

        # Última opción: Pescar si está cerca de un río
        # Solo pesca si tiene hambre y está cerca de un río.
        if self._energia < UMBRAL_HAMBRE_OMNIVORO and ecosistema.esta_en_rio(self.x, self.y) and ecosistema.comer_peces(self, self.rango_vision / 4):
            self._energia += ENERGIA_PEZ
            self._energia = min(self._energia, self.genes['max_energia'])
            return f"{self._nombre} (Omnívoro) ha pescado un pez. Energía: {self._energia}"
        
        return f"{self._nombre} (Omnívoro) buscó comida sin éxito."

    def _intentar_comer_bayas(self, ecosistema):
        """Lógica separada para comer bayas, reutilizable."""
        if ecosistema.comer_bayas(self):
            self.memoria["ultima_comida_vista"] = (self.x, self.y) # Recuerda la selva
            self._energia += ENERGIA_BAYAS
            self._energia = min(self._energia, self.genes['max_energia'])
            return f"{self._nombre} (Omnívoro) ha comido bayas. Energía: {self._energia}"
        else:
            # Si llega aquí, es porque no había bayas en la selva en la que está.
            # La penalización real por no encontrar comida se gestiona en _buscar_comida.
            return ""

    def _buscar_comida(self, ecosistema):
        """Los omnívoros buscan selvas si tienen hambre."""
        # Si ya tiene un objetivo, no busca más
        if self.objetivo_actual:
            return 0, 0

        # Decide si cazar o buscar bayas
        selva_cercana = ecosistema.encontrar_selva_cercana(self.x, self.y, self.rango_vision)
        fuerza_cazadores = ecosistema.fuerza_de_grupo.get(self, 1)
        presa_cercana = ecosistema.encontrar_presa_cercana(self, fuerza_cazadores)

        dist_selva = self._distancia_a(selva_cercana.rect.centerx, selva_cercana.rect.centery) if selva_cercana else float('inf')
        dist_presa = self._distancia_a(presa_cercana.x, presa_cercana.y) if presa_cercana else float('inf') # La distancia ya se calcula dentro de encontrar_presa_cercana

        # Decidir si cazar o buscar bayas basado en la cercanía
        if dist_presa < dist_selva and presa_cercana:
            # Cazar es la mejor opción
            self.objetivo_actual = presa_cercana
            return presa_cercana.x - self.x, presa_cercana.y - self.y
        elif selva_cercana:
            # Buscar bayas es la mejor opción
            self.memoria["ultima_comida_vista"] = selva_cercana.rect.center
            dx = selva_cercana.rect.centerx - self.x
            dy = selva_cercana.rect.centery - self.y
            return dx, dy
        elif presa_cercana:
            # No hay selvas, pero sí presas, así que cazamos
            self.objetivo_actual = presa_cercana
            return presa_cercana.x - self.x, presa_cercana.y - self.y
        elif self.memoria["ultima_comida_vista"]: # Si no ve nada, ir a la última comida recordada
            return self.memoria["ultima_comida_vista"][0] - self.x, self.memoria["ultima_comida_vista"][1] - self.y

        # Si no, busca un río si tiene hambre
        rio_cercano = ecosistema.encontrar_rio_cercano(self.x, self.y, self.rango_vision * 2)
        if rio_cercano:
            self.memoria["ultimo_rio_visto"] = rio_cercano.rect.center
            dx = rio_cercano.rect.centerx - self.x
            dy = rio_cercano.rect.centery - self.y
            return dx, dy

        # Si no hay objetivos, se mueve aleatoriamente y pierde energía.
        self._energia -= COSTE_BUSCAR_COMIDA
        self.verificar_estado(ecosistema)
        return 0, 0

# --- Clases de Animales Específicos ---

class Conejo(Herbivoro):
    """Un herbívoro específico."""
    pass

class Cabra(Herbivoro):
    """Un herbívoro que se siente cómodo cerca de las montañas."""
    pass

class Raton(Herbivoro):
    """Un herbívoro específico."""
    def __init__(self, nombre: str, x: int, y: int, edad: int = 0, energia: int = 100, genes=None, es_nocturno=True, madre=None, reproduction_cooldown=0):
        super().__init__(nombre, x, y, edad, energia, genes, es_nocturno, madre=madre, reproduction_cooldown=reproduction_cooldown)

class Leopardo(Carnivoro):
    """Un carnívoro específico."""
    def __init__(self, nombre: str, x: int, y: int, edad: int = 0, energia: int = 100, genes=None, es_nocturno=True, madre=None, reproduction_cooldown=0):
        super().__init__(nombre, x, y, edad, energia, genes, es_nocturno, madre=madre, reproduction_cooldown=reproduction_cooldown)


class Gato(Carnivoro):
    """Un carnívoro específico."""
    pass

class Cerdo(Omnivoro):
    """Un omnívoro específico."""
    pass

class Mono(Omnivoro):
    """Un omnívoro específico."""
    pass

class Halcon(Carnivoro):
    """Un carnívoro volador que puede atravesar obstáculos."""
    def __init__(self, nombre: str, x: int, y: int, edad: int = 0, energia: int = 100, genes=None, es_nocturno=False, madre=None, reproduction_cooldown=0):
        super().__init__(nombre, x, y, edad, energia, genes, es_nocturno, madre=madre, reproduction_cooldown=reproduction_cooldown)
        self.puede_volar = True
    
    def moverse(self, ecosistema) -> str:
        """Los halcones pueden volar sobre obstáculos."""
        # Heredar toda la lógica de movimiento de Animal pero sin chequeo de colisiones
        if not self._esta_vivo:
            return ""
        
        if self.madre and self.madre.esta_vivo:
            return super().moverse(ecosistema)  # Las crías siguen las reglas normales
            
        # El resto del movimiento es similar pero con más libertad
        self._energia -= COSTE_MOVIMIENTO * 1.5  # Volar consume más energía
        self._sed += AUMENTO_SED_MOVIMIENTO
        
        dx, dy = 0, 0
        if self.objetivo_actual and self.objetivo_actual.esta_vivo:
            dx = self.objetivo_actual.x - self.x
            dy = self.objetivo_actual.y - self.y
        else:
            # Comportamiento específico de búsqueda aérea
            dx, dy = self._buscar_comida(ecosistema)
            
        if dx == 0 and dy == 0:
            dx = random.randint(-15, 15)  # Mayor rango de movimiento aleatorio
            dy = random.randint(-15, 15)
            
        dist = math.sqrt(dx**2 + dy**2)
        if dist > 0:
            dx = (dx / dist) * VELOCIDAD_ANIMAL * 1.5  # Los halcones son más rápidos
            dy = (dy / dist) * VELOCIDAD_ANIMAL * 1.5
            
        self.x = max(0, min(self.x + dx, SIM_WIDTH - 10))
        self.y = max(0, min(self.y + dy, SCREEN_HEIGHT - 10))
        
        # Los halcones no dejan rastros en el aire
        log = f"{self._nombre} vuela por el aire. Energía: {self._energia}, Sed: {self._sed}."
        return log + self.verificar_estado(ecosistema)

class Insecto(Herbivoro):
    """Un pequeño herbívoro que sirve como presa para aves y otros depredadores."""
    def __init__(self, nombre: str, x: int, y: int, edad: int = 0, energia: int = 100, genes=None, es_nocturno=False, madre=None, reproduction_cooldown=0):
        # Los insectos tienen genes diferentes por defecto
        if genes is None:
            genes = {
                'max_energia': max(30, min(50, 40 + random.randint(-5, 5))),  # Menos energía máxima
                'rango_vision': max(40, min(80, 60 + random.randint(-10, 10)))  # Menor rango de visión
            }
        super().__init__(nombre, x, y, edad, energia, genes, es_nocturno, madre=madre, reproduction_cooldown=reproduction_cooldown)
    
    def moverse(self, ecosistema) -> str:
        """Los insectos se mueven de forma más errática y rápida."""
        if not self._esta_vivo:
            return ""
            
        self._energia -= COSTE_MOVIMIENTO * 0.5  # Los insectos gastan menos energía al moverse
        self._sed += AUMENTO_SED_MOVIMIENTO * 0.5
        
        # Movimiento más errático
        dx = random.randint(-20, 20)
        dy = random.randint(-20, 20)
        
        # Si hay depredador cerca, intentar escapar
        depredador = ecosistema.encontrar_depredador_cercano(self)
        if depredador:
            dx = self.x - depredador.x
            dy = self.y - depredador.y
            
        dist = math.sqrt(dx**2 + dy**2)
        if dist > 0:
            dx = (dx / dist) * VELOCIDAD_ANIMAL * 1.2  # Los insectos son un poco más rápidos
            dy = (dy / dist) * VELOCIDAD_ANIMAL * 1.2
            
        nueva_x = max(0, min(self.x + dx, SIM_WIDTH - 10))
        nueva_y = max(0, min(self.y + dy, SCREEN_HEIGHT - 10))
        
        if not ecosistema.choca_con_terreno(nueva_x, nueva_y):
            self.x = nueva_x
            self.y = nueva_y
            
        log = f"{self._nombre} se mueve rápidamente. Energía: {self._energia}, Sed: {self._sed}."
        return log + self.verificar_estado(ecosistema)

class Selva(Terreno):
    """Zona donde crecen las bayas. No es una barrera."""
    def __init__(self, rect):
        super().__init__(rect)
        self.bayas = 25

    def crecer_recursos(self, factor_crecimiento):
        self.bayas += int(2 * factor_crecimiento)

class Ecosistema:
    """Gestiona el estado del entorno y los animales."""
    def __init__(self):
        self.animales: list[Animal] = []
        self.terreno = {
            "montanas": [],
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
                Rio((150, 0, 40, 300)),      # Nuevo río vertical izquierdo
                Rio((150, 150, 100, 40)),     # Nuevo afluente horizontal izquierdo
                Rio((450, 0, 40, 250)),      # Afluente norte
                Rio((450, 210, 200, 40)),     # Conexión afluente
                Rio((610, 210, 40, 490)),     # Río principal vertical
                Rio((0, 400, 610, 40))       # Afluente oeste
            ],
            "selvas": [
                Selva((200, 450, 250, 180)),
                Selva((20, 20, 100, 100)),
                Selva((500, 250, 150, 100)),
                Selva((700, 20, 80, 250)),
                Selva((550, 50, 200, 200)),
                Selva((20, 200, 120, 150))      # Nueva selva en el lado izquierdo
            ],
            "santuarios": [],
            "arboles": [], # Elementos decorativos
            "plantas": [], # Elementos decorativos
        }
        # --- Nuevo sistema de recursos ---
        self.recursos = {
            "carcasas": []
        }
        self.rastros_olor: list[RastroOlor] = []
        self.grid_width = SIM_WIDTH // CELL_SIZE
        self.grid_height = SCREEN_HEIGHT // CELL_SIZE
        self.grid_hierba = [[0 for _ in range(self.grid_height)] for _ in range(self.grid_width)]
        # Inicializar la hierba

        # --- Rejilla Espacial para Optimización ---
        self.grid_animales_width = math.ceil(SIM_WIDTH / GRID_CELL_SIZE)
        self.grid_animales_height = math.ceil(SCREEN_HEIGHT / GRID_CELL_SIZE)
        self.grid_animales = [[] for _ in range(self.grid_animales_width * self.grid_animales_height)]

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
            "Primavera": {"crecimiento": 1.5, "coste_energia": 0}, # Coste nulo en primavera
            "Verano":    {"crecimiento": 1.0, "coste_energia": 0}, # Sin coste de energía estacional en verano.
            "Otoño":     {"crecimiento": 0.5, "coste_energia": 1}, # Coste ligero en otoño.
            "Invierno":  {"crecimiento": 0.1, "coste_energia": 2}  # El invierno sigue siendo el más duro.
        }
        self.clima_actual = "Normal"

        self.animales_nuevos = [] # Lista para las crías nacidas en el día
        self.fuerza_de_grupo = {} # Cache para la fuerza de grupo de cada animal en el turno actual
        self.presas_disponibles = False # Flag para saber si hay presas en el mapa

        self._poblar_decoraciones() # Añadir árboles y plantas

    def _actualizar_rejilla_animales(self):
        """Limpia y re-pobla la rejilla espacial con la posición actual de los animales."""
        # Usar un diccionario estándar para evitar problemas con defaultdict y claves de tupla.
        self.grid_animales = {}
        
        for animal in self.animales:
            if animal.esta_vivo:
                grid_x = int(animal.x // GRID_CELL_SIZE)
                grid_y = int(animal.y // GRID_CELL_SIZE)
                cell_key = (grid_x, grid_y)
                if cell_key not in self.grid_animales:
                    self.grid_animales[cell_key] = []
                self.grid_animales[cell_key].append(animal)
                
                # Actualizar cache del animal
                animal._last_pos = (animal.x, animal.y)


    def encontrar_presa_cercana(self, depredador, fuerza_cazadores):
        """
        Encuentra la presa más vulnerable (mejor combinación de cercanía y aislamiento)
        dentro del rango de visión del depredador. USA LA REJILLA ESPACIAL.
        """
        mejor_presa = None
        mejor_puntuacion = float('inf')

        # Obtener animales solo de las celdas cercanas
        animales_cercanos = self._obtener_animales_cercanos(depredador)
        for presa in animales_cercanos:
            # Filtrar solo presas válidas y dentro del rango de visión
            if not (isinstance(presa, (Herbivoro, Omnivoro)) and presa.esta_vivo and presa != depredador):
                continue
            
            distancia = depredador._distancia_a(presa.x, presa.y)
            if distancia >= depredador.rango_vision:
                continue

            if self.esta_en_santuario(presa.x, presa.y):
                continue

            # Usar la fuerza de grupo pre-calculada
            fuerza_presas = self.fuerza_de_grupo.get(presa, 1)

            # Solo considerar atacar si la manada de cazadores es más fuerte
            if fuerza_cazadores > fuerza_presas:
                # Puntuación: penaliza la distancia. Un valor más bajo es mejor.
                # La fuerza ya se usó para filtrar, ahora solo importa la cercanía.
                puntuacion = distancia
                if puntuacion < mejor_puntuacion:
                    mejor_puntuacion = puntuacion
                    mejor_presa = presa
        
        return mejor_presa
        
    def encontrar_rastro_cercano(self, depredador):
        """Encuentra el rastro de olor de una presa más cercano."""
        rastros_interesantes = [
            r for r in self.rastros_olor
            if isinstance(r.emisor, (Herbivoro, Omnivoro)) and depredador._distancia_a(r.x, r.y) < depredador.rango_vision * 1.5
        ]
        if not rastros_interesantes:
            return None
        # Devuelve el rastro más "fresco" (con más tiempo de vida restante)
        return max(rastros_interesantes, key=lambda r: r.tiempo_vida)

    def encontrar_depredador_cercano(self, presa):
        """Encuentra el carnívoro más cercano a una presa."""
        animales_cercanos = self._obtener_animales_cercanos(presa)
        depredadores_cercanos = [
            animal for animal in animales_cercanos
            if isinstance(animal, Carnivoro) and animal.esta_vivo and
            presa._distancia_a(animal.x, animal.y) < presa.rango_vision
        ]
        if not depredadores_cercanos:
            return None
        # Devuelve el depredador más cercano
        return min(depredadores_cercanos, key=lambda d: presa._distancia_a(d.x, d.y))

    def encontrar_pareja_cercana(self, animal_buscando):
        """Encuentra una pareja compatible para la reproducción."""
        animales_cercanos = self._obtener_animales_cercanos(animal_buscando)
        for animal in animales_cercanos:
            if (animal is not animal_buscando and
                type(animal) is type(animal_buscando) and
                animal.esta_vivo and
                animal.edad > EDAD_ADULTA and
                animal.energia > ENERGIA_REPRODUCCION and
                animal_buscando._distancia_a(animal.x, animal.y) < DISTANCIA_REPRODUCCION):
                return animal
        return None

    def contar_aliados_cercanos(self, animal_origen, tipo_buscado):
        """Cuenta cuántos animales del mismo tipo están cerca de un animal dado."""
        animales_cercanos = self._obtener_animales_cercanos(animal_origen)
        contador = 0
        for otro_animal in animales_cercanos:
            if (otro_animal is not animal_origen and 
                isinstance(otro_animal, tipo_buscado) and
                animal_origen._distancia_a(otro_animal.x, otro_animal.y) < DISTANCIA_MANADA):
                contador += 1
        return contador

    def encontrar_rio_cercano(self, x, y, rango):
        """Encuentra el río más cercano dentro de un rango."""
        rios_cercanos = [r for r in self.terreno["rios"] if self._distancia_a_rect(x, y, r.rect) < rango]
        if not rios_cercanos:
            return None
        return min(rios_cercanos, key=lambda r: self._distancia_a_rect(x, y, r.rect))

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

    def encontrar_mejor_pasto_cercano(self, x, y, rango):
        """Encuentra la celda con más hierba dentro del rango de visión de un animal. Devuelve coordenadas de píxeles."""
        grid_x, grid_y = int(x // CELL_SIZE), int(y // CELL_SIZE)
        radio_busqueda = int(rango // CELL_SIZE)
        
        mejor_pos = None
        max_hierba = 0

        for gx in range(max(0, grid_x - radio_busqueda), min(self.grid_width, grid_x + radio_busqueda)):
            for gy in range(max(0, grid_y - radio_busqueda), min(self.grid_height, grid_y + radio_busqueda)):
                # No buscar comida en terreno infranqueable
                if not self.choca_con_terreno(gx * CELL_SIZE, gy * CELL_SIZE):
                    if self.grid_hierba[gx][gy] > max_hierba:
                        max_hierba = self.grid_hierba[gx][gy]
                        mejor_pos = (gx * CELL_SIZE + CELL_SIZE // 2, gy * CELL_SIZE + CELL_SIZE // 2)
        
        return mejor_pos

    def encontrar_carcasa_cercana(self, x, y, rango):
        """Encuentra la carcasa más cercana dentro de un rango."""
        carcasas_cercanas = [c for c in self.recursos["carcasas"] if self._distancia_a_rect(x, y, pygame.Rect(c.x, c.y, 1, 1)) < rango]
        if not carcasas_cercanas:
            return None
        return min(carcasas_cercanas, key=lambda c: self._distancia_a_rect(x, y, pygame.Rect(c.x, c.y, 1, 1)))


    def _distancia_a_rect(self, x, y, rect):
        """Calcula la distancia más corta desde un punto (x, y) al borde de un rectángulo."""
        # Encuentra el punto más cercano en el rectángulo al punto (x, y)
        closest_x = max(rect.left, min(x, rect.right))
        closest_y = max(rect.top, min(y, rect.bottom))
        
        # Calcula la distancia euclidiana a este punto más cercano
        return math.sqrt((x - closest_x)**2 + (y - closest_y)**2)

    def _obtener_animales_cercanos(self, animal):
        """Devuelve una lista de animales en la celda del animal y las celdas vecinas."""
        animales_en_rango = []
        grid_x = int(animal.x // GRID_CELL_SIZE)
        grid_y = int(animal.y // GRID_CELL_SIZE)

        for i in range(-1, 2):
            for j in range(-1, 2):
                vecino_x = grid_x + i
                vecino_y = grid_y + j

                if 0 <= vecino_x < self.grid_animales_width and 0 <= vecino_y < self.grid_animales_height:
                    cell_key = (vecino_x, vecino_y)
                    if cell_key in self.grid_animales:
                        animales_en_rango.extend(self.grid_animales[cell_key])
        
        # Eliminar duplicados si un animal estuviera en múltiples listas (no debería pasar con esta implementación)
        # y devolver una lista única.
        return list(set(animales_en_rango))


    def choca_con_terreno(self, x, y):
        """Comprueba si una posición colisiona con una barrera."""
        # Los ríos ya no son barreras. Solo los árboles son obstáculos.
        # Comprobar colisión con árboles (considerando un radio más pequeño para el tronco)
        radio_tronco = 5
        return any(math.sqrt((ax - x)**2 + (ay - y)**2) < radio_tronco for ax, ay in self.terreno["arboles"])

    def esta_en_rio(self, x, y):
        """Comprueba si un animal está dentro de un río."""
        for rio in self.terreno["rios"]:
            if rio.rect.collidepoint(x, y):
                return True
        return False

    def esta_en_santuario(self, x, y):
        """Comprueba si una posición está dentro de un santuario."""
        for santuario in self.terreno["santuarios"]:
            if santuario.rect.collidepoint(x, y):
                return True
        return False

    def comer_peces(self, animal, distancia_captura):
        """Permite a un animal pescar si está cerca de un río con peces. Optimizado para rendimiento."""
        rio_actual = None
        for rio in self.terreno["rios"]:
            if rio.rect.collidepoint(animal.x, animal.y):
                rio_actual = rio
                break
        
        if not rio_actual or not rio_actual.peces:
            return False

        # Optimización: solo buscar en peces cercanos
        peces_cercanos = []
        for pez in rio_actual.peces:
            dist = math.hypot(animal.x - pez.x, animal.y - pez.y)  # Más rápido que _distancia_a
            if dist < distancia_captura:
                peces_cercanos.append((pez, dist))
        
        if peces_cercanos:
            pez_atrapado, _ = min(peces_cercanos, key=lambda x: x[1])
            rio_actual.peces.remove(pez_atrapado)
            return True
        return False

    def comer_bayas(self, animal):
        """Permite a un animal comer bayas si está en una selva con bayas."""
        for selva in self.terreno["selvas"]:
            if selva.rect.collidepoint(animal.x, animal.y) and selva.bayas > 0:
                selva.bayas -= 1
                return True
        return False

    def comer_hierba(self, x, y):
        """Permite a un animal comer hierba de la celda en la que se encuentra."""
        grid_x = int(x // CELL_SIZE)
        grid_y = int(y // CELL_SIZE)
        if 0 <= grid_x < self.grid_width and 0 <= grid_y < self.grid_height:
            if self.grid_hierba[grid_x][grid_y] > 10: # Debe haber una cantidad mínima para comer
                self.grid_hierba[grid_x][grid_y] -= 10 # Consume 10 unidades de hierba
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

    def agregar_rastro_olor(self, x, y, emisor):
        """Añade un nuevo rastro de olor al ecosistema."""
        nuevo_rastro = RastroOlor(x, y, emisor)
        self.rastros_olor.append(nuevo_rastro)

    def _es_posicion_decoracion_valida(self, x, y, decoraciones_existentes, min_dist):
        """Comprueba si una posición está lo suficientemente lejos de otras decoraciones."""
        for dx, dy in decoraciones_existentes:
            dist = math.sqrt((x - dx)**2 + (y - dy)**2)
            if dist < min_dist:
                return False
        return True
    
    def _es_posicion_valida_para_vegetacion(self, x, y, decoraciones_existentes, min_dist):
        """Comprueba si una posición es válida para plantar algo (no en río y con suficiente espacio)."""
        if any(rio.rect.collidepoint(x, y) for rio in self.terreno["rios"]):
            return False
        return self._es_posicion_decoracion_valida(x, y, decoraciones_existentes, min_dist)

    def _poblar_decoraciones(self):
        """Añade elementos decorativos según su bioma."""
        self.terreno["arboles"].clear()
        self.terreno["plantas"].clear()
        
        decoraciones_todas = []
        intentos_max = 80 # Aumentamos los intentos para zonas muy densas
        margen = 5 # Margen para no generar en los bordes exactos de las zonas

        # 1. Poblar árboles en las selvas
        for selva in self.terreno["selvas"]:
            for _ in range(35): # 35 árboles por selva
                for _ in range(intentos_max):
                    x = random.randint(selva.rect.left + margen, selva.rect.right - margen)
                    y = random.randint(selva.rect.top + margen, selva.rect.bottom - margen)
                    if self._es_posicion_valida_para_vegetacion(x, y, decoraciones_todas, min_dist=35):
                        self.terreno["arboles"].append((x, y)); decoraciones_todas.append((x, y))
                        break

        # 2. Poblar plantas en zonas de alimento (praderas y selvas)
        zonas_alimento = self.terreno["praderas"] + self.terreno["selvas"]
        for zona in zonas_alimento:
            for _ in range(35): # 35 plantas por zona
                for _ in range(intentos_max):
                    x = random.randint(zona.rect.left + margen, zona.rect.right - margen)
                    y = random.randint(zona.rect.top + margen, zona.rect.bottom - margen)
                    if self._es_posicion_valida_para_vegetacion(x, y, decoraciones_todas, min_dist=20):
                        self.terreno["plantas"].append((x, y)); decoraciones_todas.append((x, y))
                        break

        # 3. Añadir algunas plantas repartidas por el mapa (que no estén en montañas/ríos)
        for _ in range(120): # 120 plantas adicionales
            for _ in range(intentos_max):
                x, y = random.randint(0, SIM_WIDTH), random.randint(0, SCREEN_HEIGHT)
                if not self.choca_con_terreno(x,y) and self._es_posicion_valida_para_vegetacion(x, y, decoraciones_todas, min_dist=20):
                    self.terreno["plantas"].append((x, y)); decoraciones_todas.append((x, y))
                    break

    def _actualizar_estacion(self):
        """Actualiza la estación del año."""
        indice_estacion = (self.dia_total // self.dias_por_estacion) % 4
        self.estacion_actual = list(self.estaciones.keys())[indice_estacion]

    def _actualizar_clima(self):
        # Lógica del clima
        if random.random() < 0.05: # 5% de probabilidad de sequía
            self.clima_actual = "Sequía"
        else:
            self.clima_actual = "Normal"

    def simular_dia(self) -> list[str]:
        """Ejecuta 24 ciclos de simulación (horas) y devuelve los logs."""
        logs_dia = []
        for _ in range(24): # 24 horas en un día
            logs_hora = self.simular_hora()
            # Podríamos decidir agregar solo logs importantes para no saturar
            # logs_dia.extend(logs_hora)
        return logs_dia # De momento devolvemos una lista vacía para no sobrecargar la UI

    def simular_hora(self) -> list[str]:
        """Ejecuta un ciclo de simulación de una hora y devuelve los logs."""
        logs_hora = []
        self.hora_actual += 1

        # --- Actualización de la Rejilla Espacial (OPTIMIZACIÓN) ---
        self._actualizar_rejilla_animales()

        # --- Pre-cálculo de optimización para el turno ---
        self.fuerza_de_grupo.clear()

        # Optimización: clasificar animales por tipo una vez por turno
        animales_por_tipo = defaultdict(list)
        for animal in self.animales:
            if animal.esta_vivo:
                animales_por_tipo[type(animal)].append(animal)
        
        # Comprobar presas disponibles usando la clasificación previa
        self.presas_disponibles = bool(animales_por_tipo.get(Herbivoro) or 
                                     animales_por_tipo.get(Omnivoro))
        
        # Calcular la fuerza de cada grupo en un solo paso O(n^2) pero solo una vez por hora.
        # Esto es mucho mejor que O(n^3) o superior que ocurría antes.
        for animal in self.animales:
            if animal.esta_vivo:
                if isinstance(animal, Herbivoro):
                    tipo_buscado = Herbivoro
                else: # Carnivoro y Omnivoro se alían para cazar
                    tipo_buscado = (Carnivoro, Omnivoro)
                # La fuerza de un animal es él mismo (1) más sus aliados cercanos.
                fuerza = 1 + self.contar_aliados_cercanos(animal, tipo_buscado)
                self.fuerza_de_grupo[animal] = fuerza


        # --- Acciones que ocurren cada hora ---
        random.shuffle(self.animales)
        for animal in self.animales:
            if animal.esta_vivo:
                logs_hora.append(animal.comer(self))
                logs_hora.append(animal.moverse(self))

        for rio in self.terreno["rios"]:
            for pez in rio.peces:
                pez.moverse()

        # --- Acciones que ocurren una vez al día (a medianoche) ---
        if self.hora_actual >= 24:
            self.hora_actual = 0
            self.dia_total += 1
            self._actualizar_estacion()
            self._actualizar_clima()

            logs_hora.append(f"--- NUEVO DÍA: {self.dia_total} ---")
            logs_hora.append(f"Estación: {self.estacion_actual}. Clima: {self.clima_actual}.")

            # Crecimiento de recursos
            factor_crecimiento = self.estaciones[self.estacion_actual]['crecimiento']
            if self.clima_actual == "Sequía":
                factor_crecimiento *= 0.1
                logs_hora.append("¡Una sequía azota la región!")

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

            # Descomposición de carcasas
            for c in self.recursos["carcasas"]: c.dias_descomposicion += 1
            self.recursos["carcasas"] = [c for c in self.recursos["carcasas"] if c.energia_restante > 0 and c.dias_descomposicion < 5]

            # Actualización y desvanecimiento de rastros de olor
            for rastro in self.rastros_olor:
                rastro.tiempo_vida -= 1
            self.rastros_olor = [r for r in self.rastros_olor if r.tiempo_vida > 0]

            # Envejecimiento y reproducción
            self.animales_nuevos = []
            for animal in self.animales:
                if animal.esta_vivo:
                    logs_hora.append(animal.envejecer(self))
                    logs_hora.append(animal.reproducirse(self))

        self.animales = [animal for animal in self.animales if animal.esta_vivo]
        self.animales.extend(self.animales_nuevos) # Añadir las crías a la lista principal

        return [log for log in logs_hora if log]

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
            "grid_hierba": self.grid_hierba,
            "selvas": [{"rect": list(s.rect), "bayas": s.bayas} for s in self.terreno["selvas"]],
            "rios": [{"rect": list(r.rect), "num_peces": len(r.peces)} for r in self.terreno["rios"]], # Guardar solo el número
            "animales": [
                {
                    "tipo": a.__class__.__name__,
                    "nombre": a.nombre, "x": a.x, "y": a.y, "edad": a.edad, "madre_nombre": a.madre.nombre if a.madre else None,
                    "energia": a.energia, "sed": a._sed, "genes": a.genes,
                    "es_nocturno": a.es_nocturno # Guardar el estado nocturno
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
        self.grid_hierba = estado.get("grid_hierba", self.grid_hierba) # .get para compatibilidad
        for i, s_data in enumerate(estado["selvas"]):
            self.terreno["selvas"][i].bayas = s_data["bayas"]
        for i, r_data in enumerate(estado.get("rios", [])): # Usar .get para compatibilidad con guardados antiguos
            rio = self.terreno["rios"][i]
            rio.peces = [] # Limpiar la lista actual
            for _ in range(r_data.get("num_peces", 20)): # Cargar el número guardado
                rio.peces.append(Pez(rio))

        self.animales = []
        animales_cargados = {} # Diccionario para mapear nombres a objetos animales
        tipos = {"Herbivoro": Herbivoro, "Carnivoro": Carnivoro, "Omnivoro": Omnivoro, "Conejo": Conejo, "Raton": Raton, "Cabra": Cabra, "Leopardo": Leopardo, "Gato": Gato, "Cerdo": Cerdo, "Mono": Mono, "Halcon": Halcon, "Insecto": Insecto}
        for a_data in estado["animales"]:
            tipo_clase = tipos.get(a_data["tipo"])
            es_nocturno = a_data.get("es_nocturno", False)
            if tipo_clase in [Leopardo, Raton]: # Raton y Leopardo son nocturnos por defecto
                es_nocturno = True
            if tipo_clase:
                animal = tipo_clase(a_data["nombre"], a_data["x"], a_data["y"], a_data["edad"], a_data["energia"], genes=a_data.get("genes"), es_nocturno=es_nocturno)
                animal._sed = a_data.get("sed", 0)
                self.animales.append(animal)
                animales_cargados[animal.nombre] = (animal, a_data.get("madre_nombre"))

        # Segundo paso: asignar las madres
        for nombre_animal, (animal_obj, nombre_madre) in animales_cargados.items():
            if nombre_madre and nombre_madre in animales_cargados:
                madre_obj, _ = animales_cargados[nombre_madre]
                if animal_obj.edad < EDAD_INDEPENDENCIA:
                    animal_obj.madre = madre_obj