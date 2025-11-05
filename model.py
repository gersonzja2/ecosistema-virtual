from abc import ABC, abstractmethod
import pygame
import json
import math
import random

SIM_WIDTH = 800
SCREEN_HEIGHT = 700
CELL_SIZE = 20
MAX_HIERBA_NORMAL = 70
BORDE_MARGEN = 20 # Margen de seguridad para que los animales no se acerquen a los bordes
MAX_HIERBA_PRADERA = 120
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

    def actualizar(self):
        """Mueve el pez y lo mantiene dentro de los límites de su río."""
        if self.fue_comido:
            return

        # Mover el pez
        self.x += self.velocidad * math.cos(self.direccion)
        self.y += self.velocidad * math.sin(self.direccion)

        # Rebotar en los bordes del río
        if not self.rio.rect.collidepoint(self.x, self.y):
            self.x = max(self.rio.rect.left, min(self.x, self.rio.rect.right))
            self.y = max(self.rio.rect.top, min(self.y, self.rio.rect.bottom))
            # Cambiar de dirección al chocar
            self.direccion = random.uniform(0, 2 * math.pi)

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
        self.peces = [pez for pez in self.peces if not pez.fue_comido]
        
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

class Animal(ABC):
    contador = 0

    def __init__(self, nombre: str, x: int, y: int, edad: int = 0, energia: int = 100, max_energia=None):
        self._nombre = nombre
        self._x_float = float(x)
        self._y_float = float(y)
        self._edad = max(0, edad)
        self._sed = 0
        if max_energia is None:
            max_energia = max(80, min(120, 100 + random.randint(-10, 10)))
        self.max_energia = max_energia
        self._energia = max(0, min(energia, self.max_energia))
        self.estado = "deambulando"
        self.velocidad = 1.5 + random.uniform(-0.2, 0.2)
        self.target_x = None
        self.target_y = None
        self.tiempo_deambulando = 0
        self.ecosistema = None

        self.edad_reproductiva = 5 # Días
        self.energia_para_reproducir = 60
        self.probabilidad_reproduccion = 0.5 # 50% de probabilidad por hora si las condiciones se dan
        self.cooldown_reproduccion = 0
        
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
        return self._energia > 0

    def __str__(self):
        estado = "Vivo" if self.esta_vivo else "Muerto"
        return f"Animal: {self._nombre}, Tipo: {self.__class__.__name__}, Edad: {self._edad}, Energía: {self._energia}, Estado: {estado}"

    def _obtener_zona_deambulacion(self):
        """Devuelve el rectángulo (x, y, w, h) de la zona de deambulación."""
        center_x = SIM_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2
        thickness = 60
        
        rio_borde_izq = center_x - thickness // 2
        rio_borde_der = center_x + thickness // 2
        rio_borde_sup = center_y - thickness // 2

        if isinstance(self, Carnivoro):
            # Cuadrante superior izquierdo
            return (BORDE_MARGEN, BORDE_MARGEN, rio_borde_izq - BORDE_MARGEN * 2, rio_borde_sup - BORDE_MARGEN * 2)
        elif isinstance(self, Herbivoro):
            # Cuadrante inferior (todo el ancho)
            return (BORDE_MARGEN, rio_borde_sup + thickness, SIM_WIDTH - BORDE_MARGEN * 2, SCREEN_HEIGHT - (rio_borde_sup + thickness) - BORDE_MARGEN)
        elif isinstance(self, Omnivoro):
            # Cuadrante superior derecho
            return (rio_borde_der, BORDE_MARGEN, SIM_WIDTH - rio_borde_der - BORDE_MARGEN, rio_borde_sup - BORDE_MARGEN * 2)
        return (BORDE_MARGEN, BORDE_MARGEN, SIM_WIDTH - 2 * BORDE_MARGEN, SCREEN_HEIGHT - 2 * BORDE_MARGEN)

    def deambular(self):
        """Comportamiento de movimiento errático dentro de una zona."""
        if self.target_x is None or self.tiempo_deambulando <= 0:
            zona_x, zona_y, zona_w, zona_h = self._obtener_zona_deambulacion()
            self.target_x = random.randint(zona_x, zona_x + zona_w)
            self.target_y = random.randint(zona_y, zona_y + zona_h)
            self.tiempo_deambulando = random.randint(50, 150) # Ticks para deambular hacia el objetivo

        dx = self.target_x - self._x_float
        dy = self.target_y - self._y_float
        dist = math.sqrt(dx**2 + dy**2)

        if dist < self.velocidad:
            self._x_float = self.target_x
            self._y_float = self.target_y
            self.target_x = None # Forzar nuevo objetivo
        else:
            self._x_float += (dx / dist) * self.velocidad
            self._y_float += (dy / dist) * self.velocidad

        # Asegurarse de que el animal no se salga de los límites de la simulación
        self._x_float = max(BORDE_MARGEN, min(self._x_float, SIM_WIDTH - BORDE_MARGEN))
        self._y_float = max(BORDE_MARGEN, min(self._y_float, SCREEN_HEIGHT - BORDE_MARGEN))

        self.tiempo_deambulando -= 1

    def _intentar_reproducir(self, ecosistema):
        """Busca una pareja cercana y, si es adecuada, intenta reproducirse."""
        if self.edad < self.edad_reproductiva or self.energia < self.energia_para_reproducir or self.cooldown_reproduccion > 0 or self.estado == "reproduciendose":
            return

        # Buscar pareja adecuada en todo el ecosistema
        parejas_potenciales = []
        for animal in ecosistema.animales:
            if animal is not self and type(animal) is type(self) and \
               animal.edad >= animal.edad_reproductiva and \
               animal.energia >= animal.energia_para_reproducir and \
               animal.cooldown_reproduccion <= 0:
                parejas_potenciales.append(animal)

        if not parejas_potenciales:
            print(f"{self.nombre} no encontró parejas disponibles.")
            return

        # Encontrar la pareja más cercana de las disponibles
        pareja_elegida = min(parejas_potenciales, key=lambda p: math.sqrt((self.x - p.x)**2 + (self.y - p.y)**2))

        # Moverse hacia la pareja
        self.estado = "reproduciendose"
        self.target_x = pareja_elegida.x
        self.target_y = pareja_elegida.y
        print(f"{self.nombre} se dirige a reproducirse con {pareja_elegida.nombre}.")

        # Comprobar si ya está lo suficientemente cerca para reproducirse
        dist_a_pareja = math.sqrt((self.x - pareja_elegida.x)**2 + (self.y - pareja_elegida.y)**2)
        if dist_a_pareja < 15: # Umbral de cercanía para reproducirse
            # La pareja también debe estar lista en este instante
            if (pareja_elegida.edad >= pareja_elegida.edad_reproductiva and pareja_elegida.energia >= pareja_elegida.energia_para_reproducir and pareja_elegida.cooldown_reproduccion <= 0):
                if random.random() < self.probabilidad_reproduccion:
                    print(f"¡Nacimiento! {self.nombre} y {pareja_elegida.nombre} han tenido una cría.")
                    ecosistema.agregar_animal(type(self))
                    self.energia -= 30
                    pareja_elegida.energia -= 30
                    self.cooldown_reproduccion = 120 # Cooldown de 5 días (120 horas)
                    pareja_elegida.cooldown_reproduccion = 120
            self.estado = "deambulando" # Volver a deambular después del intento

    def actualizar(self, ecosistema):
        if not self.esta_vivo:
            return

        if self.ecosistema is None:
            self.ecosistema = ecosistema

        if self.cooldown_reproduccion > 0:
            self.cooldown_reproduccion -= 1

        # Lógica de comportamiento principal
        if self.estado == "deambulando":
            self.deambular()
            # self._intentar_reproducir(ecosistema) # Desactivado para control manual
        elif self.estado == "reproduciendose":
            self.deambular() # Usamos deambular para movernos hacia el target
            self._intentar_reproducir(ecosistema) # Re-evaluar en cada paso

        # Consumo de energía y sed por existir y moverse
        self._energia -= 0.05 # Coste base por hora
        self._energia = max(0, self._energia)
        self._sed += 0.5

        if self._energia <= 0:
            ecosistema.agregar_carcasa(self.x, self.y)

