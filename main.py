import pygame
import math 
from model import Ecosistema, Herbivoro, Carnivoro, Omnivoro, Conejo, Raton, Leopardo, Gato, Cerdo, Mono, Cabra, Halcon, Insecto, CELL_SIZE, MAX_HIERBA_PRADERA, Rio, Pez
from graph import PopulationGraph

# --- Constantes para Pygame ---
# Las constantes de la simulación (SIM_WIDTH, etc.) están ahora en model.py
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 700
SIM_WIDTH = 800
UI_WIDTH = 400

# --- Paleta de Colores ---
COLOR_BACKGROUND = (22, 160, 133)
COLOR_SIM_AREA = (46, 204, 113)
COLOR_HERBIVORO = (255, 255, 255)
COLOR_CARNIVORO = (231, 76, 60)
COLOR_OMNIVORO = (52, 152, 219)
COLOR_TEXT = (236, 240, 241)
COLOR_HEART = (255, 105, 180)
COLOR_RIO = (41, 128, 185)
COLOR_SELVA = (39, 174, 96)
COLOR_BUTTON = (26, 188, 156)
COLOR_PEZ = (0, 191, 255)
COLOR_CARCASA = (128, 128, 128)

# --- Clase de la Vista (GUI con Pygame) ---

class Button:
    def __init__(self, x, y, width, height, text, color, text_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.text_color = text_color
        self.font = pygame.font.SysFont("helvetica", 20)

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect, border_radius=8)
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

