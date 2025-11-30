import pygame
import math
import random
from datetime import datetime
from .Terrenos.Terrenos import Rio, Selva, Pradera, Pez, Carcasa
import src.Logica.Terrenos.Terrenos as Terrenos
from .Animales.Animal import Animal, CELL_SIZE, SCREEN_HEIGHT, BORDE_MARGEN, SIM_WIDTH
from .Animales.animales import Conejo, Raton, Cabra, Leopardo, Gato, Cerdo, Mono, Halcon, Insecto, Herbivoro, Carnivoro, Omnivoro


class Ecosistema:
    def __init__(self):
        self.tipos_de_animales = [Conejo, Raton, Cabra, Leopardo, Gato, Cerdo, Mono, Halcon, Insecto]
        self.animales: list[Animal] = []
        
        # Carga y configuración de sonidos
        self.sonido_rio = pygame.mixer.Sound("Sounds/rio 1.wav")
        self.sonido_rio.set_volume(1.5)

        self.terreno = {
            "praderas": [
                Terrenos.Pradera((50, 50, 250, 150)),      # Pradera en la esquina superior izquierda
                Terrenos.Pradera((500, 80, 200, 100)),     # Pradera en la zona superior derecha
                Terrenos.Pradera((50, 450, 250, 200)),     # Gran pradera en la esquina inferior izquierda
                Terrenos.Pradera((550, 480, 200, 150)),    # Pradera en la esquina inferior derecha
            ],
            "rios": [],
            "selvas": [
                Terrenos.Selva((350, 500, 150, 100)),      # Pequeña selva en la parte inferior central
            ],
            "montanas": [],
            "santuarios": [],
            "arboles": [],
            "plantas": [],
            "plantas_2": [],
            "puentes": []
        }
        self.recursos = {
            "carcasas": []
        }
        self.grid_width = SIM_WIDTH // CELL_SIZE
        self.grid_height = SCREEN_HEIGHT // CELL_SIZE
        self.grid_hierba = [[0 for _ in range(self.grid_height)] for _ in range(self.grid_width)]
        self.terrain_grid = [[None for _ in range(self.grid_height)] for _ in range(self.grid_width)]
        self.is_river = [[False for _ in range(self.grid_height)] for _ in range(self.grid_width)]

        # Construir ríos nuevos: pool central + brazos hacia esquinas (aproximación con rects)
        # Parámetros geométricos
        center_x = SIM_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2
        thickness = 60

        # Área central donde confluyen los ríos
        pool = Terrenos.Rio((center_x - thickness // 2, center_y - thickness // 2, thickness, thickness))

        # Brazo izquierdo horizontal: desde el borde izquierdo hasta la izquierda del pool
        left_arm = Terrenos.Rio((0, center_y - thickness // 2, center_x - thickness // 2, thickness))

        # Brazo derecho horizontal: desde la derecha del pool hasta el borde derecho
        right_arm = Terrenos.Rio((center_x + thickness // 2, center_y - thickness // 2, SIM_WIDTH - (center_x + thickness // 2), thickness))

        # Brazo superior vertical: desde el borde superior hasta la parte superior del pool
        top_arm = Terrenos.Rio((center_x - thickness // 2, 0, thickness, center_y - thickness // 2))

        # Añadir a la lista de ríos
        self.terreno["rios"].extend([left_arm, right_arm, top_arm, pool])

        # Añadir puentes en ubicaciones estratégicas sobre los brazos horizontales
        self.terreno["puentes"].append((150, center_y))
        self.terreno["puentes"].append((SIM_WIDTH - 150, center_y))
        self.terreno["puentes"].append((SIM_WIDTH // 4, center_y))
        self.terreno["puentes"].append((center_x + 2, 150)) # Nuevo puente en el río superior, movido 2px a la derecha

        # Establecer la jerarquía de terrenos (el primero tiene más prioridad)
        terrain_hierarchy = [
            ("montanas", "montana"),
            ("santuarios", "santuario"),
            ("selvas", "selva"),
            ("praderas", "pradera")
        ]

        for gx in range(self.grid_width):
            for gy in range(self.grid_height):
                cell_rect = pygame.Rect(gx * CELL_SIZE, gy * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                
                if any(rio.rect.colliderect(cell_rect) for rio in self.terreno["rios"]):
                    self.grid_hierba[gx][gy] = 0
                    self.terrain_grid[gx][gy] = "rio" # Marcar como río
                    self.is_river[gx][gy] = True
                    continue

                # Asignar tipo de terreno basado en la jerarquía
                for terrain_list_name, terrain_type_name in terrain_hierarchy:
                    if any(t.rect.colliderect(cell_rect) for t in self.terreno[terrain_list_name]):
                        self.terrain_grid[gx][gy] = terrain_type_name
                        break
                
                # Calcular hierba inicial
                max_val = Terrenos.MAX_HIERBA_PRADERA if self.terrain_grid[gx][gy] == "pradera" else Terrenos.MAX_HIERBA_NORMAL
                self.grid_hierba[gx][gy] = random.randint(0, max_val)

        self.dia_total = 1
        self.hora_actual = 0
        self.clima_actual = "Normal"
        self.factor_crecimiento_base = 1.5 # Factor de crecimiento constante
        self.animales_nuevos = []

        self.grid_animales = {}
        self.modo_caza_carnivoro_activo = False
        self._poblar_decoraciones()
        self.terrain_cache = {"rio": {}, "selva": {}}
        self._precalcular_terrenos_cercanos()

    def reproducir_sonido_rio(self):
        """Reproduce el sonido del río en bucle"""
        if self.sonido_rio:
            self.sonido_rio.play(-1)  # -1 para hacer que suene en bucle

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
        for px, py in self.terreno["puentes"]:
            if math.sqrt((x - px)**2 + (y - py)**2) < 40: # Distancia de seguridad alrededor de los puentes
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
        self.terreno["plantas"] = []
        self.terreno["plantas_2"] = []
        
        decoraciones_todas = []
        intentos_max = 80
        margen = 10

        # Poblar árboles densamente en las selvas
        for selva in self.terreno["selvas"]:
            for _ in range(40): # Número de árboles por selva
                for _ in range(intentos_max):
                    x = random.randint(selva.rect.left + margen, selva.rect.right - margen)
                    y = random.randint(selva.rect.top + margen, selva.rect.bottom - margen)
                    if self._es_posicion_valida_para_vegetacion(x, y, decoraciones_todas, min_dist=25):
                        self.terreno["arboles"].append((x, y)); decoraciones_todas.append((x, y))
                        break

        # Poblar algunos árboles en las praderas
        for pradera in self.terreno["praderas"]:
            for _ in range(15): # Número de árboles por pradera
                for _ in range(intentos_max):
                    x = random.randint(pradera.rect.left + margen, pradera.rect.right - margen)
                    y = random.randint(pradera.rect.top + margen, pradera.rect.bottom - margen)
                    if self._es_posicion_valida_para_vegetacion(x, y, decoraciones_todas, min_dist=30):
                        self.terreno["arboles"].append((x, y)); decoraciones_todas.append((x, y))
                        break
        
        # Poblar plantas en grupos sobre el fondo
        num_grupos_plantas = 15
        plantas_por_grupo = 10
        radio_grupo = 40

        for _ in range(num_grupos_plantas):
            # Elegir un centro para el grupo que no esté en un terreno ya definido
            for _ in range(intentos_max):
                centro_x = random.randint(margen, SIM_WIDTH - margen)
                centro_y = random.randint(margen, SCREEN_HEIGHT - margen)
                if not self.choca_con_terreno(centro_x, centro_y) and self.terrain_grid[centro_x // CELL_SIZE][centro_y // CELL_SIZE] is None:
                    break
            
            for _ in range(plantas_por_grupo):
                x = centro_x + random.randint(-radio_grupo, radio_grupo)
                y = centro_y + random.randint(-radio_grupo, radio_grupo)
                if self._es_posicion_valida_para_vegetacion(x, y, decoraciones_todas, min_dist=10):
                    self.terreno["plantas"].append((x, y)); decoraciones_todas.append((x, y))
        
        # Poblar plantas_2 en grupos sobre el fondo
        num_grupos_plantas_2 = 12
        plantas_por_grupo_2 = 8
        radio_grupo_2 = 35

        for _ in range(num_grupos_plantas_2):
            # Elegir un centro para el grupo que no esté en un terreno ya definido
            for _ in range(intentos_max):
                centro_x = random.randint(margen, SIM_WIDTH - margen)
                centro_y = random.randint(margen, SCREEN_HEIGHT - margen)
                if not self.choca_con_terreno(centro_x, centro_y) and self.terrain_grid[centro_x // CELL_SIZE][centro_y // CELL_SIZE] is None:
                    break
            
            for _ in range(plantas_por_grupo_2):
                x = centro_x + random.randint(-radio_grupo_2, radio_grupo_2)
                y = centro_y + random.randint(-radio_grupo_2, radio_grupo_2)
                if self._es_posicion_valida_para_vegetacion(x, y, decoraciones_todas, min_dist=10):
                    self.terreno["plantas_2"].append((x, y)); decoraciones_todas.append((x, y))

    def _precalcular_terrenos_cercanos(self):
        print("Precalculando caché de terrenos cercanos para optimización...")
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

    def get_animal_at(self, pos):
        """Devuelve el primer animal encontrado en la posición del clic."""
        x, y = pos
        for animal in self.animales:
            if math.sqrt((animal.x - x)**2 + (animal.y - y)**2) < 10: # Radio de clic de 10px
                return animal
        return None

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
                    max_capacidad = Terrenos.MAX_HIERBA_NORMAL
                    tasa_crecimiento_base = 1
                    
                    cell_rect = pygame.Rect(gx * CELL_SIZE, gy * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                    pradera_actual = next((p for p in self.terreno["praderas"] if p.rect.colliderect(cell_rect)), None)
                    if pradera_actual:
                        max_capacidad = pradera_actual.max_hierba
                        tasa_crecimiento_base = pradera_actual.tasa_crecimiento
                    crecimiento_real = int(tasa_crecimiento_base * factor_crecimiento * (1 - self.grid_hierba[gx][gy] / max_capacidad))
                    self.grid_hierba[gx][gy] += crecimiento_real
                    self.grid_hierba[gx][gy] = min(self.grid_hierba[gx][gy], max_capacidad)
            
            for selva in self.terreno["selvas"]: selva.crecer_recursos(factor_crecimiento)
            for rio in self.terreno["rios"]: rio.crecer_recursos(factor_crecimiento)

            for c in self.recursos["carcasas"]: c.dias_descomposicion += 1
            self.recursos["carcasas"] = [c for c in self.recursos["carcasas"] if c.dias_descomposicion < 5]

            for animal in self.animales:
                animal._edad += 1

            self.animales_nuevos = []

        self.animales.extend(self.animales_nuevos)
        
        # Actualizar estado de cada animal
        for animal in self.animales:
            animal.actualizar(self)

        # Eliminar animales muertos de la simulación
        self.animales = [animal for animal in self.animales if animal.esta_vivo]

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

    def agregar_animal(self, tipo_animal, nombre=None, es_cria=False, pos=None):
        if es_cria:
            if pos:
                # La cría aparece cerca de la madre
                x = pos[0] + random.randint(-10, 10)
                y = pos[1] + random.randint(-10, 10)
            else: # Fallback si no se da posición
                x, y = self._obtener_posicion_inicial(tipo_animal)
            nombre = f"Cría de {tipo_animal.__name__}"
            nuevo_animal = tipo_animal(nombre, x, y, edad=-1) # Edad -1 para que en el siguiente ciclo de día se ponga a 0
        else:
            if nombre is None:
                nombre = f"{tipo_animal.__name__} {getattr(tipo_animal, 'contador', 0) + 1}"
            x, y = self._obtener_posicion_inicial(tipo_animal)
            nuevo_animal = tipo_animal(nombre, x, y)
            
        nuevo_animal.ecosistema = self # Asignar referencia al ecosistema
        self.animales.append(nuevo_animal)
                # Sonido de aparición
        if hasattr(nuevo_animal, "reproducir_sonido"):
            nuevo_animal.reproducir_sonido(1)


    def activar_modo_caza_carnivoro(self):
        self.modo_caza_carnivoro_activo = not self.modo_caza_carnivoro_activo
        for animal in self.animales:
            if isinstance(animal, Carnivoro):
                animal.modo_caza_activado = self.modo_caza_carnivoro_activo
                
                if self.modo_caza_carnivoro_activo:
                    # Encontrar el puente más cercano para cruzar
                    puentes_caza = [p for p in self.terreno["puentes"] if p[1] > 300] # Puentes horizontales
                    if not puentes_caza:
                        animal.objetivo_puente = None
                    else:
                        puente_cercano = min(puentes_caza, key=lambda p: (animal.x - p[0])**2 + (animal.y - p[1])**2)
                        animal.objetivo_puente = puente_cercano

                    print(f"{animal.nombre} entra en modo caza y se dirige a la zona de herbívoros.")
                    if animal.objetivo_puente:
                        animal.estado = "yendo_a_cazar"
                    else: # Si no hay puentes, deambula como antes
                        animal.estado = "deambulando"
                else:
                    print(f"{animal.nombre} sale del modo caza y regresa a su territorio.")
                    # Usar el puente que cruzó para regresar, si lo recuerda
                    animal.objetivo_puente = animal.puente_cruzado
                    if animal.objetivo_puente:
                        animal.estado = "regresando_de_cazar"
                    else:
                        animal.estado = "regresando_a_zona"
                    animal.objetivo_comida = None # Cancela cualquier caza actual

    def to_dict(self):
        """Convierte el estado del ecosistema a un diccionario serializable."""
        return {
            "fecha_guardado": datetime.now().isoformat(),
            "dia_total": self.dia_total,
            "hora_actual": self.hora_actual,
            "grid_hierba": self.grid_hierba,
            "clima_actual": self.clima_actual,
            "selvas": [{"rect": list(s.rect), "bayas": s.bayas} for s in self.terreno["selvas"]],
            "rios": [{"rect": list(r.rect), "peces": [{"x": p.x, "y": p.y, "energia": p.energia} for p in r.peces]} for r in self.terreno["rios"]],
            "arboles": [list(t) for t in self.terreno.get("arboles", [])],
            "plantas": [list(p) for p in self.terreno.get("plantas", [])],
            "plantas_2": [list(p) for p in self.terreno.get("plantas_2", [])],
            "puentes": [list(p) for p in self.terreno.get("puentes", [])],
            "animales": [
                {
                    "tipo": a.__class__.__name__,
                    "nombre": a.nombre, "x": a.x, "y": a.y, "edad": a.edad,
                    "energia": a.energia, "max_energia": a.max_energia,
                    "estado": a.estado
                }
                for a in self.animales
            ],
            "carcasas": [{"x": c.x, "y": c.y, "energia_restante": c.energia_restante, "dias": c.dias_descomposicion} for c in self.recursos["carcasas"]]
        }

    @classmethod
    def from_dict(cls, data):
        """Crea una instancia de Ecosistema a partir de un diccionario."""
        ecosistema = cls() # Crea una nueva instancia con valores por defecto

        # Cargar estado simple
        ecosistema.dia_total = data.get("dia_total", 1)
        ecosistema.hora_actual = data.get("hora_actual", 0)
        ecosistema.grid_hierba = data.get("grid_hierba", ecosistema.grid_hierba)
        ecosistema.clima_actual = data.get("clima_actual", ecosistema.clima_actual)

        # Cargar terrenos
        for i, s_data in enumerate(data.get("selvas", [])):
            if i < len(ecosistema.terreno["selvas"]):
                ecosistema.terreno["selvas"][i].bayas = s_data.get("bayas", 25)
        
        for i, r_data in enumerate(data.get("rios", [])):
            if i >= len(ecosistema.terreno["rios"]): continue
            rio = ecosistema.terreno["rios"][i]
            rio.peces = []
            for p_data in r_data.get("peces", []):
                pez = Pez(p_data["x"], p_data["y"], rio)
                pez.energia = p_data.get("energia", 50)
                rio.peces.append(pez)

        # Restaurar decoraciones (árboles, plantas, puentes) si están en el archivo
        if "arboles" in data:
            ecosistema.terreno["arboles"] = [tuple(p) for p in data.get("arboles", [])]
        if "plantas" in data:
            ecosistema.terreno["plantas"] = [tuple(p) for p in data.get("plantas", [])]
        if "plantas_2" in data:
            ecosistema.terreno["plantas_2"] = [tuple(p) for p in data.get("plantas_2", [])]
        if "puentes" in data:
            ecosistema.terreno["puentes"] = [tuple(p) for p in data.get("puentes", [])]

        # Recalcular la rejilla de tipo de terreno e indicadores de río (no sobreescribimos grid_hierba)
        ecosistema.terrain_grid = [[None for _ in range(ecosistema.grid_height)] for _ in range(ecosistema.grid_width)]
        ecosistema.is_river = [[False for _ in range(ecosistema.grid_height)] for _ in range(ecosistema.grid_width)]
        terrain_hierarchy = [
            ("montanas", "montana"),
            ("santuarios", "santuario"),
            ("selvas", "selva"),
            ("praderas", "pradera")
        ]
        for gx in range(ecosistema.grid_width):
            for gy in range(ecosistema.grid_height):
                cell_rect = pygame.Rect(gx * CELL_SIZE, gy * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                if any(rio.rect.colliderect(cell_rect) for rio in ecosistema.terreno["rios"]):
                    ecosistema.terrain_grid[gx][gy] = "rio"
                    ecosistema.is_river[gx][gy] = True
                    continue
                for terrain_list_name, terrain_type_name in terrain_hierarchy:
                    if any(t.rect.colliderect(cell_rect) for t in ecosistema.terreno[terrain_list_name]):
                        ecosistema.terrain_grid[gx][gy] = terrain_type_name
                        break

        # Actualizar caché de terrenos cercanos
        ecosistema.terrain_cache = {"rio": {}, "selva": {}}
        ecosistema._precalcular_terrenos_cercanos()

        # Cargar animales
        ecosistema.animales = []
        tipos = {cls.__name__: cls for cls in [Conejo, Raton, Cabra, Leopardo, Gato, Cerdo, Mono, Halcon, Insecto, Herbivoro, Carnivoro, Omnivoro]}
        for a_data in data.get("animales", []):
            tipo_clase = tipos.get(a_data.get("tipo"))
            if tipo_clase:
                animal = tipo_clase(a_data["nombre"], a_data["x"], a_data["y"], 
                                    a_data.get("edad", 0), a_data.get("energia", 100), 
                                    max_energia=a_data.get("max_energia"))
                animal.estado = a_data.get("estado", "deambulando")
                ecosistema.animales.append(animal)
        
        # Cargar carcasas
        ecosistema.recursos["carcasas"] = []
        for c_data in data.get("carcasas", []):
            carcasa = Carcasa(c_data["x"], c_data["y"], c_data.get("energia_restante", 60))
            carcasa.dias_descomposicion = c_data.get("dias", 0)
            ecosistema.recursos["carcasas"].append(carcasa)

        return ecosistema