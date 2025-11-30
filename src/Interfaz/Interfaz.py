
import pygame
import random
from src.Logica.Logica import Ecosistema, Herbivoro, Carnivoro, Omnivoro, SIM_WIDTH, SCREEN_HEIGHT
from src.Interfaz.Constantes import *
from .Componentes_ui import PopulationGraph, Button, Cloud
import os

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
            music_folder = "assets"  # La música de fondo está en 'assets'
            music_files = [f for f in os.listdir(music_folder) if f.endswith(".mp3")]
            if music_files:
                music_path = os.path.join(music_folder, random.choice(music_files))
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.set_volume(0.15)
                pygame.mixer.music.play(-1)
                self.music_playing = True
            else:
                print(f"No se encontraron archivos .mp3 en la carpeta '{music_folder}'. La música no se reproducirá.")
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
        
        # --- Posicionamiento dinámico de botones inferiores para una alineación perfecta ---
        current_x = SIM_WIDTH + 10
        y_pos = SCREEN_HEIGHT - 40

        # Botón "Guardar como..."
        save_as_width = btn_width_small + 30 # Ancho personalizado
        buttons["save_as"] = Button(current_x, y_pos, save_as_width, btn_height_small, "Guardar como...", (0, 100, 100), COLOR_TEXT)
        current_x += save_as_width + spacing

        # Botones restantes
        buttons["restart"] = Button(current_x, y_pos, btn_width_small, btn_height_small, "Reiniciar", (200, 50, 50), COLOR_TEXT)
        current_x += btn_width_small + spacing

        music_text = "Música: ON" if getattr(self, 'music_playing', False) else "Música: OFF"
        buttons["music"] = Button(current_x, y_pos, btn_width_small, btn_height_small, music_text, (80, 80, 80), COLOR_TEXT)

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
            # Recuentos para la UI
            herb_count = sum(1 for a in ecosistema.animales if isinstance(a, Herbivoro))
            carn_count = sum(1 for a in ecosistema.animales if isinstance(a, Carnivoro))
            omni_count = sum(1 for a in ecosistema.animales if isinstance(a, Omnivoro))
            peces_totales = sum(len(r.peces) for r in ecosistema.terreno["rios"])
            animales_totales = len(ecosistema.animales) + peces_totales

            self._draw_text(f"Animales Totales: {animales_totales}", self.font_normal, COLOR_TEXT, self.screen, ui_x, y_offset)
            y_offset += 20
            self._draw_text(f"Herbívoros: {herb_count}", self.font_normal, COLOR_HERBIVORO, self.screen, ui_x, y_offset)
            y_offset += 20
            self._draw_text(f"Carnívoros: {carn_count}", self.font_normal, COLOR_CARNIVORO, self.screen, ui_x, y_offset)
            y_offset += 20
            self._draw_text(f"Omnívoros: {omni_count}", self.font_normal, COLOR_OMNIVORO, self.screen, ui_x, y_offset)
            y_offset += 20

            bayas_totales = sum(s.bayas for s in ecosistema.terreno["selvas"])
            self._draw_text(f"Bayas: {bayas_totales}", self.font_normal, COLOR_TEXT, self.screen, ui_x, y_offset)
            y_offset += 20
            self._draw_text(f"Peces: {peces_totales}", self.font_normal, COLOR_TEXT, self.screen, ui_x, y_offset)
            y_offset += 20
            speed_text = f"Velocidad: x{sim_speed}"
            self._draw_text(speed_text, self.font_normal, COLOR_TEXT, self.screen, ui_x, y_offset)
            y_offset += 20
            self._draw_text("Haz clic en un animal", self.font_small, COLOR_TEXT, self.screen, ui_x, y_offset)
            y_offset += 15
            self._draw_text("para ver sus detalles.", self.font_small, COLOR_TEXT, self.screen, ui_x, y_offset)

        self.graph.draw(self.screen)
        
        # Dibujar todos los botones de la UI aquí para asegurar que están por encima del panel
        for name, button in self.buttons.items():
            # Botones contextuales que dependen del estado
            if name == "force_reproduce" and not animal_seleccionado:
                continue
            if name == "hunt" and animal_seleccionado:
                continue
            if name == "feed_herbivores" and animal_seleccionado:
                continue
            
            # El resto de botones se dibujan siempre
            button.draw(self.screen)



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
        
        self._draw_text("ESC para salir", self.font_small, COLOR_TEXT, self.screen, 10, SCREEN_HEIGHT - 25)
        if self.mouse_pos and self.mouse_pos[0] < SIM_WIDTH:
            coord_text = f"({self.mouse_pos[0]}, {self.mouse_pos[1]})"
            self._draw_text(coord_text, self.font_small, COLOR_TEXT, self.screen, 10, SCREEN_HEIGHT - 45)
        
        pygame.display.flip()

    def draw_save_menu(self, save_slots, input_text, selected_save):
        """Dibuja un menú superpuesto para 'Guardar como...'."""
        # Dibuja un rectángulo semitransparente sobre el área de simulación
        overlay = pygame.Surface((SIM_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # Panel de guardado
        panel_rect = pygame.Rect(150, 150, 500, 400)
        pygame.draw.rect(self.screen, (30, 30, 30), panel_rect, border_radius=15)
        pygame.draw.rect(self.screen, COLOR_SELECTED, panel_rect, width=2, border_radius=15)

        # Título
        title_surf = self.font_header.render("Guardar Partida Como...", True, COLOR_TEXT)
        self.screen.blit(title_surf, (panel_rect.x + 20, panel_rect.y + 20))

        # Campo de texto para nuevo nombre
        input_rect = pygame.Rect(panel_rect.x + 20, panel_rect.y + 70, panel_rect.width - 40, 40)
        pygame.draw.rect(self.screen, (50, 50, 50), input_rect)
        input_surf = self.font_normal.render(input_text + "|", True, COLOR_TEXT)
        self.screen.blit(input_surf, (input_rect.x + 10, input_rect.y + 10))

        # Lista de partidas existentes para sobrescribir
        self._draw_text("O selecciona una para sobrescribir:", self.font_small, COLOR_TEXT, self.screen, panel_rect.x + 20, panel_rect.y + 130)
        save_y_start = panel_rect.y + 160
        for i, save in enumerate(save_slots):
            color = COLOR_SELECTED if save == selected_save else COLOR_TEXT
            save_name = save.replace(".json", "").replace("_", " ").capitalize()
            save_surf = self.font_normal.render(save_name, True, color)
            save_rect = save_surf.get_rect(topleft=(panel_rect.x + 20, save_y_start + i * 35))
            self.screen.blit(save_surf, save_rect)

        # Instrucciones
        self._draw_text("Presiona ENTER para guardar.", self.font_small, COLOR_TEXT, self.screen, panel_rect.x + 20, panel_rect.bottom - 50)
        self._draw_text("Presiona ESC para cancelar.", self.font_small, COLOR_TEXT, self.screen, panel_rect.x + 20, panel_rect.bottom - 30)

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

    def handle_event(self, event, ecosistema, animal_seleccionado):
        """
        Procesa un evento de Pygame y lo traduce a un comando de alto nivel para el controlador.
        Devuelve un diccionario con el tipo de comando y datos adicionales si es necesario.
        """
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            return {"type": "quit"}
        
        if event.type == pygame.KEYDOWN and event.key == pygame.K_m:
            return {"type": "toggle_music"}

        if event.type == pygame.MOUSEMOTION:
            self.mouse_pos = event.pos
            return None # No es necesario notificar al controlador de cada movimiento

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            
            # 1. Comprobar si se ha hecho clic en un botón de la UI
            active_buttons = list(self.buttons.keys())
            if not animal_seleccionado:
                if "force_reproduce" in active_buttons: active_buttons.remove("force_reproduce")
            
            for name in active_buttons:
                if self.buttons[name].rect.collidepoint(pos):
                    print(f"DEBUG: PygameView detected click on button '{name}' at {pos}")
                    return {"type": f"click_button_{name}"}

            # 2. Si no es un botón, comprobar si se ha hecho clic en un animal en el área de simulación
            if pos[0] < SIM_WIDTH:
                return {"type": "click_simulation_area", "pos": pos}

        return None