class Herbivoro(Animal):
    pass

class Carnivoro(Animal):
    pass

class Omnivoro(Animal):
    pass

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
            "rios": [],
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
        self.recursos = {
            "carcasas": []
        }
        self.grid_width = SIM_WIDTH // CELL_SIZE
        self.grid_height = SCREEN_HEIGHT // CELL_SIZE
        self.grid_hierba = [[0 for _ in range(self.grid_height)] for _ in range(self.grid_width)]
        self.is_river = [[False for _ in range(self.grid_height)] for _ in range(self.grid_width)]

        # Construir ríos nuevos: pool central + brazos hacia esquinas (aproximación con rects)
        # Parámetros geométricos
        center_x = SIM_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2
        thickness = 60

        # Área central donde confluyen los ríos
        pool = Rio((center_x - thickness // 2, center_y - thickness // 2, thickness, thickness))

        # Brazo izquierdo horizontal: desde el borde izquierdo hasta la izquierda del pool
        left_arm = Rio((0, center_y - thickness // 2, center_x - thickness // 2, thickness))

        # Brazo derecho horizontal: desde la derecha del pool hasta el borde derecho
        right_arm = Rio((center_x + thickness // 2, center_y - thickness // 2, SIM_WIDTH - (center_x + thickness // 2), thickness))

        # Brazo superior vertical: desde el borde superior hasta la parte superior del pool
        top_arm = Rio((center_x - thickness // 2, 0, thickness, center_y - thickness // 2))

        # Añadir a la lista de ríos
        self.terreno["rios"].extend([left_arm, right_arm, top_arm, pool])

        for gx in range(self.grid_width):
            for gy in range(self.grid_height):
                cell_rect = pygame.Rect(gx * CELL_SIZE, gy * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                
                if any(rio.rect.colliderect(cell_rect) for rio in self.terreno["rios"]):
                    self.grid_hierba[gx][gy] = 0
                    self.is_river[gx][gy] = True
                    continue

                max_val = MAX_HIERBA_NORMAL
                if any(p.rect.colliderect(cell_rect) for p in self.terreno["praderas"]):
                    max_val = MAX_HIERBA_PRADERA
                self.grid_hierba[gx][gy] = random.randint(0, max_val)

        self.dia_total = 1
        self.hora_actual = 0
        self.clima_actual = "Normal"
        self.factor_crecimiento_base = 1.5 # Factor de crecimiento constante
        self.animales_nuevos = []
        self.hierba_cambio = False # Flag para optimización de renderizado

        self.grid_animales = {}
        self._poblar_decoraciones()
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
        print("Pre-calculando caché de terrenos cercanos para optimización...")
        for gx in range(self.grid_width):
            for gy in range(self.grid_height):
                x, y = gx * CELL_SIZE, gy * CELL_SIZE
                
                mejor_rio, menor_dist_rio_sq = None, float('inf')
                for rio in self.terreno["rios"]:
                    dist_sq = (x - rio.rect.centerx)**2 + (y - rio.rect.centery)**2
                    if dist_sq < menor_dist_rio_sq:
                        menor_dist_rio_sq, mejor_rio = dist_sq, rio
                if mejor_rio: self.terrain_cache["rio"][(gx, gy)] = mejor_rio

                mejor_selva, menor_dist_selva_sq = None, float('inf')
                for selva in self.terreno["selvas"]:
                    dist_sq = (x - selva.rect.centerx)**2 + (y - selva.rect.centery)**2
                    if dist_sq < menor_dist_selva_sq:
                        menor_dist_selva_sq, mejor_selva = dist_sq, selva
                if mejor_selva: self.terrain_cache["selva"][(gx, gy)] = (mejor_selva, menor_dist_selva_sq)

    def _actualizar_clima(self):
        if random.random() < 0.05:
            self.clima_actual = "Sequía"
        else:
            self.clima_actual = "Normal"

    def _actualizar_grid_animales(self):
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

        if self.hora_actual >= 24:
            self.hora_actual = 0
            self.dia_total += 1
            self._actualizar_clima()

            factor_crecimiento = self.factor_crecimiento_base
            if self.clima_actual == "Sequía":
                factor_crecimiento *= 0.1

            for gx in range(self.grid_width):
                for gy in range(self.grid_height):
                    if self.is_river[gx][gy]:
                        self.grid_hierba[gx][gy] = 0
                        continue

                    tasa_crecimiento_base = 1 
                    calidad_suelo_local = 1.0
                    max_capacidad = MAX_HIERBA_NORMAL
                    tasa_crecimiento_base = 1
                    
                    cell_rect = pygame.Rect(gx * CELL_SIZE, gy * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                    pradera_actual = next((p for p in self.terreno["praderas"] if p.rect.colliderect(cell_rect)), None)
                    if pradera_actual:
                        max_capacidad = pradera_actual.max_hierba
                        tasa_crecimiento_base = pradera_actual.tasa_crecimiento
                    crecimiento_real = int(tasa_crecimiento_base * factor_crecimiento * (1 - self.grid_hierba[gx][gy] / max_capacidad))
                    self.grid_hierba[gx][gy] += crecimiento_real
                    self.grid_hierba[gx][gy] = min(self.grid_hierba[gx][gy], max_capacidad)
            self.hierba_cambio = True # La hierba creció, necesita redibujarse
            
            for selva in self.terreno["selvas"]: selva.crecer_recursos(factor_crecimiento)
            for rio in self.terreno["rios"]: rio.crecer_recursos(factor_crecimiento)

            for c in self.recursos["carcasas"]: c.dias_descomposicion += 1
            self.recursos["carcasas"] = [c for c in self.recursos["carcasas"] if c.dias_descomposicion < 5]

            self.animales_nuevos = []

        self.animales.extend(self.animales_nuevos)
        
        # Actualizar estado de cada animal
        for animal in self.animales:
            animal.actualizar(self)

        # Actualizar peces en cada río
        for rio in self.terreno["rios"]:
            for pez in rio.peces:
                pez.actualizar()
        
    def _obtener_posicion_inicial(self, tipo_animal):
        """Determina la posición inicial para un nuevo animal basado en su tipo."""
        intentos = 0
        center_x = SIM_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2
        thickness = 60
        
        rio_borde_izq = center_x - thickness // 2
        rio_borde_der = center_x + thickness // 2
        rio_borde_sup = center_y - thickness // 2

        while intentos < 100:
            if issubclass(tipo_animal, Carnivoro):
                # Cuadrante superior izquierdo
                x = random.randint(BORDE_MARGEN, rio_borde_izq - BORDE_MARGEN)
                y = random.randint(BORDE_MARGEN, rio_borde_sup - BORDE_MARGEN)
            elif issubclass(tipo_animal, Herbivoro):
                # Cuadrante inferior
                x = random.randint(BORDE_MARGEN, SIM_WIDTH - BORDE_MARGEN)
                y = random.randint(rio_borde_sup + thickness, SCREEN_HEIGHT - BORDE_MARGEN)
            elif issubclass(tipo_animal, Omnivoro):
                # Cuadrante superior derecho
                x = random.randint(rio_borde_der + BORDE_MARGEN, SIM_WIDTH - BORDE_MARGEN)
                y = random.randint(BORDE_MARGEN, rio_borde_sup - BORDE_MARGEN)
            
            if not self.choca_con_terreno(x, y) and not any(rio.rect.collidepoint(x, y) for rio in self.terreno["rios"]):
                return x, y
            intentos += 1
        return random.randint(20, SIM_WIDTH - 20), random.randint(20, SCREEN_HEIGHT - 20) # Fallback

    def agregar_animal(self, tipo_animal, nombre=None, es_rescate=False):
        if nombre is None:
            nombre = f"{tipo_animal.__name__} {getattr(tipo_animal, 'contador', 0) + 1}"
        x, y = self._obtener_posicion_inicial(tipo_animal)
        nuevo_animal = tipo_animal(nombre, x, y)
        nuevo_animal.ecosistema = self # Asignar referencia al ecosistema
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
                max_energia_default = max(80, min(120, 100 + random.randint(-10, 10)))
                animal = tipo_clase(a_data["nombre"], a_data["x"], a_data["y"], 
                                    a_data.get("edad", 0), a_data.get("energia", 100), 
                                    max_energia=a_data.get("max_energia", max_energia_default))
                animal._sed = a_data.get("sed", 0)
                self.animales.append(animal)