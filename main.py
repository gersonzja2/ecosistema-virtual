
import pygame
import random
from model import Ecosistema, Herbivoro, Carnivoro, Omnivoro, Conejo, Raton, Leopardo, Gato, Cerdo, Mono, Cabra, Halcon, Insecto, Rio, Pez, CELL_SIZE, MAX_HIERBA_PRADERA, SIM_WIDTH, SCREEN_HEIGHT
import os
import json

# === BEGIN AUDIO INIT ===
# Reduce latencia y mejora estabilidad del mixer
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
try:
    if not pygame.mixer.get_init():
        pygame.mixer.init(44100, -16, 2, 512)
    pygame.mixer.set_num_channels(32)  # varios sonidos simultáneos
except Exception as e:
    print("Aviso: no se pudo inicializar pygame.mixer:", e)
# === END AUDIO INIT ===

SCREEN_WIDTH = 1200
UI_WIDTH = 400
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
COLOR_SELECTED = (241, 196, 15)

class PopulationGraph:
    def __init__(self, x, y, width, height, font):
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.history = []
        self.colors = {
            "herb": (255, 255, 255),
            "carn": (231, 76, 60),
            "omni": (52, 152, 219)
        }
        self.labels = {
            "herb": "Herbívoros",
            "carn": "Carnívoros", 
            "omni": "Omnívoros"
        }

    def update(self, populations):
        self.history.append(populations)
        if len(self.history) > self.rect.width:
            self.history.pop(0)

    def draw(self, surface):
        pygame.draw.rect(surface, (40, 40, 40), self.rect)
        title_surf = self.font.render("Población", True, (236, 240, 241))
        surface.blit(title_surf, (self.rect.x + 5, self.rect.y + 5))

        legend_y = self.rect.y + 20
        for pop_type, label in self.labels.items():
            label_surf = self.font.render(label, True, self.colors[pop_type])
            surface.blit(label_surf, (self.rect.right - 80, legend_y))
            legend_y += 15

        if not self.history:
            return

        try:
            max_pop = max((max(p) for p in self.history if p), default=1)
        except ValueError:
            max_pop = 1

        for i, pop_type in enumerate(["herb", "carn", "omni"]):
            points = []
            for day, pops in enumerate(self.history):
                x_pos = self.rect.x + day
                y_pos = self.rect.bottom - int((pops[i] / max_pop) * (self.rect.height - 20))
                points.append((x_pos, y_pos))
            if len(points) > 1:
                pygame.draw.lines(surface, self.colors[pop_type], False, points, 1)

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

class Cloud:
    """Representa una nube que se mueve por la pantalla."""
    def __init__(self, image, screen_width, screen_height, y_range):
        self.image = image
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.y_range = y_range
        self.reset(on_screen=True) # Inicia en una posición aleatoria en pantalla

    def reset(self, on_screen=False):
        """Reinicia la posición y velocidad de la nube."""
        self.speed = random.uniform(0.2, 0.8) # Velocidad lenta y variable
        self.y = random.randint(self.y_range[0], self.y_range[1]) # Aparecen en el rango Y especificado
        # Si on_screen es True, la posiciona en cualquier parte de la pantalla. Si no, a la izquierda.
        if on_screen:
            self.x = random.randint(0, self.screen_width)
        else:
            self.x = random.randint(-self.image.get_width() - 200, -self.image.get_width())

    def update(self):
        """Mueve la nube y la reinicia si sale de la pantalla."""
        self.x += self.speed
        if self.x > self.screen_width:
            self.reset()

