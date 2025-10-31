import pygame
import time
import random
from model import Ecosistema, Herbivoro, Carnivoro, Omnivoro, Animal, ENERGIA_REPRODUCCION, EDAD_ADULTA, Conejo, Raton, Leopardo, Gato, Cerdo, Mono
from graph import PopulationGraph

# --- Constantes para Pygame ---
# Las constantes de la simulación (SIM_WIDTH, etc.) están ahora en model.py
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 700
SIM_WIDTH = 800 # Área de la simulación
UI_WIDTH = 400  # Área para la interfaz de texto

COLOR_BACKGROUND = (22, 160, 133)
COLOR_SIM_AREA = (46, 204, 113)
COLOR_HERBIVORO = (255, 255, 255) # Blanco
COLOR_CARNIVORO = (231, 76, 60)   # Rojo
COLOR_OMNIVORO = (52, 152, 219)  # Azul
COLOR_TEXT = (236, 240, 241)
COLOR_HEART = (255, 105, 180) # Rosa para el corazón
COLOR_MONTANA = (149, 165, 166) # Gris
COLOR_RIO = (41, 128, 185)     # Azul oscuro
COLOR_SELVA = (39, 174, 96)     # Verde oscuro
COLOR_PRADERA = (118, 215, 196) # Verde claro
COLOR_SANTUARIO = (241, 196, 15) # Amarillo
COLOR_BUTTON = (26, 188, 156)
COLOR_CARCASA = (128, 128, 128) # Gris para carcasas

# --- Clase para Botones ---

class Button:
    """Clase para crear botones clickeables en Pygame."""
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

# --- Clase de la Vista (GUI con Pygame) ---

