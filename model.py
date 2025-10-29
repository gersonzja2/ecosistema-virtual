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
COSTE_MOVIMIENTO = 1          # Energía perdida al moverse
AUMENTO_SED_MOVIMIENTO = 1    # Sed ganada al moverse
VELOCIDAD_ANIMAL = 5          # Píxeles por paso de simulación
UMBRAL_SED_BEBER = 60         # Nivel de sed para buscar agua activamente
UMBRAL_HAMBRE_CARNIVORO = 70  # Nivel de energía para empezar a cazar
UMBRAL_HAMBRE_OMNIVORO = 60   # Nivel de energía para buscar comida
ENERGIA_HIERBA = 20
ENERGIA_CAZA = 60
ENERGIA_BAYAS = 25
ENERGIA_PEZ = 20
COSTE_BUSCAR_COMIDA = 10      # Energía perdida si no se encuentra comida
PROBABILIDAD_REPRODUCCION = 0.10 # 10% de probabilidad por día

# Constantes para la reproducción
ENERGIA_REPRODUCCION = 70 # Energía mínima para poder reproducirse
EDAD_ADULTA = 3 # Edad mínima para poder reproducirse
DISTANCIA_MANADA = 80 # Rango en píxeles para que los animales se consideren en la misma manada

# --- Constantes para la Gestión de Recursos (Hierba) ---
CELL_SIZE = 20
MAX_HIERBA_NORMAL = 70
MAX_HIERBA_PRADERA = 120

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
        for _ in range(30): # Empezar con 30 peces
            self.peces.append(Pez(self))

    def crecer_recursos(self, factor_crecimiento):
        if len(self.peces) < 100: # Limitar la población máxima de peces por río
            for _ in range(int(3 * factor_crecimiento)):
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
    """Clase base para todos los animales. Contiene la lógica y los datos."""
    def __init__(self, nombre: str, x: int, y: int, edad: int = 0, energia: int = 100, genes=None, es_nocturno=False):
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
        self.es_nocturno = es_nocturno
        self.objetivo_actual = None # Para fijar presas o depredadores
        # Contador para nombres únicos de crías
        # --- Memoria y Territorio ---
        self.memoria = {
            "ultimo_rio_visto": None,
            "ultima_comida_vista": None # Puede ser una selva, carcasa, etc.
        }
        self.territorio_centro = (x, y) # Por defecto, su lugar de nacimiento
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
            # --- Lógica de actividad diurna/nocturna ---
            es_de_noche = 19 <= ecosistema.hora_actual or ecosistema.hora_actual <= 6
            esta_activo = (self.es_nocturno and es_de_noche) or (not self.es_nocturno and not es_de_noche)

            if not esta_activo:
                # Comportamiento de descanso: gasta menos energía y no se mueve
                self._energia -= COSTE_MOVIMIENTO / 4 # Gasto energético mínimo por estar vivo
                self._sed += AUMENTO_SED_MOVIMIENTO / 4
                return f"{self._nombre} está descansando."

            # Si está activo, procede con la lógica normal
            self._energia -= COSTE_MOVIMIENTO 
            self._sed += AUMENTO_SED_MOVIMIENTO
            dx, dy = 0, 0

            # --- Lógica de estado ---
            # Si ya tiene un objetivo (presa o depredador), actuar sobre él es la máxima prioridad.
            if self.objetivo_actual and self.objetivo_actual.esta_vivo:
                if isinstance(self, (Carnivoro, Omnivoro)) and isinstance(self.objetivo_actual, (Herbivoro, Omnivoro)): # Es un depredador cazando
                    dx = self.objetivo_actual.x - self.x
                    dy = self.objetivo_actual.y - self.y
                elif isinstance(self, (Herbivoro, Omnivoro)) and isinstance(self.objetivo_actual, Carnivoro): # Es una presa huyendo
                    dx = self.x - self.objetivo_actual.x
                    dy = self.y - self.objetivo_actual.y
            else:
                self.objetivo_actual = None # Limpiar objetivo si ha muerto o desaparecido

            # --- Lógica de movimiento inteligente ---
            # Prioridad 0: Huir si hay un depredador cerca (para presas)
            if dx == 0 and dy == 0 and isinstance(self, (Herbivoro, Omnivoro)):
                dx, dy = self._buscar_amenaza(ecosistema)


            # Prioridad 1: Beber si tiene mucha sed
            if self._sed > UMBRAL_SED_BEBER:
                rio_cercano = ecosistema.encontrar_rio_cercano(self.x, self.y, self.rango_vision)
                if rio_cercano:
                    self.memoria["ultimo_rio_visto"] = rio_cercano.rect.center # Guardar en memoria
                    # Moverse hacia el borde del río
                    punto_cercano = min(
                        [(rio_cercano.rect.left, self.y), (rio_cercano.rect.right, self.y), (self.x, rio_cercano.rect.top), (self.x, rio_cercano.rect.bottom)],
                        key=lambda p: self._distancia_a(p[0], p[1])
                    )
                    dx = punto_cercano[0] - self.x
                    dy = punto_cercano[1] - self.y
                # Si no ve un río pero recuerda uno, va hacia él
                elif self.memoria["ultimo_rio_visto"]:
                    dx = self.memoria["ultimo_rio_visto"][0] - self.x
                    dy = self.memoria["ultimo_rio_visto"][1] - self.y

            # Prioridad 1.5: Buscar refugio si la energía es baja
            if dx == 0 and dy == 0 and self._energia < 40:
                santuario_cercano = ecosistema.encontrar_santuario_cercano(self.x, self.y, self.rango_vision)
                if santuario_cercano:
                    dx = santuario_cercano.rect.centerx - self.x
                    dy = santuario_cercano.rect.centery - self.y

            # Prioridad 2: Buscar comida si tiene hambre (lógica específica en subclases)
            if dx == 0 and dy == 0:
                dx, dy = self._buscar_comida(ecosistema)
            
            # Prioridad 3: Buscar manada si no hay otra necesidad urgente (solo para herbívoros)
            if dx == 0 and dy == 0 and isinstance(self, Herbivoro):
                dx, dy = self._buscar_manada(ecosistema)

            # Prioridad 4: Patrullar territorio (carnívoros) o moverse aleatoriamente
            if dx == 0 and dy == 0:
                if isinstance(self, Carnivoro) and self._distancia_a(*self.territorio_centro) > 150:
                    # Si está muy lejos de su territorio, tiende a volver
                    dx = self.territorio_centro[0] - self.x
                    dy = self.territorio_centro[1] - self.y
                else:
                    # Movimiento aleatorio normal
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
        if self._esta_vivo and (self._energia <= 0 or self._sed >= 150 or self._edad > 35): # Muerte por vejez
            self._esta_vivo = False
            # Al morir, deja una carcasa
            ecosistema.agregar_carcasa(self.x, self.y) # Corregido: 'ecosistema' ahora está definido
            return f" -> ¡{self._nombre} ha muerto!"
        return ""

    def reproducirse(self, ecosistema) -> str:
        """Intenta reproducirse si tiene suficiente energía y edad. Devuelve un log."""
        if not (self._esta_vivo and self._energia > ENERGIA_REPRODUCCION and self._edad > EDAD_ADULTA):
            return ""

        # Buscar una pareja cercana que también cumpla los requisitos
        pareja = ecosistema.encontrar_pareja_cercana(self)
        if pareja:
            probabilidad = PROBABILIDAD_REPRODUCCION
            if ecosistema.esta_en_santuario(self.x, self.y):
                probabilidad *= 2 # Bonus del santuario

            if random.random() < probabilidad:
                # Ambos padres gastan energía
                self._energia -= 40
                pareja._energia -= 40

                # --- Lógica de Herencia Genética Sexual ---
                nuevos_genes = {
                    'max_energia': random.choice([self.genes['max_energia'], pareja.genes['max_energia']]),
                    'rango_vision': random.choice([self.genes['rango_vision'], pareja.genes['rango_vision']])
                }
                # Añadir mutación
                if random.random() < 0.1: # 10% de probabilidad de mutación
                    nuevos_genes['max_energia'] += random.randint(-5, 5)
                    nuevos_genes['rango_vision'] += random.randint(-10, 10)

                # Crear una cría del mismo tipo
                tipo_animal = type(self)
                nombre_cria = f"{tipo_animal.__name__.rstrip('o')} {getattr(tipo_animal, 'contador', 0) + 1}"
                # La cría hereda el rasgo nocturno/diurno
                cria = tipo_animal(nombre_cria, self.x, self.y, genes=nuevos_genes, es_nocturno=self.es_nocturno)
                if isinstance(cria, (Leopardo, Raton)): # Asegurarse de que las clases nocturnas lo sean
                    cria.es_nocturno = True
                cria = tipo_animal(nombre_cria, self.x, self.y, genes=nuevos_genes)
                ecosistema.animales_nuevos.append(cria) # Añadir a una lista temporal
                return f"¡{self._nombre} y {pareja.nombre} se han reproducido! Nace {nombre_cria}."
        return ""

    def _buscar_manada(self, ecosistema):
        """Intenta moverse hacia el centro de la manada local."""
        companeros = []
        for otro_animal in ecosistema.animales:
            if otro_animal is not self and type(otro_animal) is type(self) and self._distancia_a(otro_animal.x, otro_animal.y) < DISTANCIA_MANADA:
                companeros.append(otro_animal)
        
        if len(companeros) > 0:
            # Calcular el centro de masa de los compañeros
            avg_x = sum(a.x for a in companeros) / len(companeros)
            avg_y = sum(a.y for a in companeros) / len(companeros)

            # Evitar agruparse demasiado (separación)
            if self._distancia_a(avg_x, avg_y) < 20:
                return 0, 0 # Ya está lo suficientemente cerca

            # Moverse hacia el centro (cohesión)
            return avg_x - self.x, avg_y - self.y
        return 0, 0 # No hay manada cerca, movimiento aleatorio

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
            dest_x = mejor_celda[0] * CELL_SIZE + CELL_SIZE // 2
            dest_y = mejor_celda[1] * CELL_SIZE + CELL_SIZE // 2
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
        # Los herbívoros no se reproducen si no cumplen las condiciones básicas.
        if not (self._esta_vivo and self._energia > ENERGIA_REPRODUCCION and self._edad > EDAD_ADULTA):
            return ""

        # Buscar una pareja cercana que también cumpla los requisitos
        pareja = ecosistema.encontrar_pareja_cercana(self)
        if pareja:
            # Usamos la probabilidad base y la aumentamos para los herbívoros.
            probabilidad = PROBABILIDAD_REPRODUCCION * 1.5 # 50% más de probabilidad
            if ecosistema.esta_en_santuario(self.x, self.y):
                probabilidad *= 2 # Bonus del santuario

            if random.random() < probabilidad:
                # Si la reproducción es exitosa, llamamos al método del padre para ejecutar la lógica.
                # Pasamos la pareja para evitar que la busque de nuevo.
                return super().reproducirse(ecosistema)
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
        if self.objetivo_actual and isinstance(self.objetivo_actual, (Herbivoro, Omnivoro)) and self._distancia_a(self.objetivo_actual.x, self.objetivo_actual.y) < 15:
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
        if ecosistema.esta_cerca_de_rio(self.x, self.y):
            if ecosistema.comer_peces(self):
                self._energia += ENERGIA_PEZ
                self._energia = min(self._energia, self.genes['max_energia'])
                return f"{self._nombre} (Carnívoro) ha pescado un pez. Energía: {self._energia}"

        # La penalización por no encontrar comida se aplica solo si no hay objetivo.
        # Esto se gestiona ahora en _buscar_comida.
        # Si llega aquí, significa que no tenía nada al alcance para comer en este turno.
        return f"{self._nombre} (Carnívoro) está buscando comida."


    def _buscar_comida(self, ecosistema):
        """Busca la presa más cercana y se mueve hacia ella."""
        # Si ya está cazando, no busca nueva presa
        if not self.objetivo_actual:
            presa_cercana = ecosistema.encontrar_presa_cercana(self)
            if presa_cercana:
                self.objetivo_actual = presa_cercana # Fija la presa como objetivo
                # El movimiento se gestionará en el bucle principal de moverse()
                return presa_cercana.x - self.x, presa_cercana.y - self.y
        
        # Si no ve presas, usa el "olfato" para moverse en la dirección general de la presa más cercana
        presa_lejana = ecosistema.encontrar_presa_mas_cercana_global(self)
        if presa_lejana:
            dx = presa_lejana.x - self.x
            dy = presa_lejana.y - self.y
            return dx, dy

        # Si no hay presas en absoluto, busca carroña
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

        # Decisión más inteligente: ¿qué está más cerca, bayas o presas?
        presa_cercana = ecosistema.encontrar_presa_cercana(self)
        selva_cercana = ecosistema.encontrar_selva_cercana(self.x, self.y, self.rango_vision)

        dist_presa = self._distancia_a(presa_cercana.x, presa_cercana.y) if presa_cercana else float('inf')
        dist_selva = ecosistema._distancia_a_rect(self.x, self.y, selva_cercana.rect) if selva_cercana else float('inf')

        # Opción 1: Cazar si la presa está más cerca (o no hay selvas) y hay presa.
        if self.objetivo_actual and isinstance(self.objetivo_actual, (Herbivoro, Omnivoro)) and self._distancia_a(self.objetivo_actual.x, self.objetivo_actual.y) < 15:
            presa_atrapada = self.objetivo_actual
            self._energia += ENERGIA_CAZA
            self._energia = min(self._energia, self.genes['max_energia'])
            presa_atrapada._energia = 0
            self.objetivo_actual = None # Limpiar objetivo
            log_muerte = presa_atrapada.verificar_estado(ecosistema)
            return f"{self._nombre} (Omnívoro) ha cazado a {presa_atrapada.nombre}." + log_muerte

        # Opción 2: Comer carroña si está más cerca que las bayas
        carcasa_cercana = ecosistema.encontrar_carcasa_cercana(self.x, self.y, self.rango_vision)
        dist_carcasa = self._distancia_a(carcasa_cercana.x, carcasa_cercana.y) if carcasa_cercana else float('inf')

        if carcasa_cercana and dist_carcasa < dist_selva:
            if ecosistema.comer_carcasa(self):
                self._energia += 20 # Ganan un poco menos que los carnívoros de la carroña
                return f"{self._nombre} (Omnívoro) ha comido carroña. Energía: {self._energia}"

        # Opción 3: Comer bayas si está en una selva.
        log_bayas = self._intentar_comer_bayas(ecosistema)
        if "ha comido bayas" in log_bayas:
            return log_bayas

        # Última opción: Pescar si está cerca de un río
        if ecosistema.esta_cerca_de_rio(self.x, self.y) and ecosistema.comer_peces(self):
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
        presa_cercana = ecosistema.encontrar_presa_cercana(self)

        dist_selva = ecosistema._distancia_a_rect(self.x, self.y, selva_cercana.rect) if selva_cercana else float('inf')
        dist_presa = self._distancia_a(presa_cercana.x, presa_cercana.y) if presa_cercana else float('inf')

        if selva_cercana:
            self.memoria["ultima_comida_vista"] = selva_cercana.rect.center
            dx = selva_cercana.rect.centerx - self.x
            dy = selva_cercana.rect.centery - self.y
            return dx, dy
        
        # Si no ve una selva pero recuerda una, va hacia ella
        elif self.memoria["ultima_comida_vista"]:
            dx = self.memoria["ultima_comida_vista"][0] - self.x
            dy = self.memoria["ultima_comida_vista"][1] - self.y
            return dx, dy
            
        # Olfato para presas si no hay selvas cerca
        presa_lejana = ecosistema.encontrar_presa_mas_cercana_global(self)
        if presa_lejana:
            dx = presa_lejana.x - self.x
            dy = presa_lejana.y - self.y
            return dx, dy

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
    def __init__(self, nombre: str, x: int, y: int, edad: int = 0, energia: int = 100, genes=None, es_nocturno=True):
        super().__init__(nombre, x, y, edad, energia, genes, es_nocturno)