class PygameView:
    def __init__(self):
        pygame.init()
        try:
            pygame.mixer.init()
        except Exception:
            print("Aviso: no se pudo inicializar pygame.mixer; la música de fondo no estará disponible.")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Simulador de Ecosistema Virtual")
        self.font_header = pygame.font.SysFont("helvetica", 24, bold=True)
        self.font_normal = pygame.font.SysFont("consola", 16)
        self.font_small = pygame.font.SysFont("consola", 14)
        self.font_tiny = pygame.font.SysFont("consola", 12)
        self.sprites = self._load_sprites()
        self.music_playing = False
        try:
            import os
            music_files = [f for f in os.listdir("assets") if f.endswith(".mp3")]
            if music_files:
                music_path = os.path.join("assets", random.choice(music_files))
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.set_volume(0.15)
                pygame.mixer.music.play(-1)
                self.music_playing = True
            else:
                print("No se encontraron archivos .mp3 en la carpeta 'assets'. La música no se reproducirá.")
        except Exception as e:
            print(f"No se pudo cargar o reproducir la música de fondo: {e}")
        self.buttons = self._create_buttons()
        self.graph = PopulationGraph(SIM_WIDTH + 10, SCREEN_HEIGHT - 350, UI_WIDTH - 20, 120, self.font_small)
        self.mouse_pos = None

        # Superficie para el renderizado optimizado de la hierba
        self.hierba_surface = pygame.Surface((SIM_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        # NUEVO: Superficie para el fondo estático (terreno, decoraciones)
        self.background_surface = pygame.Surface((SIM_WIDTH, SCREEN_HEIGHT))
        # Flag para saber si el fondo estático necesita ser redibujado (ej. al cargar partida)
        self.needs_static_redraw = True

    def _load_sprites(self):
        sprites = {}
        sprite_definitions = {
            "Conejo": {"file": "conejo.png", "size": (15, 15)},
            "Raton": {"file": "raton.png", "size": (15, 15)},
            "Leopardo": {"file": "leopardo.png", "size": (15, 15)},
            "Gato": {"file": "gato.png", "size": (15, 15)},
            "Cabra": {"file": "cabra.png", "size": (15, 15)},
            "Cerdo": {"file": "cerdo.png", "size": (15, 15)},
            "Mono": {"file": "mono.png", "size": (15, 15)},
            "Halcon": {"file": "halcon.png", "size": (15, 15)},
            "Insecto": {"file": "insecto.png", "size": (8, 8)},
            "Pez": {"file": "pez.png", "size": (10, 10)},
            "arbol": {"file": "arbol_medium.png", "size": (30, 30)},
            "planta": {"file": "planta_small.png", "size": (12, 12)},
            "hierba": {"file": "hierba.png", "size": (20, 20)}  # Añadir sprite para hierba
        }
        try:
            for name, data in sprite_definitions.items():
                sprites[name] = pygame.transform.scale(pygame.image.load(f"assets/{data['file']}"), data['size'])
            return sprites
        except pygame.error as e:
            print(f"\n--- ADVERTENCIA: No se encontraron los sprites ---")
            print(f"Error: {e}.")
            print("La simulación usará círculos de colores en lugar de imágenes.")
            print("Para usar sprites, crea una carpeta 'assets' y coloca dentro los archivos .png de los animales (conejo.png, gato.png, etc.).\n")
            return None

    def _create_buttons(self):
        buttons = {}
        # --- Definición de la cuadrícula de botones para una mejor organización ---
        ui_x = SIM_WIDTH
        margin = 15
        spacing = 10
        btn_width = (UI_WIDTH - (2 * margin) - (2 * spacing)) / 3
        btn_height = 30

        col1_x = ui_x + margin
        col2_x = col1_x + btn_width + spacing
        col3_x = col2_x + btn_width + spacing
        
        # Botones de control de velocidad
        control_y = SCREEN_HEIGHT - 225
        buttons["pause_resume"] = Button(SIM_WIDTH + 10, control_y, 130, 35, "Pausa/Reanudar", COLOR_BUTTON, COLOR_TEXT)
        buttons["next_day"] = Button(SIM_WIDTH + 150, control_y, 130, 35, "Adelantar Día", COLOR_BUTTON, COLOR_TEXT)
        buttons["add_conejo"] = Button(col1_x, SCREEN_HEIGHT - 175, btn_width, btn_height, "Añadir Conejo", COLOR_HERBIVORO, (0,0,0))
        buttons["add_raton"] = Button(col2_x, SCREEN_HEIGHT - 175, btn_width, btn_height, "Añadir Ratón", COLOR_HERBIVORO, (0,0,0))
        buttons["add_cabra"] = Button(col3_x, SCREEN_HEIGHT - 175, btn_width, btn_height, "Añadir Cabra", COLOR_HERBIVORO, (0,0,0))
        buttons["add_leopardo"] = Button(col1_x, SCREEN_HEIGHT - 135, btn_width, btn_height, "Añadir Leopardo", COLOR_CARNIVORO, COLOR_TEXT)
        buttons["add_gato"] = Button(col2_x, SCREEN_HEIGHT - 135, btn_width, btn_height, "Añadir Gato", COLOR_CARNIVORO, COLOR_TEXT)
        buttons["add_cerdo"] = Button(col1_x, SCREEN_HEIGHT - 95, btn_width, btn_height, "Añadir Cerdo", COLOR_OMNIVORO, COLOR_TEXT)
        buttons["add_mono"] = Button(col2_x, SCREEN_HEIGHT - 95, btn_width, btn_height, "Añadir Mono", COLOR_OMNIVORO, COLOR_TEXT)
        buttons["add_halcon"] = Button(col3_x, SCREEN_HEIGHT - 135, btn_width, btn_height, "Añadir Halcón", COLOR_CARNIVORO, COLOR_TEXT) # Ajuste de posición
        buttons["add_insecto"] = Button(col3_x, SCREEN_HEIGHT - 95, btn_width, btn_height, "Añadir Insecto", COLOR_HERBIVORO, (0,0,0)) # Ajuste de posición
        
        btn_width_small, btn_height_small = 90, 30
        buttons["save"] = Button(SIM_WIDTH + 10, SCREEN_HEIGHT - 40, btn_width_small, btn_height_small, "Guardar", (0, 100, 0), COLOR_TEXT)
        buttons["load"] = Button(SIM_WIDTH + 105, SCREEN_HEIGHT - 40, btn_width_small, btn_height_small, "Cargar", (100, 100, 0), COLOR_TEXT)
        buttons["restart"] = Button(SIM_WIDTH + 200, SCREEN_HEIGHT - 40, btn_width_small, btn_height_small, "Reiniciar", (200, 50, 50), COLOR_TEXT)
        music_text = "Música: ON" if getattr(self, 'music_playing', False) else "Música: OFF"
        buttons["music"] = Button(SIM_WIDTH + 295, SCREEN_HEIGHT - 40, btn_width_small, btn_height_small, music_text, (80, 80, 80), COLOR_TEXT)
        return buttons

    def _draw_text(self, text, font, color, surface, x, y):
        text_shadow = font.render(text, 1, (0, 0, 0))
        surface.blit(text_shadow, (x + 1, y + 1))
        textobj = font.render(text, 1, color)
        textrect = textobj.get_rect()
        textrect.topleft = (x, y)
        surface.blit(textobj, textrect)

    def update_hierba_surface(self, ecosistema):
        """Actualiza la superficie de la hierba. Llamar solo cuando la hierba cambia."""
        self.hierba_surface.fill((0, 0, 0, 0)) # Limpiar la superficie
        if self.sprites and "hierba" in self.sprites:
            sprite_hierba = self.sprites["hierba"]
            for gx in range(ecosistema.grid_width):
                for gy in range(ecosistema.grid_height):
                    nivel_hierba = ecosistema.grid_hierba[gx][gy]
                    if nivel_hierba > 0:
                        alpha = int(255 * (nivel_hierba / MAX_HIERBA_PRADERA))
                        sprite_hierba.set_alpha(alpha)
                        self.hierba_surface.blit(sprite_hierba, (gx * CELL_SIZE, gy * CELL_SIZE))
        else:
            # Método alternativo si no hay sprite
            for gx in range(ecosistema.grid_width):
                for gy in range(ecosistema.grid_height):
                    nivel_hierba = ecosistema.grid_hierba[gx][gy]
                    if nivel_hierba > 0:
                        # Determinar el máximo local (pradera o normal)
                        es_pradera = any(p.rect.collidepoint(gx * CELL_SIZE, gy * CELL_SIZE) for p in ecosistema.terreno["praderas"])
                        max_local = MAX_HIERBA_PRADERA if es_pradera else 70 # MAX_HIERBA_NORMAL
                        intensidad = min(1.0, nivel_hierba / max_local)
                        color_base = list(COLOR_SIM_AREA)
                        color_hierba = (34, 139, 34)
                        color_final = tuple([int(color_base[i] * (1 - intensidad) + color_hierba[i] * intensidad) for i in range(3)])
                        pygame.draw.rect(self.hierba_surface, color_final, (gx * CELL_SIZE, gy * CELL_SIZE, CELL_SIZE, CELL_SIZE))

    def _create_static_background(self, ecosistema):
        """Dibuja todos los elementos estáticos en una superficie para optimizar el renderizado."""
        self.background_surface.fill(COLOR_SIM_AREA)
        
        # --- Dibujo de auras de terreno ---
        for selva in ecosistema.terreno["selvas"]:
            aura_rect = selva.rect.inflate(10, 10)
            s = pygame.Surface(aura_rect.size, pygame.SRCALPHA)
            s.fill(COLOR_SELVA + (30,))
            self.background_surface.blit(s, aura_rect.topleft)
        for rio in ecosistema.terreno["rios"]:
            aura_rect = rio.rect.inflate(10, 10)
            s = pygame.Surface(aura_rect.size, pygame.SRCALPHA)
            s.fill(COLOR_RIO + (50,))
            self.background_surface.blit(s, aura_rect.topleft)

        # --- Dibujo principal del terreno ---
        for selva in ecosistema.terreno["selvas"]:
            pygame.draw.rect(self.background_surface, COLOR_SELVA, selva.rect)
        for rio in ecosistema.terreno["rios"]:
            pygame.draw.rect(self.background_surface, tuple(max(0, c-40) for c in COLOR_RIO), rio.rect, 3)
            pygame.draw.rect(self.background_surface, COLOR_RIO, rio.rect)

        # --- Dibujo de decoraciones ---
        if self.sprites and "arbol" in self.sprites:
            for x, y in ecosistema.terreno["arboles"]:
                sprite = self.sprites["arbol"]
                self.background_surface.blit(sprite, (x - sprite.get_width() // 2, y - sprite.get_height() // 2))
        if self.sprites and "planta" in self.sprites:
            for x, y in ecosistema.terreno["plantas"]:
                sprite = self.sprites["planta"]
                self.background_surface.blit(sprite, (x - sprite.get_width() // 2, y - sprite.get_height() // 2))
        self.needs_static_redraw = False
    
    def _draw_recursos(self, ecosistema):
        pez_sprite = self.sprites.get("Pez") if self.sprites else None
        for rio in ecosistema.terreno["rios"]:
            for pez in rio.peces:
                if not pez.fue_comido:
                    if pez_sprite:
                        self.screen.blit(pez_sprite, (pez.x - pez_sprite.get_width() // 2, pez.y - pez_sprite.get_height() // 2))
                    else:
                        pygame.draw.circle(self.screen, COLOR_PEZ, (pez.x, pez.y), 3)

        for carcasa in ecosistema.recursos["carcasas"]:
            alpha = max(0, 255 - carcasa.dias_descomposicion * 50)
            temp_surface = pygame.Surface((10, 10), pygame.SRCALPHA)
            pygame.draw.circle(temp_surface, COLOR_CARCASA + (alpha,), (5, 5), 5)
            self.screen.blit(temp_surface, (carcasa.x - 5, carcasa.y - 5))

    def _draw_animales(self, ecosistema, animal_seleccionado):
        if self.sprites:
            for animal in ecosistema.animales:
                sprite_pos_x = animal.x - 7
                sprite_pos_y = animal.y - 7
                sprite = self.sprites.get(animal.__class__.__name__)
                if sprite:
                    self.screen.blit(sprite, (sprite_pos_x, sprite_pos_y))
                
                # --- Barra de energía centrada ---
                bar_width = 15
                bar_height = 4
                bar_x = animal.x - bar_width // 2
                bar_y = sprite_pos_y - bar_height - 2 # Posicionar la barra sobre el sprite

                max_energia = animal.max_energia or 100
                energia_percent = max(0, animal.energia) / max_energia
                pygame.draw.rect(self.screen, (0,0,0), (bar_x-1, bar_y-1, bar_width+2, bar_height+2))
                pygame.draw.rect(self.screen, (90, 90, 90), (bar_x, bar_y, bar_width, bar_height))
                pygame.draw.rect(self.screen, (0, 255, 0), (bar_x, bar_y, bar_width * energia_percent, bar_height))
                
                # --- Indicador de estado de huida ---
                if animal.estado == "huyendo":
                    self._draw_text("!", self.font_normal, (255, 255, 0), self.screen, animal.x - 4, bar_y - 15)
        else:
            for animal in ecosistema.animales:
                color = (0,0,0)
                if isinstance(animal, Herbivoro): color = COLOR_HERBIVORO
                elif isinstance(animal, Carnivoro): color = COLOR_CARNIVORO
                elif isinstance(animal, Omnivoro): color = COLOR_OMNIVORO
                pygame.draw.circle(self.screen, color, (int(animal.x), int(animal.y)), 7)
        if animal_seleccionado:
            pygame.draw.circle(self.screen, (255, 255, 0), (animal_seleccionado.x, animal_seleccionado.y), 10, 2)

    def _draw_ui(self, ecosistema, animal_seleccionado, sim_speed):
        ui_x = SIM_WIDTH + 10
        hora_str = str(ecosistema.hora_actual).zfill(2)
        self._draw_text(f"DÍA: {ecosistema.dia_total} - {hora_str}:00", self.font_header, COLOR_TEXT, self.screen, ui_x, 5)

        y_offset = 35
        self._draw_text(f"Estación: {ecosistema.estacion_actual}", self.font_normal, COLOR_TEXT, self.screen, ui_x, y_offset)
        y_offset += 20
        self._draw_text(f"Clima: {ecosistema.clima_actual}", self.font_normal, COLOR_TEXT, self.screen, ui_x, y_offset)
        
        y_offset = 80
        self._draw_text("--- INFO ---", self.font_normal, COLOR_TEXT, self.screen, ui_x, y_offset)
        y_offset += 25
        if animal_seleccionado:
            info = [
                f"Nombre: {animal_seleccionado.nombre}",
                f"Tipo: {animal_seleccionado.__class__.__name__}",
                f"Energía: {animal_seleccionado.energia}/{animal_seleccionado.max_energia}",
                f"Sed: {animal_seleccionado._sed}/150",
                f"Estado: {animal_seleccionado.estado}",
                f"Edad: {animal_seleccionado.edad}"
            ]
            for line in info:
                self._draw_text(line, self.font_small, COLOR_TEXT, self.screen, ui_x, y_offset)
                y_offset += 15
        else:
            # Desglose de poblaciones por tipo
            herb_count = sum(1 for a in ecosistema.animales if isinstance(a, Herbivoro))
            carn_count = sum(1 for a in ecosistema.animales if isinstance(a, Carnivoro))
            omni_count = sum(1 for a in ecosistema.animales if isinstance(a, Omnivoro))

            self._draw_text(f"Herbívoros: {herb_count}", self.font_normal, COLOR_HERBIVORO, self.screen, ui_x, y_offset)
            y_offset += 20
            self._draw_text(f"Carnívoros: {carn_count}", self.font_normal, COLOR_CARNIVORO, self.screen, ui_x, y_offset)
            y_offset += 20
            self._draw_text(f"Omnívoros: {omni_count}", self.font_normal, COLOR_OMNIVORO, self.screen, ui_x, y_offset)
            y_offset += 20

            bayas_totales = sum(s.bayas for s in ecosistema.terreno["selvas"])
            self._draw_text(f"Bayas: {bayas_totales}", self.font_normal, COLOR_TEXT, self.screen, ui_x, y_offset)
            y_offset += 20
            peces_totales = sum(len(r.peces) for r in ecosistema.terreno["rios"])
            self._draw_text(f"Peces: {peces_totales}", self.font_normal, COLOR_TEXT, self.screen, ui_x, y_offset)
            y_offset += 20
            # Indicador de velocidad
            speed_text = f"Velocidad: x{sim_speed}"
            self._draw_text(speed_text, self.font_normal, COLOR_TEXT, self.screen, ui_x, y_offset)
            y_offset += 20
            self._draw_text("Haz clic en un animal", self.font_small, COLOR_TEXT, self.screen, ui_x, y_offset)
            y_offset += 15
            self._draw_text("para ver sus detalles.", self.font_small, COLOR_TEXT, self.screen, ui_x, y_offset)

        self.graph.draw(self.screen)

    def draw_simulation(self, ecosistema, sim_over, animal_seleccionado, sim_speed):
        self.screen.fill(COLOR_BACKGROUND)
        
        if self.needs_static_redraw:
            self._create_static_background(ecosistema)

        self.screen.blit(self.background_surface, (0, 0))
        self.screen.blit(self.hierba_surface, (0, 0)) # Dibujar la superficie de hierba pre-renderizada
        self._draw_recursos(ecosistema)
        
        self._draw_animales(ecosistema, animal_seleccionado)
        self._draw_ui(ecosistema, animal_seleccionado, sim_speed)
        if not sim_over:
            for button in self.buttons.values():
                button.draw(self.screen)
        
        self._draw_text("ESC para salir", self.font_small, COLOR_TEXT, self.screen, 10, SCREEN_HEIGHT - 25)
        if self.mouse_pos and self.mouse_pos[0] < SIM_WIDTH:
            coord_text = f"({self.mouse_pos[0]}, {self.mouse_pos[1]})"
            self._draw_text(coord_text, self.font_small, COLOR_TEXT, self.screen, 10, SCREEN_HEIGHT - 45)
        
        pygame.display.flip()

    def close(self):
        try:
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
        except Exception:
            pass
        pygame.quit()

    def toggle_music(self):
        try:
            if not pygame.mixer.get_init():
                print("Mixer no inicializado; no se puede controlar la música.")
                return
            if self.music_playing and pygame.mixer.music.get_busy():
                pygame.mixer.music.pause()
                self.music_playing = False
                if "music" in self.buttons:
                    self.buttons["music"].text = "Música: OFF"
            else:
                try:
                    pygame.mixer.music.unpause()
                except Exception:
                    try:
                        pygame.mixer.music.play(-1)
                    except Exception as e:
                        print(f"No se pudo reproducir la música: {e}")
                        return
                self.music_playing = True
                if "music" in self.buttons:
                    self.buttons["music"].text = "Música: ON"
        except Exception as e:
            print(f"Error al alternar música: {e}")

class SimulationController:
    def __init__(self, dias_simulacion: int):
        pygame.init()  # Asegurar que pygame está inicializado
        self.ecosistema = Ecosistema()
        self.view = PygameView()
        self.dias_simulacion = dias_simulacion
        self.animal_seleccionado = None
        self.paused = True
        
        # Ajustar velocidades
        self.sim_speed_multiplier = 3  # Aumentado para mejor fluidez
        self.base_time_per_hour = 25   # Reducido para mejor respuesta
        self.last_update_time = pygame.time.get_ticks()
        self.clock = pygame.time.Clock()

        self.next_day_cooldown = 50  # Reducido para mejor respuesta

    def _poblar_ecosistema(self):
        tipos_de_animales = [Conejo, Raton, Cabra, Leopardo, Gato, Cerdo, Mono, Halcon, Insecto]
        for tipo in tipos_de_animales:
            for _ in range(10):
                self.ecosistema.agregar_animal(tipo)

    def _avanzar_dia(self):
        # Bucle para simular las 24 horas de un día
        for _ in range(24):
            self.ecosistema.simular_hora()
            # Detener si la simulación termina a mitad del día
            if self.ecosistema.dia_total >= self.dias_simulacion or not self.ecosistema.animales:
                return True
        
        # Actualizar el gráfico una vez al final del día avanzado
        self._actualizar_grafico()
        self.view.update_hierba_surface(self.ecosistema) # Actualizar hierba después del crecimiento
        return self.ecosistema.dia_total >= self.dias_simulacion or not self.ecosistema.animales
    
    def _actualizar_grafico(self):
        """Calcula las poblaciones y actualiza el gráfico."""
        poblaciones = (
            sum(1 for a in self.ecosistema.animales if isinstance(a, Herbivoro)),
            sum(1 for a in self.ecosistema.animales if isinstance(a, Carnivoro)),
            sum(1 for a in self.ecosistema.animales if isinstance(a, Omnivoro))
        )
        self.view.graph.update(poblaciones)

    def _avanzar_hora(self):
        # Actualizar gráfico cada hora para ver cambios más suaves
        poblaciones = (
            sum(1 for a in self.ecosistema.animales if isinstance(a, Herbivoro)),
            sum(1 for a in self.ecosistema.animales if isinstance(a, Carnivoro)),
            sum(1 for a in self.ecosistema.animales if isinstance(a, Omnivoro))
        )
        self.view.graph.update(poblaciones)

        self.ecosistema.simular_hora()
        # Si la hierba cambió (porque un animal comió), actualizar la superficie
        if self.ecosistema.hierba_cambio:
            self.view.update_hierba_surface(self.ecosistema)
            self.ecosistema.hierba_cambio = False
        if self.ecosistema.dia_total >= self.dias_simulacion or not self.ecosistema.animales:
            return True
        return False

    def _setup_button_actions(self):
        """Crea un diccionario que mapea nombres de botones a sus funciones."""
        animal_map = {
            "conejo": Conejo, "raton": Raton, "cabra": Cabra,
            "leopardo": Leopardo, "gato": Gato, "halcon": Halcon,
            "cerdo": Cerdo, "mono": Mono, "insecto": Insecto
        }

        self.button_actions = {
            "save": self._action_save,
            "load": self._action_load,
            "music": self.view.toggle_music,
            "pause_resume": self._action_toggle_pause,
            "next_day": self._action_advance_day,
            "restart": self._action_restart
        }
        
        # Añadir dinámicamente las acciones para agregar animales
        for name, cls in animal_map.items():
            # Usamos una función lambda con un argumento por defecto para "capturar"
            # el valor de 'cls' en cada iteración.
            self.button_actions[f"add_{name}"] = lambda species=cls: self.ecosistema.agregar_animal(species)

    def _action_save(self): self.ecosistema.guardar_estado()
    def _action_load(self):
        try: self.ecosistema.cargar_estado(); self.view.graph.history = []; self.view.update_hierba_surface(self.ecosistema); self.view.needs_static_redraw = True
        except FileNotFoundError: print("¡No se encontró guardado!")

    def _action_restart(self):
        print("Reiniciando simulación...")
        self.ecosistema = Ecosistema()
        self._poblar_ecosistema()
        self.view.graph.history.clear()
        self.animal_seleccionado = None
        self.view.update_hierba_surface(self.ecosistema)
        self.view.needs_static_redraw = True
        self.paused = True
    def _action_toggle_pause(self): self.paused = not self.paused
    def _action_advance_day(self):
        if self.ecosistema.dia_total < self.dias_simulacion and self.ecosistema.animales:
            # Hacer más lento el avance manual del día
            self.next_day_cooldown = 400  # Era 250
            return self._avanzar_dia()
        return True  # La simulación ya ha terminado o no hay animales

    def run(self):
        self._poblar_ecosistema()
        self.view.update_hierba_surface(self.ecosistema) # Renderizado inicial de la hierba
        
        running = True
        sim_over = False
        self._setup_button_actions()

        while running:
            self.clock.tick(60)  # Mantener 60 FPS constantes

            current_time = pygame.time.get_ticks()
            delta_time = current_time - self.last_update_time

            # Actualizar la simulación si no está en pausa
            if not self.paused and not sim_over and delta_time > self.base_time_per_hour / self.sim_speed_multiplier:
                sim_over = self._avanzar_hora()
                self.last_update_time = current_time
                
                if self.animal_seleccionado and not self.animal_seleccionado.esta_vivo:
                    self.animal_seleccionado = None

            # Manejo de eventos (refactorizado para mayor claridad)
            running, sim_over = self.handle_events(running, sim_over)

            self.view.draw_simulation(self.ecosistema, sim_over, self.animal_seleccionado, self.sim_speed_multiplier)
    
        self.view.close()

    def handle_events(self, running, sim_over):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                return False, sim_over
            
            if event.type == pygame.KEYDOWN and event.key == pygame.K_m:
                self.view.toggle_music()

            if event.type == pygame.MOUSEMOTION:
                self.view.mouse_pos = event.pos

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not sim_over:
                pos = pygame.mouse.get_pos()
                # Comprobar si se ha hecho clic en un botón
                clicked_button_name = self.get_clicked_button(pos)
                if clicked_button_name:
                    action = self.button_actions.get(clicked_button_name)
                    if action:
                        result = action()
                        if clicked_button_name in ["next_day", "restart"]:
                            sim_over = result or sim_over
                else:
                    # Si no se hizo clic en un botón, comprobar si se hizo clic en un animal
                    self.select_animal_at(pos)
        return running, sim_over

    def get_clicked_button(self, pos):
        for name, button in self.view.buttons.items():
            if button.rect.collidepoint(pos):
                return name
        return None

    def select_animal_at(self, pos):
        if pos[0] < SIM_WIDTH: # Solo seleccionar si el clic es en el área de simulación
            self.animal_seleccionado = None
            # Iterar en reversa para seleccionar el que está dibujado encima.
            for animal in reversed(self.ecosistema.animales):
                dist_sq = (animal.x - pos[0])**2 + (animal.y - pos[1])**2
                if dist_sq < 12**2: # 12 píxeles de radio al cuadrado
                    self.animal_seleccionado = animal
                    break

# --- Ejecución Principal ---

def main():
    controlador = SimulationController(dias_simulacion=200)
    controlador.run()

if __name__ == "__main__":
    main()