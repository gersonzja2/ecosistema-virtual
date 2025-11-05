import pygame
import random
from model import Ecosistema, Herbivoro, Carnivoro, Omnivoro, Conejo, Raton, Leopardo, Gato, Cerdo, Mono, Cabra, Halcon, Insecto, Rio, Pez, CELL_SIZE, MAX_HIERBA_PRADERA, SIM_WIDTH, SCREEN_HEIGHT

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
        self.terrain_textures = self._load_terrain_textures()
        self.agua_texturas = self._load_water_textures()
        self.agua_frame_actual = 0
        self.tiempo_animacion_agua = 500 # ms por frame de animación
        self.ultimo_cambio_agua = pygame.time.get_ticks()

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

        self.hierba_surface = pygame.Surface((SIM_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.background_surface = pygame.Surface((SIM_WIDTH, SCREEN_HEIGHT))
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
            "hierba": {"file": "hierba.png", "size": (20, 20)}
        }
        for name, data in sprite_definitions.items():
            try:
                sprites[name] = pygame.transform.scale(pygame.image.load(f"assets/{data['file']}"), data['size'])
            except (pygame.error, FileNotFoundError):
                print(f"ADVERTENCIA: No se pudo cargar el sprite '{data['file']}'. Se usará un marcador de posición si es necesario.")
        
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
            print("\n--- ADVERTENCIA GENERAL: No se encontró ningún archivo de sprite en la carpeta 'assets' ---")
            print("La simulación usará círculos de colores para todos los animales.")
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
                print(f"Advertencia: No se encontró la textura '{filename}'. Se usará un color sólido.")
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
            print("Advertencia: No se encontraron texturas de agua (ej: assets/fondo_agua0.png). Se usará un color sólido.")
        return texturas

    def _create_buttons(self):
        buttons = {}
        ui_x = SIM_WIDTH
        margin = 15
        spacing = 10
        btn_width = (UI_WIDTH - (2 * margin) - (2 * spacing)) / 3
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
        buttons["load"] = Button(SIM_WIDTH + 105, SCREEN_HEIGHT - 40, btn_width_small, btn_height_small, "Cargar", (100, 100, 0), COLOR_TEXT)
        buttons["restart"] = Button(SIM_WIDTH + 200, SCREEN_HEIGHT - 40, btn_width_small, btn_height_small, "Reiniciar", (200, 50, 50), COLOR_TEXT)
        music_text = "Música: ON" if getattr(self, 'music_playing', False) else "Música: OFF"
        buttons["music"] = Button(SIM_WIDTH + 295, SCREEN_HEIGHT - 40, btn_width_small, btn_height_small, music_text, (80, 80, 80), COLOR_TEXT)
        
        # Botones de acción para animal seleccionado
        buttons["force_eat"] = Button(SIM_WIDTH + 10, 220, 130, 30, "Forzar Comer", (0, 150, 0), COLOR_TEXT)
        buttons["force_reproduce"] = Button(SIM_WIDTH + 150, 220, 130, 30, "Forzar Reprod.", (200, 0, 200), COLOR_TEXT)
        return buttons

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

        if animal_seleccionado:
            pygame.draw.circle(self.screen, (255, 255, 0), (animal_seleccionado.x, animal_seleccionado.y), 10, 2)

    def _draw_fallback_animal(self, animal):
        """Dibuja un círculo de color para un animal si su sprite no está disponible."""
        color = (0, 0, 0)  # Color por defecto
        if isinstance(animal, Herbivoro): color = COLOR_HERBIVORO
        elif isinstance(animal, Carnivoro): color = COLOR_CARNIVORO
        elif isinstance(animal, Omnivoro): color = COLOR_OMNIVORO
        pygame.draw.circle(self.screen, color, (int(animal.x), int(animal.y)), 7)

    def _draw_ui(self, ecosistema, animal_seleccionado, sim_speed):
        ui_x = SIM_WIDTH + 10
        ui_rect = pygame.Rect(SIM_WIDTH, 0, UI_WIDTH, SCREEN_HEIGHT)
        pygame.draw.rect(self.screen, COLOR_BACKGROUND, ui_rect)

        hora_str = str(ecosistema.hora_actual).zfill(2)
        self._draw_text(f"DÍA: {ecosistema.dia_total} - {hora_str}:00", self.font_header, COLOR_TEXT, self.screen, ui_x, 5)

        y_offset = 40
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
                f"Estado: {'Vivo' if animal_seleccionado.esta_vivo else 'Muerto'}",
                f"Edad: {animal_seleccionado.edad}"
            ]
            for line in info:
                self._draw_text(line, self.font_small, COLOR_TEXT, self.screen, ui_x, y_offset)
                y_offset += 15
            
            # Dibujar botones de acción si hay un animal seleccionado
            if "force_eat" in self.buttons: self.buttons["force_eat"].draw(self.screen)
            if "force_reproduce" in self.buttons: self.buttons["force_reproduce"].draw(self.screen)

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
        self.background_surface.fill(COLOR_SIM_AREA)
        if self.terrain_textures.get("fondo"):
            self._draw_tiled_texture(self.background_surface, self.terrain_textures["fondo"], self.background_surface.get_rect())

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
        for x, y in ecosistema.terreno["arboles"]:
            sprite = self.sprites.get("arbol")
            if sprite: self.background_surface.blit(sprite, (x - sprite.get_width()//2, y - sprite.get_height()//2))
        for x, y in ecosistema.terreno["plantas"]:
            sprite = self.sprites.get("planta")
            if sprite: self.background_surface.blit(sprite, (x - sprite.get_width()//2, y - sprite.get_height()//2))

    def update_hierba_surface(self, ecosistema):
        self.hierba_surface.fill((0, 0, 0, 0))
        hierba_sprite = self.sprites.get("hierba") if self.sprites else None
        for gx in range(ecosistema.grid_width):
            for gy in range(ecosistema.grid_height):
                valor_hierba = ecosistema.grid_hierba[gx][gy]
                if valor_hierba > 5:
                    alpha = min(255, int((valor_hierba / MAX_HIERBA_PRADERA) * 255))
                    if hierba_sprite:
                        temp_sprite = hierba_sprite.copy()
                        temp_sprite.set_alpha(alpha)
                        self.hierba_surface.blit(temp_sprite, (gx * CELL_SIZE, gy * CELL_SIZE))

    def _draw_recursos(self, ecosistema):
        for carcasa in ecosistema.recursos["carcasas"]:
            alpha = max(0, 255 - carcasa.dias_descomposicion * 50)
            temp_surface = pygame.Surface((10, 10), pygame.SRCALPHA)
            pygame.draw.circle(temp_surface, COLOR_CARCASA + (alpha,), (5, 5), 5)
            self.screen.blit(temp_surface, (carcasa.x - 5, carcasa.y - 5))

    def draw_simulation(self, ecosistema, sim_over, animal_seleccionado, sim_speed):
        self.screen.fill(COLOR_BACKGROUND)
        
        if self.needs_static_redraw:
            self._create_static_background(ecosistema)

        self.screen.blit(self.background_surface, (0, 0))
        self._draw_rios(ecosistema)
        self._draw_puentes(ecosistema)
        self.screen.blit(self.hierba_surface, (0, 0))
        self._draw_recursos(ecosistema)
        
        self._draw_animales(ecosistema, animal_seleccionado)
        self._draw_ui(ecosistema, animal_seleccionado, sim_speed)
        if not sim_over:
            # Dibujar solo los botones que no dependen de la selección
            for name, button in self.buttons.items():
                if name not in ["force_eat", "force_reproduce"]:
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
        
        self.sim_speed_multiplier = 3
        self.base_time_per_hour = 25
        self.last_update_time = pygame.time.get_ticks()
        self.clock = pygame.time.Clock()

    def _poblar_ecosistema(self):
        tipos_de_animales = [Conejo, Raton, Cabra, Leopardo, Gato, Cerdo, Mono, Halcon, Insecto]
        for tipo in tipos_de_animales:
            for _ in range(10):
                self.ecosistema.agregar_animal(tipo)

    def _avanzar_dia(self):
        for _ in range(24):
            self.ecosistema.simular_hora()
            if self.ecosistema.dia_total >= self.dias_simulacion or not self.ecosistema.animales:
                return True
        
        self._actualizar_grafico()
        self.view.update_hierba_surface(self.ecosistema)
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
        if self.ecosistema.hierba_cambio:
            self.view.update_hierba_surface(self.ecosistema)
            self.ecosistema.hierba_cambio = False
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
            "restart": self._action_restart
        }
        
        for name, cls in animal_map.items():
            self.button_actions[f"add_{name}"] = lambda species=cls: self.ecosistema.agregar_animal(species)
        
        # Acciones para los nuevos botones
        self.button_actions["force_eat"] = self._action_force_eat
        self.button_actions["force_reproduce"] = self._action_force_reproduce

    def _action_force_eat(self):
        if self.animal_seleccionado: print(f"Forzando a {self.animal_seleccionado.nombre} a buscar comida.")
    def _action_force_reproduce(self):
        if self.animal_seleccionado: print(f"Forzando a {self.animal_seleccionado.nombre} a buscar pareja.")

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
            return self._avanzar_dia()
        return True

    def run(self):
        self._poblar_ecosistema()
        self.view.update_hierba_surface(self.ecosistema)
        
        running = True
        sim_over = False
        self._setup_button_actions()

        while running:
            self.clock.tick(60)  # Mantener 60 FPS constantes

            current_time = pygame.time.get_ticks()
            delta_time = current_time - self.last_update_time

            if not self.paused and not sim_over and delta_time > self.base_time_per_hour / self.sim_speed_multiplier:
                sim_over = self._avanzar_hora()
                self.last_update_time = current_time
                
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
                
                # Determinar qué botones están activos para la comprobación de clics
                active_buttons = list(self.view.buttons.keys())
                if not self.animal_seleccionado:
                    active_buttons = [b for b in active_buttons if b not in ["force_eat", "force_reproduce"]]
                clicked_button_name = self.get_clicked_button(pos, active_buttons)
                if clicked_button_name:
                    action = self.button_actions.get(clicked_button_name)
                    if action:
                        result = action()
                        if clicked_button_name in ["next_day", "restart"]:
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
            self.animal_seleccionado = None
            for animal in reversed(self.ecosistema.animales):
                dist_sq = (animal.x - pos[0])**2 + (animal.y - pos[1])**2
                if dist_sq < 12**2:
                    self.animal_seleccionado = animal
                    break

def main():
    controlador = SimulationController(dias_simulacion=200)
    controlador.run()

if __name__ == "__main__":
    main()