class Leopardo(Carnivoro):
    """Un carnívoro específico."""
    def __init__(self, nombre: str, x: int, y: int, edad: int = 0, energia: int = 100, genes=None, es_nocturno=True):
        super().__init__(nombre, x, y, edad, energia, genes, es_nocturno)


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
        self.bayas = 25

    def crecer_recursos(self, factor_crecimiento):
        self.bayas += int(2 * factor_crecimiento)

class Ecosistema:
    """Gestiona el estado del entorno y los animales."""
    def __init__(self):
        self.animales: list[Animal] = []
        self.terreno = {
            "montanas": [
                Montana((50, 50, 100, 150)),      # Existente
                Montana((600, 400, 150, 120)),    # Existente
                Montana((700, 20, 80, 250)),      # Nueva cordillera vertical
                Montana((250, 200, 200, 50))      # Nueva montaña horizontal
            ],
            "praderas": [
                Pradera((20, 400, 150, 150)),     # Existente
                Pradera((300, 50, 250, 100))      # Nueva pradera grande en el norte
            ],
            "rios": [
                Rio((0, 300, 500, 40)),           # Existente
                Rio((460, 100, 40, 240)),         # Existente
                Rio((650, 600, 150, 30)),         # Existente
                Rio((0, 650, 400, 30))            # Nuevo río en el sur
            ],
            "selvas": [
                Selva((200, 450, 250, 180)),      # Existente
                Selva((20, 20, 100, 100)),        # Existente
                Selva((500, 250, 150, 100))       # Nueva selva en el centro-este
            ],
            "santuarios": [
                Santuario((550, 50, 200, 200)),   # Existente
                Santuario((20, 560, 180, 120))    # Existente
            ],
        }
        # --- Nuevo sistema de recursos ---
        self.recursos = {
            "carcasas": []
        }
        self.grid_width = SIM_WIDTH // CELL_SIZE
        self.grid_height = SCREEN_HEIGHT // CELL_SIZE
        self.grid_hierba = [[0 for _ in range(self.grid_height)] for _ in range(self.grid_width)]
        # Inicializar la hierba
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

    def encontrar_pareja_cercana(self, animal_buscando):
        """Encuentra una pareja compatible para la reproducción."""
        for animal in self.animales:
            if (animal is not animal_buscando and
                type(animal) is type(animal_buscando) and
                animal.esta_vivo and
                animal.edad > EDAD_ADULTA and
                animal.energia > ENERGIA_REPRODUCCION and
                animal_buscando._distancia_a(animal.x, animal.y) < 50): # Deben estar cerca
                return animal
        return None

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

    def encontrar_mejor_pasto_cercano(self, x, y, rango):
        """Encuentra la celda con más hierba dentro del rango de visión de un animal."""
        grid_x, grid_y = int(x // CELL_SIZE), int(y // CELL_SIZE)
        radio_busqueda = int(rango // CELL_SIZE)
        
        mejor_celda = None
        max_hierba = 0

        for gx in range(max(0, grid_x - radio_busqueda), min(self.grid_width, grid_x + radio_busqueda)):
            for gy in range(max(0, grid_y - radio_busqueda), min(self.grid_height, grid_y + radio_busqueda)):
                # No buscar comida en terreno infranqueable
                if not self.choca_con_terreno(gx * CELL_SIZE, gy * CELL_SIZE):
                    if self.grid_hierba[gx][gy] > max_hierba:
                        max_hierba = self.grid_hierba[gx][gy]
                        mejor_celda = (gx, gy)
        
        return mejor_celda

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

    def comer_peces(self, animal):
        """Permite a un animal pescar si está cerca de un río con peces."""
        distancia_captura = 25  # Distancia a la que un animal puede atrapar un pez
        pez_cercano = None
        dist_min = float('inf')

        for rio in self.terreno["rios"]:
            for pez in rio.peces:
                dist = animal._distancia_a(pez.x, pez.y)
                if dist < dist_min:
                    dist_min = dist
                    pez_cercano = pez
        
        if pez_cercano and dist_min < distancia_captura:
            pez_cercano.rio.peces.remove(pez_cercano) # El pez es atrapado y eliminado
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
                    "nombre": a.nombre, "x": a.x, "y": a.y, "edad": a.edad,
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
        tipos = {"Herbivoro": Herbivoro, "Carnivoro": Carnivoro, "Omnivoro": Omnivoro, "Conejo": Conejo, "Raton": Raton, "Cabra": Cabra, "Leopardo": Leopardo, "Gato": Gato, "Cerdo": Cerdo, "Mono": Mono}
        for a_data in estado["animales"]:
            tipo_clase = tipos.get(a_data["tipo"])
            es_nocturno = a_data.get("es_nocturno", False)
            # Para compatibilidad con guardados antiguos
            if tipo_clase in [Leopardo, Raton]: # Raton y Leopardo son nocturnos por defecto
                es_nocturno = True
            if tipo_clase:
                animal = tipo_clase(a_data["nombre"], a_data["x"], a_data["y"], a_data["edad"], a_data["energia"], genes=a_data.get("genes"), es_nocturno=es_nocturno)
                # Restaurar sed si está en los datos guardados
                animal._sed = a_data.get("sed", 0)
                self.animales.append(animal)