class PygameView:
    """Se encarga de mostrar la simulación en una ventana con Pygame."""
    def __init__(self):
        # Inicializar Pygame y el mezclador de audio
        pygame.init()
        try:
            # Inicializar el mixer por separado para mayor control (es seguro si ya está inicializado)
            pygame.mixer.init()
        except Exception:
            # Si falla, seguimos sin audio (por ejemplo en entornos sin dispositivo de audio)
            print("Aviso: no se pudo inicializar pygame.mixer; la música de fondo no estará disponible.")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Simulador de Ecosistema Virtual")
        self.font_header = pygame.font.SysFont("helvetica", 24, bold=True)
        self.font_normal = pygame.font.SysFont("consola", 16)
        self.font_small = pygame.font.SysFont("consola", 14)
        self.font_tiny = pygame.font.SysFont("consola", 12)
        # Cargar sprites primero
        self.sprites = self._load_sprites()
        # Cargar texturas de terreno
        self.terrain_textures = self._load_terrain_textures()
        # Cargar texturas animadas para el agua
        self.agua_texturas = self._load_water_textures()
        self.agua_frame_actual = 0
        self.tiempo_animacion_agua = 500 # ms por frame de animación
        self.ultimo_cambio_agua = pygame.time.get_ticks()

        # Intentar cargar y reproducir la música de fondo
        self.music_playing = False
        try:
            music_path = "assets/musica_fondo_0.mp3"
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.set_volume(0.15)  # Volumen por defecto (0.0 - 1.0)
            pygame.mixer.music.play(-1)  # Repetir indefinidamente
            self.music_playing = True
        except Exception as e:
            # No abortamos la ejecución si falla la música
            print(f"No se pudo cargar/reproducir la música de fondo: {e}")
        # Crear botones después de conocer el estado de la música para mostrar el texto correcto
        self.buttons = self._create_buttons()
        self.graph = PopulationGraph(SIM_WIDTH + 10, SCREEN_HEIGHT - 350, UI_WIDTH - 20, 120, self.font_small)

    def _load_sprites(self):
        """Carga las imágenes para los animales."""
        sprites = {}
        animal_sprites = {
            "Conejo": "conejo.png", "Raton": "raton.png",
            "Leopardo": "leopardo.png", "Gato": "gato.png",
            "Cerdo": "cerdo.png", "Mono": "mono.png"
        }
        try:
            for name, filename in animal_sprites.items():
                sprites[name] = pygame.transform.scale(pygame.image.load(f"assets/{filename}"), (15, 15))
            return sprites
        except pygame.error as e:
            print(f"\n--- ADVERTENCIA: No se encontraron los sprites ---")
            print(f"Error: {e}.")
            print("La simulación usará círculos de colores en lugar de imágenes.")
            print("Para usar sprites, crea una carpeta 'assets' y coloca dentro los archivos .png de los animales (conejo.png, gato.png, etc.).\n")
            return None

    def _load_terrain_textures(self):
        """Carga las texturas para los diferentes tipos de terreno."""
        textures = {}
        texture_files = {
            "fondo": "textura_fondo.png",
            "selva": "textura_selva.png",
            "pradera": "textura_pradera.png",
            "montana": "textura_montana.png",
            "santuario": "textura_santuario.png"
        }
        for name, filename in texture_files.items():
            try:
                textures[name] = pygame.image.load(f"assets/{filename}").convert()
            except (pygame.error, FileNotFoundError):
                print(f"Advertencia: No se encontró la textura '{filename}'. Se usará un color sólido.")
                textures[name] = None
        return textures


    def _load_water_textures(self):
        """Carga las texturas animadas para el agua (fondo_agua0.png, fondo_agua1.png, etc.)."""
        texturas = []
        i = 0
        while True:
            try:
                ruta = f"assets/fondo_agua{i}.png"
                texturas.append(pygame.image.load(ruta).convert())
                i += 1
            except (pygame.error, FileNotFoundError):
                # Si no se encuentra el archivo, se asume que no hay más texturas.
                break
        if not texturas:
            print("Advertencia: No se encontraron texturas de agua (ej: assets/fondo_agua0.png). Se usará un color sólido.")
        return texturas


    def _create_buttons(self):
        """Crea los botones de la interfaz."""
        buttons = {}
        btn_width, btn_height = 120, 30
        col1_x = SIM_WIDTH + 20
        col2_x = SIM_WIDTH + 150
        
        # Botones de control de velocidad
        control_y = SCREEN_HEIGHT - 220
        buttons["pause_resume"] = Button(SIM_WIDTH + 10, control_y, 120, 35, "Pausa/Reanudar", COLOR_BUTTON, COLOR_TEXT)
        buttons["speed_1x"] = Button(SIM_WIDTH + 140, control_y, 45, 35, "x1", COLOR_BUTTON, COLOR_TEXT)
        buttons["speed_2x"] = Button(SIM_WIDTH + 195, control_y, 45, 35, "x2", COLOR_BUTTON, COLOR_TEXT)
        buttons["speed_5x"] = Button(SIM_WIDTH + 250, control_y, 45, 35, "x5", COLOR_BUTTON, COLOR_TEXT)
        
        # Botones para añadir animales
        buttons["add_conejo"] = Button(col1_x, SCREEN_HEIGHT - 175, btn_width, btn_height, "Añadir Conejo", COLOR_HERBIVORO, (0,0,0))
        buttons["add_raton"] = Button(col2_x, SCREEN_HEIGHT - 175, btn_width, btn_height, "Añadir Ratón", COLOR_HERBIVORO, (0,0,0))
        buttons["add_leopardo"] = Button(col1_x, SCREEN_HEIGHT - 135, btn_width, btn_height, "Añadir Leopardo", COLOR_CARNIVORO, COLOR_TEXT)
        buttons["add_gato"] = Button(col2_x, SCREEN_HEIGHT - 135, btn_width, btn_height, "Añadir Gato", COLOR_CARNIVORO, COLOR_TEXT)
        buttons["add_cerdo"] = Button(col1_x, SCREEN_HEIGHT - 95, btn_width, btn_height, "Añadir Cerdo", COLOR_OMNIVORO, COLOR_TEXT)
        buttons["add_mono"] = Button(col2_x, SCREEN_HEIGHT - 95, btn_width, btn_height, "Añadir Mono", COLOR_OMNIVORO, COLOR_TEXT)

        # Botones de guardado, carga y música
        buttons["save"] = Button(SIM_WIDTH + 10, SCREEN_HEIGHT - 40, 120, 30, "Guardar", (0, 100, 0), COLOR_TEXT)
        buttons["load"] = Button(SIM_WIDTH + 140, SCREEN_HEIGHT - 40, 120, 30, "Cargar", (100, 100, 0), COLOR_TEXT)
        music_text = "Música: ON" if getattr(self, 'music_playing', False) else "Música: OFF"
        buttons["music"] = Button(SIM_WIDTH + 270, SCREEN_HEIGHT - 40, 120, 30, music_text, (80, 80, 80), COLOR_TEXT)

        return buttons

    def _draw_text(self, text, font, color, surface, x, y):
        textobj = font.render(text, 1, color)
        textrect = textobj.get_rect()
        textrect.topleft = (x, y)
        surface.blit(textobj, textrect)

    def _draw_tiled_texture(self, surface, texture, rect):
        """Rellena un rectángulo con una textura de forma repetida (tiling)."""
        if not texture:
            return
        tex_w, tex_h = texture.get_size()
        for y in range(rect.top, rect.bottom, tex_h):
            for x in range(rect.left, rect.right, tex_w):
                surface.blit(texture, (x, y))

    def _update_water_animation(self):
        """Actualiza el frame de la animación del agua basado en el tiempo."""
        if not self.agua_texturas:
            return
        current_time = pygame.time.get_ticks()
        time_per_frame = self.tiempo_animacion_agua
        if current_time - self.ultimo_cambio_agua > time_per_frame:
            self.ultimo_cambio_agua = current_time
            self.agua_frame_actual = (self.agua_frame_actual + 1) % len(self.agua_texturas)

    def draw_simulation(self, ecosistema, logs, sim_over, animal_seleccionado):
        # 1. Dibujar fondos
        self.screen.fill(COLOR_BACKGROUND)
        pygame.draw.rect(self.screen, COLOR_SIM_AREA, (0, 0, SIM_WIDTH, SCREEN_HEIGHT))
        if self.terrain_textures.get("fondo"):
            self._draw_tiled_texture(self.screen, self.terrain_textures["fondo"], pygame.Rect(0, 0, SIM_WIDTH, SCREEN_HEIGHT))

        # Actualizar animación del agua
        self._update_water_animation()

        # Dibujar terreno
        for selva in ecosistema.terreno["selvas"]:
            if self.terrain_textures.get("selva"):
                self._draw_tiled_texture(self.screen, self.terrain_textures["selva"], selva.rect)
            else:
                pygame.draw.rect(self.screen, COLOR_SELVA, selva.rect)
        for pradera in ecosistema.terreno["praderas"]:
            if self.terrain_textures.get("pradera"):
                self._draw_tiled_texture(self.screen, self.terrain_textures["pradera"], pradera.rect)
            else:
                pygame.draw.rect(self.screen, COLOR_PRADERA, pradera.rect)
        for montana in ecosistema.terreno["montanas"]:
            if self.terrain_textures.get("montana"):
                self._draw_tiled_texture(self.screen, self.terrain_textures["montana"], montana.rect)
            else:
                pygame.draw.rect(self.screen, COLOR_MONTANA, montana.rect)
        for rio in ecosistema.terreno["rios"]:
            if self.agua_texturas:
                self._draw_tiled_texture(self.screen, self.agua_texturas[self.agua_frame_actual], rio.rect)
            else:
                pygame.draw.rect(self.screen, COLOR_RIO, rio.rect) # Fallback a color sólido
        for santuario in ecosistema.terreno["santuarios"]:
            if self.terrain_textures.get("santuario"):
                self._draw_tiled_texture(self.screen, self.terrain_textures["santuario"], santuario.rect)
            else:
                pygame.draw.rect(self.screen, COLOR_SANTUARIO, santuario.rect)

        # Dibujar carcasas
        for carcasa in ecosistema.recursos["carcasas"]:
            # La carcasa se hace más transparente a medida que se descompone
            alpha = max(0, 255 - carcasa.dias_descomposicion * 50)
            temp_surface = pygame.Surface((10, 10), pygame.SRCALPHA)
            pygame.draw.circle(temp_surface, COLOR_CARCASA + (alpha,), (5, 5), 5)
            self.screen.blit(temp_surface, (carcasa.x - 5, carcasa.y - 5))


        # 2. Dibujar animales
        if self.sprites:
            for animal in ecosistema.animales:
                sprite_pos_x = animal.x - 7
                sprite_pos_y = animal.y - 7

                # Dibujar sprite del animal
                sprite = self.sprites.get(animal.__class__.__name__)
                if sprite:
                    self.screen.blit(sprite, (sprite_pos_x, sprite_pos_y))
                
                # --- Dibujar Indicadores Visuales ---
                bar_width = 15
                bar_height = 4
                bar_x = sprite_pos_x
                bar_y = sprite_pos_y - bar_height - 2

                # Barra de energía
                energia_percent = animal.energia / animal.genes['max_energia']
                pygame.draw.rect(self.screen, (211, 211, 211), (bar_x, bar_y, bar_width, bar_height)) # Fondo gris claro
                pygame.draw.rect(self.screen, (0, 255, 0), (bar_x, bar_y, bar_width * energia_percent, bar_height)) # Barra verde

                # Indicador de sed (si tiene más de 80 de sed)
                if animal._sed > 80:
                    pygame.draw.circle(self.screen, COLOR_RIO, (int(sprite_pos_x + bar_width + 4), int(sprite_pos_y + 4)), 3)

                # Indicador de reproducción
                if animal.energia > ENERGIA_REPRODUCCION and animal.edad > EDAD_ADULTA:
                    pygame.draw.circle(self.screen, COLOR_HEART, (int(sprite_pos_x - 4), int(sprite_pos_y + 4)), 3)

        else: # Fallback a círculos si no hay sprites
            for animal in ecosistema.animales:
                # Nota: Los indicadores no se dibujarán en modo fallback para simplificar.
                color = (0,0,0) # Color por defecto si no es de un tipo conocido
                if isinstance(animal, Herbivoro): color = COLOR_HERBIVORO # Esto incluye Conejo, Raton
                elif isinstance(animal, Carnivoro): color = COLOR_CARNIVORO # Esto incluye Leopardo, Gato
                elif isinstance(animal, Omnivoro): color = COLOR_OMNIVORO
                
                # Usar el color genérico para las clases base si aún se usan
                pygame.draw.circle(self.screen, color, (int(animal.x), int(animal.y)), 7)
        
        # Resaltar animal seleccionado
        if animal_seleccionado:
            pygame.draw.circle(self.screen, (255, 255, 0), (animal_seleccionado.x, animal_seleccionado.y), 10, 2)

        # 3. Dibujar UI (panel de texto)
        ui_x = SIM_WIDTH + 10
        self._draw_text(f"DÍA: {ecosistema.dia_total}", self.font_header, COLOR_TEXT, self.screen, ui_x, 5)
        
        # Estado del ecosistema
        y_offset = 35
        self._draw_text(f"Estación: {ecosistema.estacion_actual}", self.font_normal, COLOR_TEXT, self.screen, ui_x, y_offset)
        y_offset += 20
        self._draw_text(f"Clima: {ecosistema.clima_actual}", self.font_normal, COLOR_TEXT, self.screen, ui_x, y_offset)
        
        # Panel de información / animal seleccionado
        y_offset = 80
        self._draw_text("--- INFO ---", self.font_normal, COLOR_TEXT, self.screen, ui_x, y_offset)
        y_offset += 25
        if animal_seleccionado:
            self._draw_text(f"Nombre: {animal_seleccionado.nombre}", self.font_small, COLOR_TEXT, self.screen, ui_x, y_offset)
            y_offset += 15
            self._draw_text(f"Tipo: {animal_seleccionado.__class__.__name__}", self.font_small, COLOR_TEXT, self.screen, ui_x, y_offset)
            y_offset += 15
            self._draw_text(f"Energía: {animal_seleccionado.energia}/{animal_seleccionado.genes['max_energia']}", self.font_small, COLOR_TEXT, self.screen, ui_x, y_offset)
            y_offset += 15
            self._draw_text(f"Sed: {animal_seleccionado._sed}", self.font_small, COLOR_TEXT, self.screen, ui_x, y_offset)
            y_offset += 15
            self._draw_text(f"Edad: {animal_seleccionado.edad}", self.font_small, COLOR_TEXT, self.screen, ui_x, y_offset)
            y_offset += 20
            self._draw_text(f"GENES:", self.font_tiny, COLOR_TEXT, self.screen, ui_x, y_offset)
            y_offset += 12
            self._draw_text(f" Visión: {animal_seleccionado.genes['rango_vision']}", self.font_tiny, COLOR_TEXT, self.screen, ui_x, y_offset)
        else:
            self._draw_text(f"Animales: {len(ecosistema.animales)}", self.font_normal, COLOR_TEXT, self.screen, ui_x, y_offset)
            y_offset += 20
            self._draw_text(f"Hierba: {ecosistema.recursos['hierba']}", self.font_normal, COLOR_TEXT, self.screen, ui_x, y_offset)
            y_offset += 20
            bayas_totales = sum(s.bayas for s in ecosistema.terreno["selvas"])
            self._draw_text(f"Bayas: {bayas_totales}", self.font_normal, COLOR_TEXT, self.screen, ui_x, y_offset)
            y_offset += 20
            self._draw_text("Haz clic en un animal", self.font_small, COLOR_TEXT, self.screen, ui_x, y_offset)
            y_offset += 15
            self._draw_text("para ver sus detalles.", self.font_small, COLOR_TEXT, self.screen, ui_x, y_offset)

        # Dibujar gráfico
        self.graph.draw(self.screen)

        # 4. Dibujar botones
        if not sim_over:
            for button in self.buttons.values():
                button.draw(self.screen)
        
        # Instrucciones
        self._draw_text("ESC para salir", self.font_small, COLOR_TEXT, self.screen, 10, SCREEN_HEIGHT - 25)
        
        # 4. Actualizar la pantalla
        pygame.display.flip()

    def close(self):
        # Detener música si está sonando
        try:
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
        except Exception:
            pass
        pygame.quit()

    def toggle_music(self):
        """Alterna la reproducción de la música de fondo ON/OFF.

        Actualiza también el texto del botón `music`.
        """
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
                # Si no está sonando, intentamos reanudar; si falla, intentamos play desde el inicio
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
    """Controla el flujo de la simulación, conectando el Modelo y la Vista."""
    def __init__(self, dias_simulacion: int):
        self.ecosistema = Ecosistema()
        self.view = PygameView()
        self.dias_simulacion = dias_simulacion
        self.logs = ["¡Bienvenido! Pulsa 'Siguiente Día' para empezar."]
        self.animal_seleccionado = None
        self.paused = True # Empezar en pausa
        self.sim_speed_multiplier = 1
        self.base_time_per_day = 500 # ms por día a velocidad x1
        self.last_update_time = 0

    def _poblar_ecosistema(self):
        """Método privado para añadir los animales iniciales."""
        self.ecosistema.agregar_animal(Conejo)
        self.ecosistema.agregar_animal(Raton)
        self.ecosistema.agregar_animal(Leopardo)
        self.ecosistema.agregar_animal(Gato)
        self.ecosistema.agregar_animal(Cerdo)
        self.ecosistema.agregar_animal(Mono)

    def _avanzar_dia(self):
        """Avanza un día en la simulación."""
        self.logs = self.ecosistema.simular_dia()
        
        # Actualizar gráfico
        poblaciones = (
            sum(1 for a in self.ecosistema.animales if isinstance(a, Herbivoro)),
            sum(1 for a in self.ecosistema.animales if isinstance(a, Carnivoro)),
            sum(1 for a in self.ecosistema.animales if isinstance(a, Omnivoro))
        )
        self.view.graph.update(poblaciones)

        if self.ecosistema.dia_total >= self.dias_simulacion or not self.ecosistema.animales:
            self.logs.append("--- SIMULACIÓN FINALIZADA ---")
            return True # La simulación ha terminado
        return False # La simulación continúa


    def run(self):
        """Bucle principal de la simulación con Pygame."""
        self._poblar_ecosistema()
        
        running = True
        sim_over = False
        self.last_update_time = pygame.time.get_ticks()

        while running:
            # --- Lógica de Avance Automático ---
            if not self.paused and not sim_over:
                current_time = pygame.time.get_ticks()
                time_per_day = self.base_time_per_day / self.sim_speed_multiplier if self.sim_speed_multiplier > 0 else float('inf')
                if current_time - self.last_update_time > time_per_day:
                    sim_over = self._avanzar_dia()
                    self.last_update_time = current_time
                    if self.animal_seleccionado and not self.animal_seleccionado.esta_vivo:
                        self.animal_seleccionado = None

            # Manejo de eventos de Pygame
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_m:
                        # Atajo de teclado: tecla M para alternar música
                        try:
                            self.view.toggle_music()
                        except Exception as e:
                            print(f"Error al alternar música desde teclado: {e}")
                if event.type == pygame.MOUSEBUTTONDOWN and not sim_over:
                    pos = pygame.mouse.get_pos()
                    # Controles de simulación
                    if self.view.buttons["add_conejo"].rect.collidepoint(pos):
                        self.ecosistema.agregar_animal(Conejo)
                    elif self.view.buttons["add_raton"].rect.collidepoint(pos):
                        self.ecosistema.agregar_animal(Raton)
                    elif self.view.buttons["add_leopardo"].rect.collidepoint(pos):
                        self.ecosistema.agregar_animal(Leopardo)
                    elif self.view.buttons["add_gato"].rect.collidepoint(pos):
                        self.ecosistema.agregar_animal(Gato)
                    elif self.view.buttons["add_cerdo"].rect.collidepoint(pos):
                        self.ecosistema.agregar_animal(Cerdo)
                    elif self.view.buttons["add_mono"].rect.collidepoint(pos):
                        self.ecosistema.agregar_animal(Mono)
                    elif self.view.buttons["save"].rect.collidepoint(pos):
                        self.ecosistema.guardar_estado()
                        self.logs.append("¡Partida guardada!")
                    elif self.view.buttons["load"].rect.collidepoint(pos):
                        try:
                            self.ecosistema.cargar_estado()
                            self.view.graph.history = [] # Resetear gráfico
                            self.logs.append("¡Partida cargada!")
                        except FileNotFoundError:
                            self.logs.append("¡No se encontró guardado!")
                    elif self.view.buttons["music"].rect.collidepoint(pos):
                        # Alternar la música de fondo
                        try:
                            self.view.toggle_music()
                        except Exception as e:
                            print(f"Error al alternar música desde controlador: {e}")
                    elif self.view.buttons["pause_resume"].rect.collidepoint(pos):
                        self.paused = not self.paused
                    elif self.view.buttons["speed_1x"].rect.collidepoint(pos):
                        self.sim_speed_multiplier = 1
                    elif self.view.buttons["speed_2x"].rect.collidepoint(pos):
                        self.sim_speed_multiplier = 2
                    elif self.view.buttons["speed_5x"].rect.collidepoint(pos):
                        self.sim_speed_multiplier = 5
                    else:
                        # Comprobar si se hizo clic en un animal
                        self.animal_seleccionado = None
                        for animal in reversed(self.ecosistema.animales):
                            dist = (animal.x - pos[0])**2 + (animal.y - pos[1])**2
                            if dist < 10**2: # Si el clic está dentro del radio del animal
                                self.animal_seleccionado = animal
                                break

            # Dibujar todo
            self.view.draw_simulation(self.ecosistema, self.logs, sim_over, self.animal_seleccionado)

        self.view.close()

# --- Ejecución Principal ---

def main():
    """Función principal para ejecutar la simulación."""
    controlador = SimulationController(dias_simulacion=200) # Puedes ajustar el total de días
    controlador.run()

if __name__ == "__main__":
    main()