class Menu:
    def __init__(self, screen, font_header, font_normal, font_small):
        self.screen = screen
        self.font_header = font_header
        self.font_normal = font_normal
        self.font_small = font_small
        self.users = []
        self.saves = []
        self.selected_user = None
        self.selected_save = None
        self.input_text = ""
        self.input_active = False
        self.load_users()

        self.buttons = {
            "new_user": pygame.Rect(SIM_WIDTH + 50, 200, 300, 40),
            "new_save": pygame.Rect(SIM_WIDTH + 50, 450, 300, 40),
            "start_game": pygame.Rect(SIM_WIDTH + 50, 550, 300, 50)
        }

    def load_users(self):
        """Carga los nombres de usuario de las carpetas en 'saves'."""
        self.users = []
        if not os.path.exists("saves"):
            os.makedirs("saves")
        try:
            self.users = [d for d in os.listdir("saves") if os.path.isdir(os.path.join("saves", d))]
        except FileNotFoundError:
            pass

    def load_saves_for_user(self, username):
        """Carga las partidas guardadas para un usuario específico."""
        self.saves = []
        user_path = os.path.join("saves", username)
        if os.path.exists(user_path):
            self.saves = [f for f in os.listdir(user_path) if f.endswith(".json")]

    def handle_event(self, event):
        """Maneja los eventos de Pygame para el menú."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Lógica para seleccionar usuarios
            user_y_start = 100
            for i, user in enumerate(self.users):
                user_rect = pygame.Rect(SIM_WIDTH + 50, user_y_start + i * 30, 300, 30)
                if user_rect.collidepoint(event.pos):
                    self.selected_user = user
                    self.selected_save = None
                    self.load_saves_for_user(user)
                    return None

            # Lógica para seleccionar partidas
            save_y_start = 300
            for i, save in enumerate(self.saves):
                save_rect = pygame.Rect(SIM_WIDTH + 50, save_y_start + i * 30, 300, 30)
                if save_rect.collidepoint(event.pos):
                    self.selected_save = save
                    return None

            # Lógica para botones
            if self.buttons["new_user"].collidepoint(event.pos):
                self.input_active = True
                self.input_text = ""
                return None
            
            if self.buttons["new_save"].collidepoint(event.pos) and self.selected_user:
                # Crear una nueva partida (se guardará al salir de la simulación)
                num_saves = len(self.saves)
                new_save_name = f"partida_{num_saves + 1}.json"
                self.selected_save = new_save_name
                # No creamos el archivo aquí, solo preparamos el nombre.
                return self.get_selected_path()

            if self.buttons["start_game"].collidepoint(event.pos) and self.selected_user and self.selected_save:
                return self.get_selected_path()

        if event.type == pygame.KEYDOWN and self.input_active:
            if event.key == pygame.K_RETURN:
                if self.input_text:
                    new_user_path = os.path.join("saves", self.input_text)
                    if not os.path.exists(new_user_path):
                        os.makedirs(new_user_path)
                    self.load_users()
                    self.selected_user = self.input_text
                    self.load_saves_for_user(self.selected_user)
                self.input_active = False
                self.input_text = ""
            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            else:
                self.input_text += event.unicode
        
        return None

    def get_selected_path(self):
        if self.selected_user and self.selected_save:
            return os.path.join("saves", self.selected_user, self.selected_save)
        return None

    def draw(self):
        """Dibuja el menú completo en la pantalla."""
        self.screen.fill(COLOR_BACKGROUND)
        
        # Título
        title_surf = self.font_header.render("Simulador de Ecosistema", True, COLOR_TEXT)
        self.screen.blit(title_surf, (SIM_WIDTH // 2 - title_surf.get_width() // 2, 200))
        
        # Panel derecho
        pygame.draw.rect(self.screen, (40, 40, 40), (SIM_WIDTH, 0, UI_WIDTH, SCREEN_HEIGHT))
        
        # Sección de Usuarios
        self.screen.blit(self.font_header.render("Usuarios", True, COLOR_TEXT), (SIM_WIDTH + 20, 50))
        user_y_start = 100
        for i, user in enumerate(self.users):
            color = COLOR_SELECTED if user == self.selected_user else COLOR_TEXT
            user_surf = self.font_normal.render(user, True, color)
            self.screen.blit(user_surf, (SIM_WIDTH + 50, user_y_start + i * 30))

        # Botón/Input para nuevo usuario
        pygame.draw.rect(self.screen, COLOR_BUTTON, self.buttons["new_user"])
        if self.input_active:
            input_surf = self.font_normal.render(self.input_text + "|", True, COLOR_TEXT)
        else:
            input_surf = self.font_normal.render("Crear Nuevo Usuario", True, COLOR_TEXT)
        self.screen.blit(input_surf, (self.buttons["new_user"].x + 10, self.buttons["new_user"].y + 10))

        # Sección de Partidas
        if self.selected_user:
            self.screen.blit(self.font_header.render(f"Partidas de {self.selected_user}", True, COLOR_TEXT), (SIM_WIDTH + 20, 250))
            save_y_start = 300
            for i, save in enumerate(self.saves):
                color = COLOR_SELECTED if save == self.selected_save else COLOR_TEXT
                save_name = save.replace(".json", "").replace("_", " ").capitalize()
                save_surf = self.font_normal.render(save_name, True, color)
                self.screen.blit(save_surf, (SIM_WIDTH + 50, save_y_start + i * 30))
            
            # Botón para nueva partida
            pygame.draw.rect(self.screen, COLOR_BUTTON, self.buttons["new_save"])
            new_save_surf = self.font_normal.render("Nueva Partida", True, COLOR_TEXT)
            self.screen.blit(new_save_surf, (self.buttons["new_save"].x + 10, self.buttons["new_save"].y + 10))

        # Botón para Iniciar
        if self.selected_user and self.selected_save:
            pygame.draw.rect(self.screen, (0, 150, 0), self.buttons["start_game"])
            start_text = "Cargar Partida" if os.path.exists(self.get_selected_path()) else "Empezar Nueva Partida"
            start_surf = self.font_header.render(start_text, True, COLOR_TEXT)
            self.screen.blit(start_surf, (self.buttons["start_game"].centerx - start_surf.get_width() // 2, self.buttons["start_game"].centery - start_surf.get_height() // 2))

        pygame.display.flip()

class PygameView:
    def __init__(self):
        pygame.init()
        try:
            pygame.mixer.init()
        except Exception:
            print("Aviso: No se pudo inicializar pygame.mixer; la música de fondo no estará disponible.")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Simulador de Ecosistema Virtual")
        self.font_header = pygame.font.SysFont("helvetica", 24, bold=True)
        self.font_normal = pygame.font.SysFont("consola", 16)
        self.font_small = pygame.font.SysFont("consola", 14)
        self.font_tiny = pygame.font.SysFont("consola", 12)
        self.sprites = self._load_sprites()
        self.terrain_textures = self._load_terrain_textures()
        self.agua_texturas = self._load_water_textures()
        self.agua_frame_actual = 0
        self.tiempo_animacion_agua = 500 # ms por frame de animación
        self.ultimo_cambio_agua = pygame.time.get_ticks()

        self.music_playing = False
        try:
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

        self.hierba_surface = pygame.Surface((SIM_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.background_surface = pygame.Surface((SIM_WIDTH, SCREEN_HEIGHT))
        self.needs_static_redraw = True
        self.top_clouds = self._create_clouds(y_range=(5, SCREEN_HEIGHT // 3), count=10)
        self.middle_clouds = self._create_clouds(y_range=(SCREEN_HEIGHT // 3 + 10, SCREEN_HEIGHT // 2 - 70), count=5)
        self.bottom_clouds = self._create_clouds(y_range=(SCREEN_HEIGHT // 2 + 60, SCREEN_HEIGHT - 70), count=8)

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
            "arbol": {"file": "arbol_1.png", "size": (30, 50)},
            "planta": {"file": "plantas_1.png", "size": (30, 30)},
            "planta_2": {"file": "plantas_2.png", "size": (30, 30)},
            "nube": {"file": "texturas_nubes.png", "size": (120, 60)}
        }
        sprite_definitions["carcasa"] = {"file": "esqueleto.png", "size": (15, 15)}
        for name, data in sprite_definitions.items():
            try:
                sprites[name] = pygame.transform.scale(pygame.image.load(f"assets/{data['file']}"), data['size'])
            except (pygame.error, FileNotFoundError):
                print(f"ADVERTENCIA: No se pudo cargar el sprite '{data['file']}'. Se usará un marcador de posición.")
        
        # Carga especial para el puente para mantener la relación de aspecto
        try:
            puente_img = pygame.image.load("assets/textura_puente.png")
            original_width, original_height = puente_img.get_size()
            target_height = 70  # Queremos que el puente sea un poco más alto que el río (60px)
            aspect_ratio = original_width / original_height
            target_width = int(target_height * aspect_ratio)
            sprites["puente"] = pygame.transform.scale(puente_img, (target_width, target_height))
        except (pygame.error, FileNotFoundError):
            print("ADVERTENCIA: No se pudo cargar el sprite 'textura_puente.png'.")

        # Carga especial para el puente horizontal, rotando la textura
        # La imagen textura_puente2.png ya es horizontal, así que no la rotamos.
        try:
            puente_h_img = pygame.image.load("assets/textura_puente2.png")
            original_width, original_height = puente_h_img.get_size()
            target_height = 70 # Queremos que el puente tenga una altura de 70px para cruzar el río de 60px
            aspect_ratio = original_width / original_height # Aspecto original de la imagen horizontal
            target_width = int(target_height * aspect_ratio) # Calculamos el ancho proporcional
            sprites["puente_horizontal"] = pygame.transform.scale(puente_h_img, (target_width, target_height))
        except (pygame.error, FileNotFoundError):
            print("ADVERTENCIA: No se pudo cargar el sprite 'textura_puente2.png' para el puente horizontal.")


        if not sprites:
            print("\n--- ADVERTENCIA GENERAL: No se encontró ningún archivo de sprite en la carpeta 'assets'. ---")
            print("La simulación usará círculos de colores para representar a los animales.")
        return sprites

    def _load_terrain_textures(self):
        textures = {}
        texture_files = {
            "fondo": "textura_fondo.png",
            "montana": "textura_montana.png",
            "santuario": "textura_santuario.png",
            "selva": "textura_selva.png",
            "pradera": "textura_pradera.png"
        }
        for name, filename in texture_files.items():
            try:
                textures[name] = pygame.image.load(f"assets/{filename}").convert()
            except (pygame.error, FileNotFoundError):
                print(f"Advertencia: No se encontró la textura '{filename}'. Se usará un color sólido en su lugar.")
                textures[name] = None
        return textures


    def _load_water_textures(self):
        texturas = []
        i = 0
        while True:
            try:
                ruta = f"assets/fondo_agua{i}.png"
                texturas.append(pygame.image.load(ruta).convert())
                i += 1
            except (pygame.error, FileNotFoundError):
                break
        if not texturas:
            print("Advertencia: No se encontraron texturas de agua (ej: 'assets/fondo_agua0.png'). Se usará un color sólido.")
        return texturas

    def _create_buttons(self):
        buttons = {}
        ui_x = SIM_WIDTH
        margin = 15
        spacing = 10
        btn_width = int((UI_WIDTH - (2 * margin) - (2 * spacing)) / 3)
        btn_height = 30

        col1_x = ui_x + margin
        col2_x = col1_x + btn_width + spacing
        col3_x = col2_x + btn_width + spacing
        
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
        buttons["add_halcon"] = Button(col3_x, SCREEN_HEIGHT - 135, btn_width, btn_height, "Añadir Halcón", COLOR_CARNIVORO, COLOR_TEXT)
        buttons["add_insecto"] = Button(col3_x, SCREEN_HEIGHT - 95, btn_width, btn_height, "Añadir Insecto", COLOR_HERBIVORO, (0,0,0))
        
        btn_width_small, btn_height_small = 90, 30
        buttons["save"] = Button(SIM_WIDTH + 10, SCREEN_HEIGHT - 40, btn_width_small, btn_height_small, "Guardar", (0, 100, 0), COLOR_TEXT)
        buttons["load"] = Button(SIM_WIDTH + 10 + btn_width_small + spacing, SCREEN_HEIGHT - 40, btn_width_small, btn_height_small, "Cargar", (100, 100, 0), COLOR_TEXT)
        buttons["restart"] = Button(SIM_WIDTH + 10 + 2 * (btn_width_small + spacing), SCREEN_HEIGHT - 40, btn_width_small, btn_height_small, "Reiniciar", (200, 50, 50), COLOR_TEXT)
        music_text = "Música: ON" if getattr(self, 'music_playing', False) else "Música: OFF"
        buttons["music"] = Button(SIM_WIDTH + 10 + 3 * (btn_width_small + spacing), SCREEN_HEIGHT - 40, btn_width_small, btn_height_small, music_text, (80, 80, 80), COLOR_TEXT)

        # Botones contextuales (se dibujarán por separado)
        buttons["force_reproduce"] = Button(SIM_WIDTH + 15, 200, 180, 30, "Forzar Reproducción", (142, 68, 173), COLOR_TEXT)
        hunt_text = "Cazar Herbívoros"
        buttons["hunt"] = Button(SIM_WIDTH + 205, 65, 180, 30, hunt_text, (192, 57, 43), COLOR_TEXT)
        buttons["feed_herbivores"] = Button(SIM_WIDTH + 15, 65, 180, 30, "Alimentar Herbívoros", (211, 84, 0), COLOR_TEXT)

        return buttons

    def _create_clouds(self, y_range, count):
        """Crea la lista inicial de nubes."""
        cloud_sprite = self.sprites.get("nube")
        if not cloud_sprite:
            return []
        
        # Aseguramos que la nube tenga transparencia
        cloud_sprite_alpha = cloud_sprite.convert_alpha()
        return [Cloud(cloud_sprite_alpha, SIM_WIDTH, SCREEN_HEIGHT, y_range) for _ in range(count)]

    def _draw_text(self, text, font, color, surface, x, y):
        text_shadow = font.render(text, 1, (0, 0, 0))
        surface.blit(text_shadow, (x + 1, y + 1))
        textobj = font.render(text, 1, color)
        textrect = textobj.get_rect()
        textrect.topleft = (x, y)
        surface.blit(textobj, textrect)

    def _draw_tiled_texture(self, surface, texture, rect):
        if not texture:
            return
        tex_w, tex_h = texture.get_size()
        for y in range(rect.top, rect.bottom, tex_h):
            for x in range(rect.left, rect.right, tex_w):
                surface.blit(texture, (x, y))

    def _update_water_animation(self):
        if not self.agua_texturas:
            return
        current_time = pygame.time.get_ticks()
        time_per_frame = self.tiempo_animacion_agua
        if current_time - self.ultimo_cambio_agua > time_per_frame:
            self.ultimo_cambio_agua = current_time
            self.agua_frame_actual = (self.agua_frame_actual + 1) % len(self.agua_texturas)

    def _draw_animal_bars(self, animal):
        """Dibuja las barras de vida y sed sobre un animal."""
        BAR_WIDTH = 20
        BAR_HEIGHT = 3
        Y_OFFSET_VIDA = 10  # Distancia sobre el animal para la barra de vida

        # --- Barra de Vida (Energía) ---
        vida_percent = animal.energia / animal.max_energia
        vida_bar_width = int(BAR_WIDTH * vida_percent)
        vida_bar_bg = pygame.Rect(animal.x - BAR_WIDTH // 2, animal.y - Y_OFFSET_VIDA, BAR_WIDTH, BAR_HEIGHT)
        vida_bar_fill = pygame.Rect(animal.x - BAR_WIDTH // 2, animal.y - Y_OFFSET_VIDA, vida_bar_width, BAR_HEIGHT)
        pygame.draw.rect(self.screen, (80, 0, 0), vida_bar_bg) # Fondo rojo oscuro
        pygame.draw.rect(self.screen, (0, 255, 0), vida_bar_fill) # Relleno verde

    def _draw_animales(self, ecosistema, animal_seleccionado):
        for animal in ecosistema.animales:
            sprite = self.sprites.get(animal.__class__.__name__)
            if sprite:
                sprite_w, sprite_h = sprite.get_size()
                sprite_pos_x = animal.x - sprite_w // 2
                sprite_pos_y = animal.y - sprite_h // 2
                self.screen.blit(sprite, (sprite_pos_x, sprite_pos_y))
            else:
                # Si no hay sprite, dibuja un círculo de color como fallback
                self._draw_fallback_animal(animal)
            
            # Dibujar las barras de estado para cada animal
            self._draw_animal_bars(animal)

        if animal_seleccionado:
            pygame.draw.circle(self.screen, (255, 255, 0), (animal_seleccionado.x, animal_seleccionado.y), 10, 2)

    def _draw_pareja_seleccionada(self, pareja):
        if pareja:
            pygame.draw.circle(self.screen, (255, 0, 255), (pareja.x, pareja.y), 10, 2) # Color magenta para la pareja

    def _draw_fallback_animal(self, animal):
        """Dibuja un círculo de color para un animal si su sprite no está disponible."""
        color = (0, 0, 0)  # Color por defecto
        if isinstance(animal, Herbivoro): color = COLOR_HERBIVORO
        elif isinstance(animal, Carnivoro): color = COLOR_CARNIVORO
        elif isinstance(animal, Omnivoro): color = COLOR_OMNIVORO
        pygame.draw.circle(self.screen, color, (int(animal.x), int(animal.y)), 7)

    def _draw_ui(self, ecosistema, animal_seleccionado, pareja_seleccionada, sim_speed):
        ui_x = SIM_WIDTH + 10
        ui_rect = pygame.Rect(SIM_WIDTH, 0, UI_WIDTH, SCREEN_HEIGHT)
        pygame.draw.rect(self.screen, COLOR_BACKGROUND, ui_rect)

        hora_str = str(ecosistema.hora_actual).zfill(2)
        self._draw_text(f"DÍA: {ecosistema.dia_total} - {hora_str}:00", self.font_header, COLOR_TEXT, self.screen, ui_x, 5)

        y_offset = 40
        self._draw_text(f"Clima: {ecosistema.clima_actual}", self.font_normal, COLOR_TEXT, self.screen, ui_x, y_offset)
        
        y_offset = 105 # Aumentamos el offset para dejar espacio al nuevo botón
        self._draw_text("--- INFO GENERAL ---", self.font_normal, COLOR_TEXT, self.screen, ui_x, y_offset)
        y_offset += 25
        if animal_seleccionado:
            info = [
                f"Nombre: {animal_seleccionado.nombre}",
                f"Tipo: {animal_seleccionado.__class__.__name__}",
                f"Energía: {animal_seleccionado.energia}/{animal_seleccionado.max_energia}",
                f"Edad: {animal_seleccionado.edad} días"
            ]
            info.append(f"Estado: {animal_seleccionado.estado.capitalize()}")
            for line in info:
                self._draw_text(line, self.font_small, COLOR_TEXT, self.screen, ui_x, y_offset)
                y_offset += 15
            
            # Dibujar botón de reproducción si hay un animal seleccionado
            self.buttons["force_reproduce"].draw(self.screen)
        else:
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
            speed_text = f"Velocidad: x{sim_speed}"
            self._draw_text(speed_text, self.font_normal, COLOR_TEXT, self.screen, ui_x, y_offset)
            y_offset += 20
            self._draw_text("Haz clic en un animal", self.font_small, COLOR_TEXT, self.screen, ui_x, y_offset)
            y_offset += 15
            self._draw_text("para ver sus detalles.", self.font_small, COLOR_TEXT, self.screen, ui_x, y_offset)

        self.graph.draw(self.screen)

    def _create_static_background(self, ecosistema):
        """Crea la superficie de fondo con elementos que no cambian (terreno, decoraciones)."""
        self._draw_terrenos_estaticos(ecosistema)
        self._draw_decoraciones(ecosistema)
        self.needs_static_redraw = False

    def _draw_terrenos_estaticos(self, ecosistema):
        """Dibuja las texturas de fondo y luego las áreas de terreno específicas."""
        # 1. Dibuja la textura de fondo general en toda la superficie de la simulación.
        fondo_texture = self.terrain_textures.get("fondo")
        if fondo_texture:
            self._draw_tiled_texture(self.background_surface, fondo_texture, self.background_surface.get_rect())

        # 2. Dibuja cada área de terreno específica sobre el fondo.
        # El orden aquí importa: las selvas se dibujarán encima de las praderas si se superponen.
        terrain_types_to_draw = ["praderas", "selvas", "santuarios", "montanas"]

        for terrain_name in terrain_types_to_draw:
            texture = self.terrain_textures.get(terrain_name[:-1]) # "praderas" -> "pradera"
            if texture:
                for terreno_obj in ecosistema.terreno[terrain_name]:
                    self._draw_tiled_texture(self.background_surface, texture, terreno_obj.rect)

    def _draw_rios(self, ecosistema):
        """Dibuja los ríos, actualizando la animación del agua."""
        self._update_water_animation()
        for rio in ecosistema.terreno["rios"]:
            if self.agua_texturas:
                self._draw_tiled_texture(self.screen, self.agua_texturas[self.agua_frame_actual], rio.rect)
            else:
                pygame.draw.rect(self.screen, COLOR_RIO, rio.rect)

    def _draw_puentes(self, ecosistema):
        """Dibuja los puentes sobre el mapa."""
        sprite_puente_v = self.sprites.get("puente") # Textura para puentes verticales
        sprite_puente_h = self.sprites.get("puente_horizontal") # Textura para puentes horizontales
        center_x = SIM_WIDTH // 2

        for x, y in ecosistema.terreno["puentes"]:
            # Si la coordenada X del puente es la del centro + 1, es el puente superior (horizontal).
            if x == center_x + 2 and sprite_puente_h:
                sprite_a_usar = sprite_puente_h
            # Para todos los demás puentes, usamos la textura vertical.
            elif sprite_puente_v:
                sprite_a_usar = sprite_puente_v
            else:
                continue # Si no hay sprites, no dibujamos nada.
            
            self.screen.blit(sprite_a_usar, (x - sprite_a_usar.get_width() // 2, y - sprite_a_usar.get_height() // 2))

    def _draw_decoraciones(self, ecosistema):
        """Dibuja elementos de decoración como árboles y plantas sobre el fondo estático."""
        sprite_arbol = self.sprites.get("arbol")
        if sprite_arbol:
            for x, y in ecosistema.terreno["arboles"]:
                self.background_surface.blit(sprite_arbol, (x - sprite_arbol.get_width()//2, y - sprite_arbol.get_height()//2))
        sprite_planta = self.sprites.get("planta")
        if sprite_planta:
            for x, y in ecosistema.terreno["plantas"]:
                self.background_surface.blit(sprite_planta, (x - sprite_planta.get_width()//2, y - sprite_planta.get_height()//2))
        sprite_planta_2 = self.sprites.get("planta_2")
        if sprite_planta_2:
            for x, y in ecosistema.terreno["plantas_2"]:
                self.background_surface.blit(sprite_planta_2, (x - sprite_planta_2.get_width()//2, y - sprite_planta_2.get_height()//2))

    def _draw_clouds(self):
        """Dibuja y actualiza las nubes."""
        # Combinamos ambas listas de nubes para dibujarlas todas
        all_clouds = self.top_clouds + self.middle_clouds + self.bottom_clouds
        for cloud in all_clouds:
            cloud.update()
            cloud.image.set_alpha(180) # Hacemos las nubes semitransparentes
            self.screen.blit(cloud.image, (cloud.x, cloud.y))

    def _draw_recursos(self, ecosistema):
        carcasa_sprite = self.sprites.get("carcasa")
        for carcasa in ecosistema.recursos["carcasas"]:
            alpha = max(0, 255 - carcasa.dias_descomposicion * 50)
            if carcasa_sprite:
                temp_sprite = carcasa_sprite.copy()
                temp_sprite.set_alpha(alpha)
                sprite_w, sprite_h = temp_sprite.get_size()
                self.screen.blit(temp_sprite, (carcasa.x - sprite_w // 2, carcasa.y - sprite_h // 2))
            else:
                temp_surface = pygame.Surface((10, 10), pygame.SRCALPHA)
                pygame.draw.circle(temp_surface, COLOR_CARCASA + (alpha,), (5, 5), 5)
                self.screen.blit(temp_surface, (carcasa.x - 5, carcasa.y - 5))

    def _draw_peces(self, ecosistema):
        """Dibuja los peces en los ríos."""
        pez_sprite = self.sprites.get("Pez")
        for rio in ecosistema.terreno["rios"]:
            for pez in rio.peces:
                if pez_sprite:
                    sprite_w, sprite_h = pez_sprite.get_size()
                    self.screen.blit(pez_sprite, (pez.x - sprite_w // 2, pez.y - sprite_h // 2))
                else:
                    # Fallback a un círculo si no hay sprite
                    pygame.draw.circle(self.screen, COLOR_PEZ, (pez.x, pez.y), 4)

    def draw_simulation(self, ecosistema, sim_over, animal_seleccionado, pareja_seleccionada, sim_speed):
        self.screen.fill(COLOR_BACKGROUND)
        
        if self.needs_static_redraw:
            self._create_static_background(ecosistema)

        self.screen.blit(self.background_surface, (0, 0))
        self._draw_rios(ecosistema)
        self._draw_peces(ecosistema) # Dibujar peces sobre el agua
        self._draw_puentes(ecosistema)
        self.screen.blit(self.hierba_surface, (0, 0))
        self._draw_recursos(ecosistema)
        
        self._draw_animales(ecosistema, animal_seleccionado)
        self._draw_clouds() # Dibujamos las nubes aquí para que se superpongan a todo
        self._draw_pareja_seleccionada(pareja_seleccionada)
        self._draw_ui(ecosistema, animal_seleccionado, pareja_seleccionada, sim_speed)
        
        # Dibujar botones no contextuales
        for name, button in self.buttons.items():
            # El botón de reproducción se dibuja condicionalmente en _draw_ui
            if name == "force_reproduce" and not animal_seleccionado:
                continue
            # El resto de botones se dibujan siempre
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

class Persistencia:
    """
    Gestiona el guardado y la carga del estado de la simulación.
    Implementa mecanismos de respaldo para prevenir la pérdida de datos.
    """
    def guardar(self, ecosistema, archivo):
        """
        Guarda el estado del ecosistema en un archivo JSON.
        Crea un respaldo del archivo anterior antes de escribir.
        """
        if not archivo:
            print("Error: No se proporcionó una ruta de archivo para guardar.")
            return

        # Crear un respaldo del guardado anterior
        if os.path.exists(archivo):
            try:
                os.rename(archivo, archivo + ".bak")
                print(f"Respaldo creado en {archivo}.bak")
            except OSError as e:
                print(f"Advertencia: No se pudo crear el respaldo. Error: {e}")

        try:
            with open(archivo, 'w', encoding='utf-8') as f:
                json.dump(ecosistema.to_dict(), f, indent=4)
            print(f"Partida guardada exitosamente en {archivo}")
        except Exception as e:
            print(f"Error al guardar la partida: {e}")
            # Si el guardado falla, intentar restaurar el respaldo
            if os.path.exists(archivo + ".bak"):
                os.rename(archivo + ".bak", archivo)
                print("Se ha restaurado el guardado anterior desde el respaldo.")

    def rescatar(self, archivo):
        """
        Carga un ecosistema desde un archivo JSON.
        Si el archivo principal falla, intenta cargar desde el respaldo (.bak).
        """
        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"Partida cargada desde {archivo}")
                return Ecosistema.from_dict(data)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"No se pudo cargar {archivo} ({e}). Intentando cargar respaldo...")
            archivo_bak = archivo + ".bak"
            if os.path.exists(archivo_bak):
                with open(archivo_bak, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"Partida cargada exitosamente desde el respaldo {archivo_bak}")
                    return Ecosistema.from_dict(data)
            # Si no hay archivo principal ni respaldo, la excepción se propagará
            raise FileNotFoundError(f"No se encontró un archivo de guardado válido ni un respaldo para {archivo}")

class SimulationController:
    def __init__(self, dias_simulacion: int):
        pygame.init()  # Asegurar que pygame está inicializado
        self.ecosistema = Ecosistema()
        self.view = PygameView()
        self.dias_simulacion = dias_simulacion
        self.menu = Menu(self.view.screen, self.view.font_header, self.view.font_normal, self.view.font_small)
        
        self.current_state = "MENU" # Estados: "MENU", "SIMULATION"
        self.save_path = None

        self.animal_seleccionado = None
        self.pareja_seleccionada = None
        self.paused = True
        
        self.sim_speed_multiplier = 3
        self.base_time_per_hour = 50 # Ralentizamos un poco para mejor visualización
        self.last_update_time = pygame.time.get_ticks()
        self.clock = pygame.time.Clock()

    def _poblar_ecosistema(self):
        tipos_de_animales = [Conejo, Raton, Cabra, Leopardo, Gato, Cerdo, Mono, Halcon, Insecto]
        for tipo in tipos_de_animales:
            for _ in range(2):
                self.ecosistema.agregar_animal(tipo)

    def _avanzar_dia(self):
        for _ in range(24):
            self.ecosistema.simular_hora()
            if self.ecosistema.dia_total >= self.dias_simulacion or not self.ecosistema.animales:
                return True
        
        self._actualizar_grafico()
        return self.ecosistema.dia_total >= self.dias_simulacion or not self.ecosistema.animales
    
    def _actualizar_grafico(self):
        poblaciones = (
            sum(1 for a in self.ecosistema.animales if isinstance(a, Herbivoro)),
            sum(1 for a in self.ecosistema.animales if isinstance(a, Carnivoro)),
            sum(1 for a in self.ecosistema.animales if isinstance(a, Omnivoro))
        )
        self.view.graph.update(poblaciones)

    def _avanzar_hora(self):
        self.ecosistema.simular_hora()
        if self.ecosistema.dia_total >= self.dias_simulacion or not self.ecosistema.animales:
            return True
        if self.ecosistema.hora_actual == 0:
            self._actualizar_grafico()
        return False

    def _setup_button_actions(self):
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
            "restart": self._action_restart,
            "feed_herbivores": self._action_feed_all_herbivores,
            "force_reproduce": self._action_force_reproduce,
            "hunt": self._action_toggle_hunt_mode
        }
        
        for name, cls in animal_map.items():
            self.button_actions[f"add_{name}"] = lambda species=cls: self.ecosistema.agregar_animal(species)
        
    def _action_save(self):
        """Utiliza la clase Persistencia para guardar el estado del ecosistema."""
        if self.save_path:
            p = Persistencia()
            p.guardar(self.ecosistema, self.save_path)
        else:
            print("Error: No hay una ruta de guardado definida.")

    def _action_load(self):
        """Utiliza la clase Persistencia para cargar el estado del ecosistema."""
        if self.save_path:
            try:
                p = Persistencia()
                self.ecosistema = p.rescatar(self.save_path)
                self.view.graph.history.clear()
                self.view.needs_static_redraw = True
            except FileNotFoundError:
                print(f"No se encontró archivo de guardado en {self.save_path}. Creando nueva partida.")
                self.ecosistema = Ecosistema()
                self._poblar_ecosistema()
            except Exception as e:
                # Captura otros errores (ej. JSON corrupto, datos inválidos)
                print(f"Error crítico al cargar la partida: {e}. Se reiniciará la simulación.")
                self._action_restart()
        elif not self.ecosistema.animales: # Validación post-carga
            print("Partida cargada vacía. Poblando con animales iniciales.")
            self._poblar_ecosistema()

    def _action_restart(self):
        self.ecosistema = Ecosistema()
        self._poblar_ecosistema()
        self.view.graph.history.clear()
        self.animal_seleccionado = None
        self.pareja_seleccionada = None
        self.view.needs_static_redraw = True
        self.paused = True
        print("Simulación reiniciada a su estado inicial.")
    def _action_toggle_pause(self): self.paused = not self.paused
    def _action_advance_day(self):
        if self.ecosistema.dia_total < self.dias_simulacion and self.ecosistema.animales:
            return self._avanzar_dia()
        return True
    
    def _action_feed_all_herbivores(self):
        """Da la orden de comer a todos los herbívoros y omnívoros con baja energía."""
        print("Dando orden de comer a herbívoros y omnívoros hambrientos...")
        for animal in self.ecosistema.animales:
            if not isinstance(animal, Carnivoro) and (animal.energia / animal.max_energia) < 0.8:
                animal.buscar_comida(forzado=True)

    def _action_toggle_hunt_mode(self):
        """Activa o desactiva el modo de caza para carnívoros."""
        self.ecosistema.activar_modo_caza_carnivoro()
        # Actualizar texto del botón
        if self.ecosistema.modo_caza_carnivoro_activo:
            self.view.buttons["hunt"].text = "Regresar Carnívoros"
        else:
            self.view.buttons["hunt"].text = "Cazar Herbívoros"

    def _action_force_reproduce(self):
        if self.animal_seleccionado and self.pareja_seleccionada:
            # Asegurarse de que son de la misma especie antes de intentar la reproducción
            if type(self.animal_seleccionado) == type(self.pareja_seleccionada):
                self.animal_seleccionado.buscar_pareja_para_reproducir(self.pareja_seleccionada)
            else:
                print(f"Error: {self.animal_seleccionado.nombre} y {self.pareja_seleccionada.nombre} no son de la misma especie y no pueden reproducirse.")

    def run(self):
        running = True
        sim_over = False
        self._setup_button_actions()

        while running:
            self.clock.tick(60)  # Mantener 60 FPS constantes
            
            if self.current_state == "MENU":
                self.menu.draw()
                running = self.handle_menu_events()
            
            elif self.current_state == "SIMULATION":
                current_time = pygame.time.get_ticks()
                delta_time = current_time - self.last_update_time

                if not self.paused and not sim_over and delta_time > self.base_time_per_hour / self.sim_speed_multiplier:
                    sim_over = self._avanzar_hora()
                    self.last_update_time = current_time
                    
                running, sim_over = self.handle_simulation_events(running, sim_over)

                self.view.draw_simulation(self.ecosistema, sim_over, self.animal_seleccionado, self.pareja_seleccionada, self.sim_speed_multiplier)
    
        self.view.close()

    def handle_menu_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                return False
            
            selected_path = self.menu.handle_event(event)
            if selected_path:
                self.save_path = selected_path
                self.ecosistema = Ecosistema() # Crea una nueva instancia de ecosistema
                self._action_load() # Carga o crea una nueva partida
                
                # Validación: si el archivo no existía y se creó uno nuevo, poblarlo.
                if not self.ecosistema.animales and not os.path.exists(self.save_path):
                    print("Creando un nuevo mundo y poblándolo con animales.")
                    self._poblar_ecosistema()

                self.view.graph.history.clear()
                self.view.needs_static_redraw = True
                self.current_state = "SIMULATION"
        return True

    def handle_simulation_events(self, running, sim_over):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                # Al presionar ESC, guarda y vuelve al menú en lugar de cerrar
                self._action_save()
                self.current_state = "MENU"
                return True, sim_over
            
            if event.type == pygame.KEYDOWN and event.key == pygame.K_m:
                self.view.toggle_music()

            if event.type == pygame.MOUSEMOTION:
                self.view.mouse_pos = event.pos

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not sim_over:
                pos = pygame.mouse.get_pos()
                
                # Construir la lista de botones que se pueden clickear
                active_buttons = list(self.button_actions.keys())
                # El botón de reproducción solo está activo si hay un animal seleccionado
                if not self.animal_seleccionado:
                    if "force_reproduce" in active_buttons: active_buttons.remove("force_reproduce")
                
                clicked_button_name = self.get_clicked_button(pos, active_buttons)
                if clicked_button_name:
                    action = self.button_actions.get(clicked_button_name)
                    if action:
                        result = action()
                        if clicked_button_name == "next_day":
                            sim_over = result or sim_over
                else:
                    self.select_animal_at(pos)
        return running, sim_over

    def get_clicked_button(self, pos, button_keys):
        for name in button_keys:
            if self.view.buttons[name].rect.collidepoint(pos):
                return name
        return None

    def select_animal_at(self, pos):
        if pos[0] < SIM_WIDTH:
            animal_clicado = None
            for animal in reversed(self.ecosistema.animales):
                dist_sq = (animal.x - pos[0])**2 + (animal.y - pos[1])**2
                if dist_sq < 12**2:
                    animal_clicado = animal
                    break
            
            if not animal_clicado:
                # Si se hace clic en espacio vacío, se deselecciona todo.
                self.animal_seleccionado = None
                self.pareja_seleccionada = None
            elif not self.animal_seleccionado or self.animal_seleccionado == animal_clicado:
                self.animal_seleccionado = animal_clicado
                self.pareja_seleccionada = None # Deseleccionar pareja si se vuelve a clicar el principal
            else: # Si ya hay un animal seleccionado y se clica en otro diferente
                self.pareja_seleccionada = animal_clicado

def main():
    controlador = SimulationController(dias_simulacion=200)
    controlador.run()

if __name__ == "__main__":
    main()
