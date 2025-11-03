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
BORDE_MARGEN = 20 # Margen de seguridad para que los animales no se acerquen a los bordes
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
            
        # Cambiar de dirección ocasionalmente
        if random.random() < 0.05:
            self.direccion += random.uniform(-0.3, 0.3)

        # Calcular nuevo movimiento (no es necesario traducir nombres de variables)
        nuevo_x = self.x + math.cos(self.direccion) * self.velocidad
        nuevo_y = self.y + math.sin(self.direccion) * self.velocidad

        # Mantener al pez dentro del río
        if self.rio:
            rect = self.rio.rect
            nuevo_x = max(rect.left + 5, min(rect.right - 5, nuevo_x))
            nuevo_y = max(rect.top + 5, min(rect.bottom - 5, nuevo_y))
            
            # Rebotar en los bordes del río
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
        
        # Eliminar peces que fueron comidos
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
        # Usar flotantes para una posición más precisa, pero mantener propiedades 'x' e 'y' como enteros para compatibilidad
        self._x_float = float(x)
        self._y_float = float(y)
        self._edad = max(0, edad)
        self._sed = 0
        if max_energia is None:
            max_energia = max(80, min(120, 100 + random.randint(-10, 10)))
        self.max_energia = max_energia
        self._energia = max(0, min(energia, self.max_energia))
        self._esta_vivo = True
        self.estado = "deambulando" # Estados: deambulando, buscando_comida, buscando_agua, cazando, huyendo
        self.objetivo = None  # Puede ser una tupla (x,y) o un objeto Animal
        
        type(self).contador = getattr(type(self), 'contador', 0) + 1

    @property
    def nombre(self):
        return self._nombre

    @property
    def x(self):
        return int(self._x_float)

    @property
    def y(self):
        return int(self._y_float)

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

    def _validar_objetivo_coordenadas(self, x, y):
        """Asegura que un objetivo de coordenadas esté dentro del margen de seguridad."""
        valid_x = max(BORDE_MARGEN, min(x, SIM_WIDTH - 1 - BORDE_MARGEN))
        valid_y = max(BORDE_MARGEN, min(y, SCREEN_HEIGHT - 1 - BORDE_MARGEN))
        return (valid_x, valid_y)

    def _decidir_proximo_paso(self, ecosistema: 'Ecosistema'):
        """Evalúa las necesidades y establece el estado y el objetivo."""
        # Lógica de "pegajosidad" (stickiness) para evitar que el animal cambie de opinión constantemente.
        # Si ya está buscando algo, que continúe hasta satisfacer su necesidad.
        if self.estado == "buscando_agua" and self._sed > 30:
            # Si el objetivo es inválido, buscar uno nuevo, pero seguir buscando agua.
            if self.objetivo is None: self.estado = "deambulando" # Forzar re-evaluación
            else: return # Seguir buscando agua
        if self.estado in ["buscando_comida", "cazando"] and self.energia < self.max_energia * 0.9:
            if self.objetivo is None or (isinstance(self.objetivo, Animal) and not self.objetivo.esta_vivo):
                self.estado = "deambulando" # Forzar re-evaluación
            else:
                return # Seguir buscando comida/cazando
        # Si está huyendo pero ya no hay peligro, que re-evalúe.
        if self.estado == "huyendo":
            depredador = self._encontrar_depredador_cercano(ecosistema)
            if not depredador:
                self.estado = "deambulando" # El peligro pasó, buscar otra cosa que hacer


        # Prioridad 0: Huir si hay un depredador cerca (para presas)
        if isinstance(self, (Herbivoro, Omnivoro)):
            depredador_cercano = self._encontrar_depredador_cercano(ecosistema)
            if depredador_cercano:
                self.estado = "huyendo"
                # Calcular vector de huida (opuesto al depredador)
                dx = self._x_float - depredador_cercano.x
                dy = self._y_float - depredador_cercano.y
                magnitud = math.sqrt(dx*dx + dy*dy) if math.sqrt(dx*dx + dy*dy) > 0 else 1
                # Proyectar un punto de huida a 100 unidades de distancia
                target_x_propuesto = self._x_float + (dx / magnitud) * 100
                target_y_propuesto = self._y_float + (dy / magnitud) * 100
                # Asegurarse de que el objetivo de huida esté dentro de los límites
                self.objetivo = self._validar_objetivo_coordenadas(target_x_propuesto, target_y_propuesto)
                return

        # Prioridad 1: Beber si tiene mucha sed
        if self._sed > 80:
            rio_cercano = self._encontrar_rio_cercano(ecosistema)
            if rio_cercano:
                self.estado = "buscando_agua"
                # Moverse a un punto aleatorio en el borde del río
                target_x = random.randint(rio_cercano.rect.left, rio_cercano.rect.right)
                target_y = random.randint(rio_cercano.rect.top, rio_cercano.rect.bottom)
                self.objetivo = self._validar_objetivo_coordenadas(target_x, target_y)
                return

        # Prioridad 2: Comer si tiene hambre
        if self.energia < self.max_energia * 0.7:
            if isinstance(self, Herbivoro):
                objetivo_comida = self._encontrar_hierba_cercana(ecosistema)
                if objetivo_comida:
                    self.estado = "buscando_comida"
                    self.objetivo = self._validar_objetivo_coordenadas(objetivo_comida[0], objetivo_comida[1])
                    return
            elif isinstance(self, (Carnivoro, Omnivoro)):
                # Lógica de decisión para carnívoros y omnívoros
                presa, dist_presa_sq = self._encontrar_presa_cercana(ecosistema)
                
                objetivo_final = None
                estado_final = "deambulando"

                if isinstance(self, Omnivoro):
                    selva, dist_selva_sq = self._encontrar_selva_cercana(ecosistema) # dist_selva_sq puede ser inf

                    # Dar una ligera preferencia a las bayas si están relativamente cerca,
                    # ya que son una fuente de comida más segura que la caza.
                    # Comparamos si la distancia a la selva es menor que el 80% de la distancia a la presa.
                    if selva and (not presa or dist_selva_sq < dist_presa_sq * 0.8):
                        target_x = random.randint(selva.rect.left, selva.rect.right)
                        target_y = random.randint(selva.rect.top, selva.rect.bottom)
                        objetivo_final = self._validar_objetivo_coordenadas(target_x, target_y)
                        estado_final = "buscando_comida"
                    elif presa:
                        objetivo_final = presa
                        estado_final = "cazando"

                else: # Si es Carnivoro puro
                    if presa:
                        objetivo_final = presa
                        estado_final = "cazando"

                if objetivo_final:
                    self.objetivo = objetivo_final
                    self.estado = estado_final
                    return

        # Si no hay necesidades urgentes, deambular
        self.estado = "deambulando"
        # --- Lógica de Deambulación Segura (Evita atascos en bordes) ---
        # El objetivo se genera directamente dentro de los límites seguros.
        rango_movimiento = 150
        min_x = max(BORDE_MARGEN, self._x_float - rango_movimiento)
        max_x = min(SIM_WIDTH - 1 - BORDE_MARGEN, self._x_float + rango_movimiento)
        min_y = max(BORDE_MARGEN, self._y_float - rango_movimiento)
        max_y = min(SCREEN_HEIGHT - 1 - BORDE_MARGEN, self._y_float + rango_movimiento)

        self.objetivo = (random.uniform(min_x, max_x), random.uniform(min_y, max_y))

    def moverse(self, ecosistema: 'Ecosistema') -> str:
        # Si no hay objetivo o el objetivo actual ya no es válido, encontrar uno nuevo.
        if self.objetivo is None or (self.estado == "cazando" and not self.objetivo.esta_vivo):
            self._decidir_proximo_paso(ecosistema)

        # Si sigue sin haber objetivo, no hacer nada.
        if self.objetivo is None:
            return ""

        # Determinar las coordenadas del objetivo
        if self.estado == "cazando" and isinstance(self.objetivo, Animal):
            # El objetivo es un animal, se mueve.
            if not self.objetivo.esta_vivo: # Si la presa murió mientras la perseguía
                self.objetivo = None
                return "" # Re-evaluar en el siguiente ciclo
            target_x, target_y = self.objetivo.x, self.objetivo.y
        else:
            # El objetivo es una coordenada estática (comida, agua, punto de paseo).
            if not isinstance(self.objetivo, tuple): # Si el objetivo no es una tupla (p.ej. un animal muerto)
                self.objetivo = None
                return ""
            target_x, target_y = self.objetivo

        # Moverse hacia el objetivo
        dx = target_x - self._x_float
        dy = target_y - self._y_float
        distancia_al_objetivo = math.sqrt(dx*dx + dy*dy)

        # Lógica de llegada al objetivo
        if distancia_al_objetivo < 15: # Umbral de llegada
            if self.estado == "buscando_agua":
                self.beber(ecosistema)
            elif self.estado == "buscando_comida" or self.estado == "cazando":
                self.comer(ecosistema)

            # Si después de la acción la necesidad está satisfecha, o si estaba deambulando, buscar nuevo objetivo.
            if self.estado in ["deambulando", "huyendo"] or (self.estado == "buscando_agua" and self._sed < 50) or (self.estado == "buscando_comida" and self.energia > self.max_energia * 0.8):
                self.objetivo = None # Forzar re-evaluación en el siguiente ciclo

            # Caso especial para herbívoros: si hay comida, quedarse. Si no, buscar más.
            if isinstance(self, Herbivoro) and self.estado == "buscando_comida":
                grid_x, grid_y = int(self.x // CELL_SIZE), int(self.y // CELL_SIZE)
                # Si la hierba se agotó o el animal está saciado, buscar un nuevo objetivo general.
                if ecosistema.grid_hierba[grid_x][grid_y] <= 5 or self.energia > self.max_energia * 0.9:
                    self.objetivo = None # Buscar nueva zona de pasto
                else:
                    # Si sigue habiendo hierba y tiene hambre, "pastorear" en la misma celda.
                    # Generar un nuevo micro-objetivo dentro de la celda actual para seguir comiendo.
                    nuevo_x = grid_x * CELL_SIZE + random.randint(0, CELL_SIZE)
                    nuevo_y = grid_y * CELL_SIZE + random.randint(0, CELL_SIZE)
                    self.objetivo = self._validar_objetivo_coordenadas(nuevo_x, nuevo_y)

            return "" # Movimiento completado por ahora

        # Normalizar el vector de movimiento para mantener una velocidad constante
        magnitud = math.sqrt(dx*dx + dy*dy)
        if magnitud > 0:
            velocidad = 1.8 if self.estado == "huyendo" else 1.5 # Huir más rápido
            dx_norm = (dx / magnitud) * velocidad
            dy_norm = (dy / magnitud) * velocidad

            nuevo_x = max(float(BORDE_MARGEN), min(self._x_float + dx_norm, float(SIM_WIDTH - 1 - BORDE_MARGEN)))
            nuevo_y = max(float(BORDE_MARGEN), min(self._y_float + dy_norm, float(SCREEN_HEIGHT - 1 - BORDE_MARGEN)))

            # Solo aplicar coste si hay movimiento real
            if abs(nuevo_x - self._x_float) > 0.001 or abs(nuevo_y - self._y_float) > 0.001:
                self._x_float = nuevo_x
                self._y_float = nuevo_y
                coste_movimiento = 0.15 + ecosistema.estaciones[ecosistema.estacion_actual]['coste_energia'] * 0.2
                self._energia -= coste_movimiento
                self._sed += 0.15
        # Se ha eliminado el sistema anti-atascos "push". La nueva lógica de generación de objetivos lo hace innecesario.
        return ""

    def _encontrar_hierba_cercana(self, ecosistema):
        grid_x = int(self.x // CELL_SIZE)
        grid_y = int(self.y // CELL_SIZE)
        mejor_pos = None
        mejor_valor = 0
        
        # Buscar en un radio de 7 celdas alrededor del animal
        for dx in range(-7, 8):
            for dy in range(-7, 8):
                gx, gy = grid_x + dx, grid_y + dy
                if (0 <= gx < ecosistema.grid_width and
                    0 <= gy < ecosistema.grid_height and 
                    ecosistema.grid_hierba[gx][gy] > mejor_valor):
                    mejor_valor = ecosistema.grid_hierba[gx][gy]
                    # Moverse a un punto aleatorio dentro de la celda, no al centro
                    mejor_pos = self._validar_objetivo_coordenadas(gx * CELL_SIZE + random.randint(0, CELL_SIZE), gy * CELL_SIZE + random.randint(0, CELL_SIZE))
        return mejor_pos

    def _encontrar_presa_cercana(self, ecosistema):
        presas_cercanas = ecosistema.obtener_animales_cercanos(self.x, self.y, 7) # Aumentar radio de búsqueda
        mejor_presa, menor_dist_sq = None, float('inf')
        
        # La lógica de si se puede cazar (tamaño, tipo) se mueve a _puede_cazar
        for presa in presas_cercanas:
            # La comprobación de si la presa es válida se hace ahora aquí
            # para que el animal no persiga presas que no puede cazar.
            # NUEVO: No considerar presas que ya están siendo cazadas por otro animal.
            if presa.estado == "huyendo":
                continue
            if self._puede_cazar(presa):
                # Usar distancia al cuadrado para evitar el costoso cálculo de la raíz cuadrada
                dist_sq = (self.x - presa.x)**2 + (self.y - presa.y)**2
                if dist_sq < menor_dist_sq:
                    menor_dist_sq = dist_sq
                    mejor_presa = presa
        # Devolvemos la presa y la distancia al cuadrado para evitar recalcularla
        return mejor_presa, menor_dist_sq

    def _encontrar_depredador_cercano(self, ecosistema):
        """Busca depredadores cercanos que puedan cazar a este animal."""
        animales_cercanos = ecosistema.obtener_animales_cercanos(self.x, self.y, 6) # Radio de detección de 6 celdas
        for posible_depredador in animales_cercanos:
            # Comprobar si el animal cercano es un depredador y si puede cazar a 'self'
            if isinstance(posible_depredador, (Carnivoro, Omnivoro)):
                # Si el depredador está huyendo, no es una amenaza inmediata
                if posible_depredador.estado == "huyendo":
                    continue
                # Usamos el método _puede_cazar del depredador para ver si somos una presa válida para él
                if posible_depredador._puede_cazar(self):
                    # ¡Peligro!
                    return posible_depredador
        return None

    def _encontrar_rio_cercano(self, ecosistema):
        # --- OPTIMIZACIÓN: Usar la caché de terreno pre-calculada ---
        grid_x, grid_y = int(self.x // CELL_SIZE), int(self.y // CELL_SIZE)
        if (grid_x, grid_y) in ecosistema.terrain_cache["rio"]:
            return ecosistema.terrain_cache["rio"][(grid_x, grid_y)]
        return None

    def _encontrar_selva_cercana(self, ecosistema):
        mejor_selva = None
        menor_dist_sq = float('inf')
        for selva in ecosistema.terreno["selvas"]:
            if selva.bayas > 10: # Solo considerar selvas con suficientes bayas
                dist_sq = (self.x - selva.rect.centerx)**2 + (self.y - selva.rect.centery)**2
                if dist_sq < menor_dist_sq:
                    menor_dist_sq = dist_sq
                    mejor_selva = selva
        # --- OPTIMIZACIÓN: Usar la caché de terreno pre-calculada ---
        grid_x, grid_y = int(self.x // CELL_SIZE), int(self.y // CELL_SIZE)
        if (grid_x, grid_y) in ecosistema.terrain_cache["selva"]:
            selva_cercana, dist_sq = ecosistema.terrain_cache["selva"][(grid_x, grid_y)]
            if selva_cercana.bayas > 10: return selva_cercana, dist_sq
        return None, float('inf')

    def envejecer(self, ecosistema: 'Ecosistema') -> str:
        self._edad += 1
        # Coste diario por envejecer. Se eliminó una resta duplicada que causaba muertes rápidas.
        self._energia -= 0.5
        return self.verificar_estado(ecosistema)

    def verificar_estado(self, ecosistema: 'Ecosistema') -> str:
        if self._esta_vivo and (
            self._energia <= 0 or 
            self._sed >= 150 or  # Límite de sed para morir
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
        prob_base = 0.025 # Probabilidad base de reproducción (2.5%)

        # --- Lógica de Capacidad de Carga para evitar sobrepoblación ---
        if isinstance(self, Herbivoro):
            limite_poblacion = 80
            conteo_actual = sum(1 for a in ecosistema.animales if isinstance(a, Herbivoro))
        elif isinstance(self, Carnivoro):
            limite_poblacion = 40
            conteo_actual = sum(1 for a in ecosistema.animales if isinstance(a, Carnivoro))
        else: # Omnivoro
            limite_poblacion = 50
            conteo_actual = sum(1 for a in ecosistema.animales if isinstance(a, Omnivoro))

        # Si la población actual supera el 70% del límite, la probabilidad de reproducción disminuye.
        if conteo_actual > limite_poblacion * 0.7:
            prob_base *= (limite_poblacion - conteo_actual) / (limite_poblacion * 0.3) # Reducción lineal

        if (self.edad > 45 and self.energia > self.max_energia * 0.85 and random.random() < prob_base):
            # Crear una cría del mismo tipo
            cría = type(self)(f"{self.nombre} Jr.", self.x, self.y)
            ecosistema.animales_nuevos.append(cría)
            self._energia -= 35  # Reducir el coste de energía por reproducirse
            return f"{self.nombre} se ha reproducido."
        return ""

    def __str__(self):
        estado = "Vivo" if self._esta_vivo else "Muerto"
        return f"Animal: {self._nombre}, Tipo: {self.__class__.__name__}, Edad: {self._edad}, Energía: {self._energia}, Estado: {estado}"

class Herbivoro(Animal):
    def comer(self, ecosistema) -> str:
        # Los herbívoros comen hierba si están en una celda con hierba
        if self.energia < self.max_energia * 0.9:  # Hacer que coman más frecuentemente
            grid_x = int(self.x // CELL_SIZE)
            grid_y = int(self.y // CELL_SIZE)
            
            # Asegurarse de que las coordenadas están dentro de los límites del mapa
            if 0 <= grid_x < ecosistema.grid_width and 0 <= grid_y < ecosistema.grid_height:
                if ecosistema.grid_hierba[grid_x][grid_y] > 0:
                    comido = min(ecosistema.grid_hierba[grid_x][grid_y], 20)  # Aumentar cantidad que comen
                    self._energia += comido * 4  # Aumentar energía obtenida
                    self._sed -= 5  # Reducir sed al comer hierba
                    self._energia = min(self._energia, self.max_energia)
                    ecosistema.grid_hierba[grid_x][grid_y] -= comido
                    ecosistema.hierba_cambio = True # Notificar que la hierba cambió
                    return f"{self.nombre} comió hierba." # No es necesario devolver mensaje para optimizar
        return ""

    def beber(self, ecosistema: 'Ecosistema') -> str:
        if self._sed > 50:
            # --- OPTIMIZACIÓN: Comprobar si la celda actual es un río usando la caché ---
            grid_x, grid_y = int(self.x // CELL_SIZE), int(self.y // CELL_SIZE)
            if ecosistema.is_river[grid_x][grid_y]:
                self._sed = max(0, self._sed - 75)
                return f"{self.nombre} bebió agua."
        return ""

class Carnivoro(Animal):
    def comer(self, ecosistema) -> str:
        # Los carnívoros intentan comer si están cazando y cerca de su presa.
        if self.estado == "cazando" and isinstance(self.objetivo, Animal) and self.objetivo.esta_vivo:
            presa_objetivo = self.objetivo
            if self._puede_cazar(presa_objetivo):
                dist_sq = (self.x - presa_objetivo.x)**2 + (self.y - presa_objetivo.y)**2
                # Rango de ataque de 15 píxeles (15*15=225)
                if dist_sq < 225:
                    presa_objetivo._esta_vivo = False # La presa muere
                    ecosistema.agregar_carcasa(presa_objetivo.x, presa_objetivo.y)
                    self._energia += 90  # Aumentar energía por caza
                    self._sed -= 10  # Reducir sed al comer presas
                    self._energia = min(self._energia, self.max_energia)
                    self.objetivo = None # Cazó, buscar otra cosa que hacer
                    return f"{self.nombre} cazó a {presa_objetivo.nombre}."
        return ""

    def _puede_cazar(self, presa):
        # Un carnívoro no puede cazar a otro carnívoro.
        es_presa_valida = not isinstance(presa, Carnivoro)
        # No caza presas mucho más grandes que él.
        es_tamano_adecuado = self.max_energia >= presa.max_energia * 0.8
        return (presa is not self and es_presa_valida and es_tamano_adecuado and presa.esta_vivo and self.energia > 30)

    def beber(self, ecosistema: 'Ecosistema') -> str:
        if self._sed > 50:
            # --- OPTIMIZACIÓN: Comprobar si la celda actual es un río usando la caché ---
            grid_x, grid_y = int(self.x // CELL_SIZE), int(self.y // CELL_SIZE)
            if ecosistema.is_river[grid_x][grid_y]:
                self._sed = max(0, self._sed - 75)
                return f"{self.nombre} bebió agua."
        return ""

class Omnivoro(Animal):
    def comer(self, ecosistema) -> str:
        if self.energia < self.max_energia * 0.8:
            # Prioridad 1: Comer bayas si está en una selva.
            for selva in ecosistema.terreno["selvas"]:
                if selva.rect.collidepoint(self.x, self.y) and selva.bayas > 0:
                    energia_ganada = min(30, selva.bayas * 2)  # Aumentar energía de bayas
                    self._energia = min(self.max_energia, self._energia + energia_ganada)
                    selva.bayas = max(0, selva.bayas - 10)
                    self.objetivo = None # Comió, buscar otra cosa que hacer.
                    return f"{self.nombre} comió bayas."

            # Prioridad 2: Cazar si está cerca de una presa.
            if self.estado == "cazando" and isinstance(self.objetivo, Animal) and self.objetivo.esta_vivo:
                presa_objetivo = self.objetivo
                if self._puede_cazar(presa_objetivo):
                    dist_sq = (self.x - presa_objetivo.x)**2 + (self.y - presa_objetivo.y)**2
                    if dist_sq < 144: # Rango de caza de 12 píxeles
                        presa_objetivo._esta_vivo = False
                        ecosistema.agregar_carcasa(presa_objetivo.x, presa_objetivo.y)
                        self._energia = min(self.max_energia, self._energia + 75) # Aumentar energía por caza
                        self.objetivo = None # Cazó, buscar otra cosa que hacer
                        return f"{self.nombre} cazó a {presa_objetivo.nombre}."

        return ""
    
    def _puede_cazar(self, presa):
        # Un omnívoro no puede cazar a otro depredador y no caza presas mucho más grandes que él.
        es_presa_valida = not isinstance(presa, (Carnivoro, Omnivoro))
        # Evitar que un cerdo cace una cabra, por ejemplo. Comparamos max_energia como proxy de tamaño/fuerza.
        es_tamano_adecuado = self.max_energia >= presa.max_energia * 0.9
        return (presa is not self and es_presa_valida and es_tamano_adecuado and presa.esta_vivo and self.energia > 30)

    def beber(self, ecosistema: 'Ecosistema') -> str:
        if self._sed > 50:
            # --- OPTIMIZACIÓN: Comprobar si la celda actual es un río usando la caché ---
            grid_x, grid_y = int(self.x // CELL_SIZE), int(self.y // CELL_SIZE)
            if ecosistema.is_river[grid_x][grid_y]:
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
                Pradera((650, 550, 130, 130))  
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
            "montanas": [],
            "santuarios": [],
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
        # --- OPTIMIZACIÓN: Pre-calcular qué celdas son ríos ---
        self.is_river = [[False for _ in range(self.grid_height)] for _ in range(self.grid_width)]

        for gx in range(self.grid_width):
            for gy in range(self.grid_height):
                cell_rect = pygame.Rect(gx * CELL_SIZE, gy * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                
                if any(rio.rect.colliderect(cell_rect) for rio in self.terreno["rios"]):
                    self.grid_hierba[gx][gy] = 0
                    # Marcar esta celda como río para futuras comprobaciones rápidas
                    self.is_river[gx][gy] = True
                    continue

                max_val = MAX_HIERBA_NORMAL
                if any(p.rect.colliderect(cell_rect) for p in self.terreno["praderas"]):
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
        self.hierba_cambio = False # Flag para optimización de renderizado

        self.grid_animales = {}  # Diccionario para optimizar la búsqueda de animales cercanos

        self._poblar_decoraciones()
        
        # --- OPTIMIZACIÓN: Pre-calcular la caché de terrenos cercanos ---
        self.terrain_cache = {"rio": {}, "selva": {}}
        self._precalcular_terrenos_cercanos()

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

    def _precalcular_terrenos_cercanos(self):
        """
        OPTIMIZACIÓN: Para cada celda del grid, calcula el río y la selva más cercanos.
        Esto evita que cada animal tenga que recalcularlo en cada ciclo.
        """
        print("Pre-calculando caché de terrenos cercanos para optimización...")
        for gx in range(self.grid_width):
            for gy in range(self.grid_height):
                x, y = gx * CELL_SIZE, gy * CELL_SIZE
                
                # Encontrar el río más cercano
                mejor_rio, menor_dist_rio_sq = None, float('inf')
                for rio in self.terreno["rios"]:
                    dist_sq = (x - rio.rect.centerx)**2 + (y - rio.rect.centery)**2
                    if dist_sq < menor_dist_rio_sq:
                        menor_dist_rio_sq, mejor_rio = dist_sq, rio
                if mejor_rio: self.terrain_cache["rio"][(gx, gy)] = mejor_rio

                # Encontrar la selva más cercana
                mejor_selva, menor_dist_selva_sq = None, float('inf')
                for selva in self.terreno["selvas"]:
                    dist_sq = (x - selva.rect.centerx)**2 + (y - selva.rect.centery)**2
                    if dist_sq < menor_dist_selva_sq:
                        menor_dist_selva_sq, mejor_selva = dist_sq, selva
                if mejor_selva: self.terrain_cache["selva"][(gx, gy)] = (mejor_selva, menor_dist_selva_sq)

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
        Si una especie se extingue, hay una baja probabilidad diaria de que
        un pequeño grupo inmigre para evitar un colapso total.
        """
        # No ejecutar si no hay animales en absoluto
        if not self.animales:
            return

        for tipo_animal in self.tipos_de_animales:
            conteo = sum(1 for a in self.animales if isinstance(a, tipo_animal))
            if conteo == 0 and random.random() < 0.10: # 10% de probabilidad de rescate por día
                print(f"¡Inmigración afortunada! Un pequeño grupo de {tipo_animal.__name__} ha llegado.")
                for _ in range(2): # Reintroducir un grupo más pequeño
                    self.agregar_animal(tipo_animal, es_rescate=True)

    def simular_hora(self):
        self._actualizar_grid_animales()

        self.hora_actual += 1

        random.shuffle(self.animales)
        for animal in self.animales:
            if animal.esta_vivo:
                animal.moverse(self) # La lógica de comer y beber ahora está dentro de moverse()

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
                    # --- OPTIMIZACIÓN: Usar la matriz pre-calculada 'is_river' ---
                    if self.is_river[gx][gy]:
                        self.grid_hierba[gx][gy] = 0
                        continue

                    # Por defecto, el crecimiento es normal
                    tasa_crecimiento_base = 1 
                    calidad_suelo_local = 1.0
                    max_capacidad = MAX_HIERBA_NORMAL
                    tasa_crecimiento_base = 1
                    
                    cell_rect = pygame.Rect(gx * CELL_SIZE, gy * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                    pradera_actual = next((p for p in self.terreno["praderas"] if p.rect.colliderect(cell_rect)), None) # colliderect es necesario aquí
                    if pradera_actual: # No es necesario comprobar si choca con el río aquí, ya se hizo arriba
                        max_capacidad = pradera_actual.max_hierba
                        tasa_crecimiento_base = pradera_actual.tasa_crecimiento
                    # El crecimiento ahora depende de la hierba existente (sobrepastoreo)
                    crecimiento_real = int(tasa_crecimiento_base * factor_crecimiento * (self.grid_hierba[gx][gy] / max_capacidad))
                    self.grid_hierba[gx][gy] += crecimiento_real
                    self.grid_hierba[gx][gy] = min(self.grid_hierba[gx][gy], max_capacidad)
            self.hierba_cambio = True # La hierba creció, necesita redibujarse
            
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

    def agregar_animal(self, tipo_animal, nombre=None, es_rescate=False):
        if nombre is None:
            nombre = f"{tipo_animal.__name__} {getattr(tipo_animal, 'contador', 0) + 1}"

        # Si es un rescate, buscar una posición válida en cualquier lugar.
        # Si es añadido por el usuario, puede aparecer en cualquier lugar no-obstáculo.
        intentos = 0
        while intentos < 100:
            x = random.randint(20, SIM_WIDTH - 20)
            y = random.randint(20, SCREEN_HEIGHT - 20)
            if not self.choca_con_terreno(x, y): break
            intentos += 1
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
        
        # --- OPTIMIZACIÓN: Recalcular caché de terreno al cargar ---
        self._precalcular_terrenos_cercanos()

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
                # Corrección: Usar .get() con un valor por defecto para max_energia para evitar errores al cargar partidas antiguas
                max_energia_default = max(80, min(120, 100 + random.randint(-10, 10)))
                animal = tipo_clase(a_data["nombre"], a_data["x"], a_data["y"], 
                                    a_data.get("edad", 0), a_data.get("energia", 100), 
                                    max_energia=a_data.get("max_energia", max_energia_default))
                animal._sed = a_data.get("sed", 0)
                animal.estado = a_data.get("estado", "deambulando")
                self.animales.append(animal)