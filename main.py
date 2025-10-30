import pygame
import random
from model import Ecosistema, Herbivoro, Carnivoro, Omnivoro, ENERGIA_REPRODUCCION, EDAD_ADULTA, Conejo, Raton, Leopardo, Gato, Cerdo, Mono, Cabra, CELL_SIZE, MAX_HIERBA_PRADERA
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
COLOR_PEZ = (0, 191, 255) # Azul brillante para los peces
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
        # Intentar cargar y reproducir la música de fondo
        self.music_playing = False
        try:
            import os
            music_files = [f for f in os.listdir("assets") if f.endswith(".mp3")]
            if music_files:
                music_path = os.path.join("assets", random.choice(music_files))
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.set_volume(0.15)  # Volumen por defecto (0.0 - 1.0)
                pygame.mixer.music.play(-1)  # Repetir indefinidamente
                self.music_playing = True
            else:
                print("No se encontraron archivos .mp3 en la carpeta 'assets'. La música no se reproducirá.")
        except Exception as e:
            # No abortamos la ejecución si falla la música
            print(f"No se pudo cargar o reproducir la música de fondo: {e}")
        # Crear botones después de conocer el estado de la música para mostrar el texto correcto
        self.buttons = self._create_buttons()
        self.graph = PopulationGraph(SIM_WIDTH + 10, SCREEN_HEIGHT - 350, UI_WIDTH - 20, 120, self.font_small)
        self.mouse_pos = None # Para almacenar la posición del ratón

    def _load_sprites(self):
        """Carga las imágenes para los animales."""
        sprites = {}
        sprite_definitions = {
            "Conejo": {"file": "conejo.png", "size": (15, 15)},
            "Raton": {"file": "raton.png", "size": (15, 15)},
            "Leopardo": {"file": "leopardo.png", "size": (15, 15)},
            "Gato": {"file": "gato.png", "size": (15, 15)},
            "Cabra": {"file": "cabra.png", "size": (15, 15)},
            "Cerdo": {"file": "cerdo.png", "size": (15, 15)},
            "Mono": {"file": "mono.png", "size": (15, 15)},
            "Pez": {"file": "pez.png", "size": (10, 10)},
            "arbol": {"file": "arbol_medium.png", "size": (30, 30)},
            "planta": {"file": "planta_small.png", "size": (12, 12)}
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
        """Crea los botones de la interfaz."""
        buttons = {}
        btn_width, btn_height = 110, 30
        col1_x = SIM_WIDTH + 15
        col2_x = SIM_WIDTH + 135
        col3_x = SIM_WIDTH + 255
        
        # Botones de control de velocidad
        control_y = SCREEN_HEIGHT - 225
        buttons["pause_resume"] = Button(SIM_WIDTH + 10, control_y, 130, 35, "Pausa/Reanudar", COLOR_BUTTON, COLOR_TEXT)
        buttons["next_day"] = Button(SIM_WIDTH + 150, control_y, 130, 35, "Adelantar Día", COLOR_BUTTON, COLOR_TEXT)
        
        buttons["speed_down"] = Button(SIM_WIDTH + 290, control_y, 35, 35, "-", COLOR_BUTTON, COLOR_TEXT)
        buttons["speed_up"] = Button(SIM_WIDTH + 380, control_y, 35, 35, "+", COLOR_BUTTON, COLOR_TEXT)
        # Botones para añadir animales
        buttons["add_conejo"] = Button(col1_x, SCREEN_HEIGHT - 175, btn_width, btn_height, "Añadir Conejo", COLOR_HERBIVORO, (0,0,0))
        buttons["add_raton"] = Button(col2_x, SCREEN_HEIGHT - 175, btn_width, btn_height, "Añadir Ratón", COLOR_HERBIVORO, (0,0,0))
        buttons["add_cabra"] = Button(col3_x, SCREEN_HEIGHT - 175, btn_width, btn_height, "Añadir Cabra", COLOR_HERBIVORO, (0,0,0))
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
        # Sombra del texto para mejorar la legibilidad
        text_shadow = font.render(text, 1, (0, 0, 0))
        surface.blit(text_shadow, (x + 1, y + 1))
        # Texto principal
        textobj = font.render(text, 1, color)
        textrect = textobj.get_rect()
        textrect.topleft = (x, y)
        surface.blit(textobj, textrect)

    def _draw_hierba(self, ecosistema):
        """Dibuja la capa de hierba."""
        for gx in range(ecosistema.grid_width):
            for gy in range(ecosistema.grid_height):
                nivel_hierba = ecosistema.grid_hierba[gx][gy]
                if nivel_hierba > 0:
                    max_val = MAX_HIERBA_PRADERA
                    intensidad = min(1.0, nivel_hierba / max_val)
                    color_base = list(COLOR_SIM_AREA)
                    color_hierba = (34, 139, 34) # Verde bosque
                    color_final = tuple([int(color_base[i] * (1 - intensidad) + color_hierba[i] * intensidad) for i in range(3)])
                    pygame.draw.rect(self.screen, color_final, (gx * CELL_SIZE, gy * CELL_SIZE, CELL_SIZE, CELL_SIZE))
    
    def _draw_terreno(self, ecosistema):
        """Dibuja los elementos del terreno como selvas y ríos."""
        # --- Suavizado de bordes (aura) ---
        for selva in ecosistema.terreno["selvas"]:
            aura_rect = selva.rect.inflate(10, 10)
            s = pygame.Surface(aura_rect.size, pygame.SRCALPHA)
            s.fill(COLOR_SELVA + (30,)) # Color con baja opacidad
            self.screen.blit(s, aura_rect.topleft)
        for rio in ecosistema.terreno["rios"]:
            aura_rect = rio.rect.inflate(10, 10)
            s = pygame.Surface(aura_rect.size, pygame.SRCALPHA)
            s.fill(COLOR_RIO + (50,))
            self.screen.blit(s, aura_rect.topleft)

        # --- Dibujo principal del terreno ---
        for selva in ecosistema.terreno["selvas"]:
            pygame.draw.rect(self.screen, COLOR_SELVA, selva.rect)
        for rio in ecosistema.terreno["rios"]:
            pygame.draw.rect(self.screen, tuple(max(0, c-40) for c in COLOR_RIO), rio.rect, 3) # Borde oscuro
            pygame.draw.rect(self.screen, COLOR_RIO, rio.rect)

    def _draw_decoraciones(self, ecosistema):
        """Dibuja los elementos decorativos como árboles y plantas."""
        if self.sprites and "arbol" in self.sprites:
            for x, y in ecosistema.terreno["arboles"]:
                sprite = self.sprites["arbol"]
                self.screen.blit(sprite, (x - sprite.get_width() // 2, y - sprite.get_height() // 2))
        if self.sprites and "planta" in self.sprites:
            for x, y in ecosistema.terreno["plantas"]:
                sprite = self.sprites["planta"]
                self.screen.blit(sprite, (x - sprite.get_width() // 2, y - sprite.get_height() // 2))
    
    def _draw_recursos(self, ecosistema):
        """Dibuja recursos como peces y carcasas."""
        pez_sprite = self.sprites.get("Pez") if self.sprites else None
        for rio in ecosistema.terreno["rios"]:
            for pez in rio.peces:
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
        """Dibuja los animales y sus indicadores."""
        if self.sprites:
            for animal in ecosistema.animales:
                sprite_pos_x = animal.x - 7
                sprite_pos_y = animal.y - 7
                sprite = self.sprites.get(animal.__class__.__name__)
                if sprite:
                    self.screen.blit(sprite, (sprite_pos_x, sprite_pos_y))
                
                bar_width = 15
                bar_height = 4
                bar_x = sprite_pos_x
                bar_y = sprite_pos_y - bar_height - 2

                # --- Corrección del bug de la barra de vida ---
                # Asegurarse de que la energía no sea negativa para el cálculo del porcentaje
                # y evitar división por cero si max_energia fuera 0.
                max_energia = animal.genes.get('max_energia', 1) or 1
                energia_percent = max(0, animal.energia) / max_energia
                pygame.draw.rect(self.screen, (0,0,0), (bar_x-1, bar_y-1, bar_width+2, bar_height+2)) # Borde
                pygame.draw.rect(self.screen, (90, 90, 90), (bar_x, bar_y, bar_width, bar_height))
                pygame.draw.rect(self.screen, (0, 255, 0), (bar_x, bar_y, bar_width * energia_percent, bar_height))

                if animal._sed > 80:
                    pygame.draw.circle(self.screen, COLOR_RIO, (int(sprite_pos_x + bar_width + 4), int(sprite_pos_y + 4)), 3)

                if animal.energia > ENERGIA_REPRODUCCION and animal.edad > EDAD_ADULTA:
                    pygame.draw.circle(self.screen, COLOR_HEART, (int(sprite_pos_x - 4), int(sprite_pos_y + 4)), 3)

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
        """Dibuja el panel de información y estadísticas."""
        ui_x = SIM_WIDTH + 10
        hora_str = str(ecosistema.hora_actual).zfill(2)
        self._draw_text(f"DÍA: {ecosistema.dia_total} - {hora_str}:00", self.font_header, COLOR_TEXT, self.screen, ui_x, 5)

        y_offset = 35
        self._draw_text(f"Estación: {ecosistema.estacion_actual}", self.font_normal, COLOR_TEXT, self.screen, ui_x, y_offset)
        y_offset += 20
        self._draw_text(f"Clima: {ecosistema.clima_actual}", self.font_normal, COLOR_TEXT, self.screen, ui_x, y_offset)
        
        speed_text = f"Velocidad: x{sim_speed}"
        self._draw_text(speed_text, self.font_normal, COLOR_TEXT, self.screen, SIM_WIDTH + 330, SCREEN_HEIGHT - 220)

        y_offset = 80
        self._draw_text("--- INFO ---", self.font_normal, COLOR_TEXT, self.screen, ui_x, y_offset)
        y_offset += 25
        if animal_seleccionado:
            info = [
                f"Nombre: {animal_seleccionado.nombre}",
                f"Tipo: {animal_seleccionado.__class__.__name__}",
                f"Energía: {animal_seleccionado.energia}/{animal_seleccionado.genes['max_energia']}",
                f"Sed: {animal_seleccionado._sed}",
                f"Edad: {animal_seleccionado.edad}"
            ]
            for line in info:
                self._draw_text(line, self.font_small, COLOR_TEXT, self.screen, ui_x, y_offset)
                y_offset += 15
            y_offset += 20
            self._draw_text(f"GENES:", self.font_tiny, COLOR_TEXT, self.screen, ui_x, y_offset)
            y_offset += 12
            self._draw_text(f" Visión: {animal_seleccionado.genes['rango_vision']}", self.font_tiny, COLOR_TEXT, self.screen, ui_x, y_offset)
        else:
            self._draw_text(f"Animales: {len(ecosistema.animales)}", self.font_normal, COLOR_TEXT, self.screen, ui_x, y_offset)
            y_offset += 20
            bayas_totales = sum(s.bayas for s in ecosistema.terreno["selvas"])
            self._draw_text(f"Bayas: {bayas_totales}", self.font_normal, COLOR_TEXT, self.screen, ui_x, y_offset)
            y_offset += 20
            peces_totales = sum(len(r.peces) for r in ecosistema.terreno["rios"])
            self._draw_text(f"Peces: {peces_totales}", self.font_normal, COLOR_TEXT, self.screen, ui_x, y_offset)
            y_offset += 20
            self._draw_text("Haz clic en un animal", self.font_small, COLOR_TEXT, self.screen, ui_x, y_offset)
            y_offset += 15
            self._draw_text("para ver sus detalles.", self.font_small, COLOR_TEXT, self.screen, ui_x, y_offset)

        # Dibujar gráfico
        self.graph.draw(self.screen)

    def draw_simulation(self, ecosistema, logs, sim_over, animal_seleccionado, sim_speed):
        # 1. Dibujar fondos y capas base
        self.screen.fill(COLOR_BACKGROUND)
        pygame.draw.rect(self.screen, COLOR_SIM_AREA, (0, 0, SIM_WIDTH, SCREEN_HEIGHT))
        self._draw_hierba(ecosistema)
        self._draw_terreno(ecosistema)

        # 2. Dibujar elementos del ecosistema
        self._draw_decoraciones(ecosistema)
        self._draw_recursos(ecosistema)
        self._draw_animales(ecosistema, animal_seleccionado)

        # 3. Dibujar la interfaz de usuario
        self._draw_ui(ecosistema, animal_seleccionado, sim_speed)
        if not sim_over:
            for button in self.buttons.values():
                button.draw(self.screen)
        
        self._draw_text("ESC para salir", self.font_small, COLOR_TEXT, self.screen, 10, SCREEN_HEIGHT - 25)

        # Mostrar coordenadas del mouse si está dentro del área de simulación
        if self.mouse_pos and self.mouse_pos[0] < SIM_WIDTH:
            coord_text = f"({self.mouse_pos[0]}, {self.mouse_pos[1]})"
            self._draw_text(coord_text, self.font_small, COLOR_TEXT, self.screen, 10, SCREEN_HEIGHT - 45)
        
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
        
        self.speed_levels = [1, 2, 5, 10, 20]
        self.current_speed_index = 0
        self.sim_speed_multiplier = self.speed_levels[self.current_speed_index]
        self.base_time_per_hour = 50 # ms por hora a velocidad x1
        self.last_update_time = 0

        self.holding_next_day = False
        self.next_day_cooldown = 150 # ms entre horas al mantener presionado

    def _poblar_ecosistema(self):
        """Método privado para añadir los animales iniciales."""
        tipos_de_animales = [Conejo, Raton, Cabra, Leopardo, Gato, Cerdo, Mono]
        for tipo in tipos_de_animales:
            for _ in range(10):
                self.ecosistema.agregar_animal(tipo)

    def _avanzar_dia(self):
        """Avanza un día en la simulación."""
        # Un "día" ahora consiste en 24 "horas" de simulación
        for _ in range(24):
            if not self.ecosistema.animales: break # Detener si no hay animales
            self.logs = self.ecosistema.simular_hora()
        
        # self.logs = self.ecosistema.simular_dia() # El método simular_dia ahora hace esto
        
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
    
    def _avanzar_hora(self):
        """Avanza una hora en la simulación."""
        self.logs = self.ecosistema.simular_hora()
        # La actualización del gráfico se hará solo al final del día para no ralentizar
        if self.ecosistema.dia_total >= self.dias_simulacion or not self.ecosistema.animales:
            self.logs.append("--- SIMULACIÓN FINALIZADA ---")
            return True
        return False

    def _increase_speed(self):
        """Aumenta la velocidad de la simulación."""
        self.current_speed_index = min(self.current_speed_index + 1, len(self.speed_levels) - 1)
        self.sim_speed_multiplier = self.speed_levels[self.current_speed_index]

    def _decrease_speed(self):
        """Disminuye la velocidad de la simulación."""
        self.current_speed_index = max(self.current_speed_index - 1, 0)
        self.sim_speed_multiplier = self.speed_levels[self.current_speed_index]

    def _setup_button_actions(self):
        """Asocia los botones con sus funciones correspondientes."""
        self.button_actions = {
            "add_conejo": lambda: self.ecosistema.agregar_animal(Conejo),
            "add_raton": lambda: self.ecosistema.agregar_animal(Raton),
            "add_cabra": lambda: self.ecosistema.agregar_animal(Cabra),
            "add_leopardo": lambda: self.ecosistema.agregar_animal(Leopardo),
            "add_gato": lambda: self.ecosistema.agregar_animal(Gato),
            "add_cerdo": lambda: self.ecosistema.agregar_animal(Cerdo),
            "add_mono": lambda: self.ecosistema.agregar_animal(Mono),
            "save": self._action_save,
            "load": self._action_load,
            "music": self.view.toggle_music,
            "pause_resume": self._action_toggle_pause,
            "speed_up": self._increase_speed,
            "speed_down": self._decrease_speed,
            "next_day": self._action_advance_day
        }

    def _action_save(self): self.ecosistema.guardar_estado(); self.logs.append("¡Partida guardada!")
    def _action_load(self):
        try: self.ecosistema.cargar_estado(); self.view.graph.history = []; self.logs.append("¡Partida cargada!")
        except FileNotFoundError: self.logs.append("¡No se encontró guardado!")
    def _action_toggle_pause(self): self.paused = not self.paused
    def _action_advance_day(self): return self._avanzar_dia() # Devuelve sim_over

    def run(self):
        """Bucle principal de la simulación con Pygame."""
        self._poblar_ecosistema()
        
        running = True
        sim_over = False
        self._setup_button_actions()
        self.last_update_time = pygame.time.get_ticks()

        while running:
            # --- Lógica de Avance Automático ---
            if not self.paused and not sim_over:
                current_time = pygame.time.get_ticks()
                time_per_step = self.base_time_per_hour / self.sim_speed_multiplier if self.sim_speed_multiplier > 0 else float('inf')
                if current_time - self.last_update_time > time_per_step:
                    sim_over = self._avanzar_hora()
                    self.last_update_time = current_time
                    if self.animal_seleccionado and not self.animal_seleccionado.esta_vivo:
                        self.animal_seleccionado = None
            
            # --- Lógica para mantener presionado "Adelantar Día" ---
            if self.holding_next_day and not sim_over:
                current_time = pygame.time.get_ticks()
                if current_time - self.last_update_time > self.next_day_cooldown:
                    sim_over = self._avanzar_hora() # Al mantener presionado, avanza hora por hora
                    self.last_update_time = current_time
                    # Reducir el cooldown para acelerar el avance con el tiempo
                    self.next_day_cooldown = max(50, self.next_day_cooldown - 10)
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
                if event.type == pygame.MOUSEMOTION:
                    self.view.mouse_pos = event.pos
                
                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1: # Botón izquierdo del ratón
                        self.holding_next_day = False
                elif event.type == pygame.MOUSEBUTTONDOWN and not sim_over:
                    pos = pygame.mouse.get_pos()
                    clicked_on_button = False
                    for name, button in self.view.buttons.items():
                        if button.rect.collidepoint(pos):
                            action = self.button_actions.get(name)
                            if action:
                                result = action()
                                if name == "next_day":
                                    sim_over = result
                                    # Lógica especial para next_day
                                    poblaciones = (sum(1 for a in self.ecosistema.animales if isinstance(a, Herbivoro)), sum(1 for a in self.ecosistema.animales if isinstance(a, Carnivoro)), sum(1 for a in self.ecosistema.animales if isinstance(a, Omnivoro)))
                                    self.view.graph.update(poblaciones)
                                    self.last_update_time = pygame.time.get_ticks()
                                    self.holding_next_day = True
                                    self.next_day_cooldown = 250
                            clicked_on_button = True
                            break
                    if not clicked_on_button:
                        # Comprobar si se hizo clic en un animal
                        self.animal_seleccionado = None
                        for animal in reversed(self.ecosistema.animales):
                            dist = (animal.x - pos[0])**2 + (animal.y - pos[1])**2
                            if dist < 10**2: # Si el clic está dentro del radio del animal
                                self.animal_seleccionado = animal
                                break

            # Dibujar todo
            self.view.draw_simulation(self.ecosistema, self.logs, sim_over, self.animal_seleccionado, self.sim_speed_multiplier)

        self.view.close()

# --- Ejecución Principal ---

def main():
    """Función principal para ejecutar la simulación."""
    controlador = SimulationController(dias_simulacion=200) # Puedes ajustar el total de días
    controlador.run()

if __name__ == "__main__":
    main()