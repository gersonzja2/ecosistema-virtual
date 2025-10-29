import pygame
import time
import random
from model import Ecosistema, Herbivoro, Carnivoro, Omnivoro, Animal
from graph import PopulationGraph



COLOR_BACKGROUND = (22, 160, 133)
COLOR_SIM_AREA = (46, 204, 113)
COLOR_HERBIVORO = (255, 255, 255) # Blanco
COLOR_CARNIVORO = (231, 76, 60)   # Rojo
COLOR_OMNIVORO = (52, 152, 219)  # Azul
COLOR_TEXT = (236, 240, 241)
COLOR_MONTANA = (149, 165, 166) # Gris
COLOR_RIO = (41, 128, 185)     # Azul oscwadwduro
COLOR_SELVA = (39, 174, 96)     # Verde oscuro
COLOR_BUTTON = (26, 188, 156)

# --- Clase para Botones ---
sorted
class Button:
    """Clase para crear botones clickeables en Pygame."""
    def __init__(self, x, y, width, height, text, color, text_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.text_color = text_color
        self.font = pygame.font.SysFont("helvetica", 20)

    def draw(self, surfac):
        pygame.draw.rect(urface, self.color, self.rect, border_radius=8)
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

# --- Clase de la Vista (GUI con Pygame) ---

class PygameView:
    """Se encarga de mostrar la simulación en una ventana con Pygame."""
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Simulador de Ecosistema Virtual")
        self.font_header = pygame.font.SysFont("helvetica", 24, bold=True)
        self.font_normal = pygame.font.SysFont("consola", 16)
        self.font_small = pygame.font.SysFont("consola", 14)
        self.font_tiny = pygame.font.SysFont("consola", 12)
        self.buttons = self._create_buttons()
        self.sprites = self._load_sprites()
        self.graph = PopulationGraph(SIM_WIDTH + 10, SCREEN_HEIGHT - 350, UI_WIDTH - 20, 120, self.font_small)

    def _load_sprites(self):
        """Carga las imágenes para los animales."""
        try:
            return {
                "Herbivoro": pygame.transform.scale(pygame.image.load("assets/herbivoro.png"), (15, 15)),
                "Carnivoro": pygame.transform.scale(pygame.image.load("assets/carnivoro.png"), (15, 15)),
                "Omnivoro": pygame.transform.scale(pygame.image.load("assets/omnivoro.png"), (15, 15)),
            }
        except pygame.error as e:
            print(f"Error al cargar sprites: {e}. Asegúrate de tener la carpeta 'assets' con las imágenes.")
            return None

    def _create_buttons(self):
        """Crea los botones de la interfaz."""
        buttons = {}
        btn_width, btn_height = 180, 35
        btn_x = SIM_WIDTH + (UI_WIDTH - btn_width) / 2
        buttons["next_day"] = Button(btn_x, SCREEN_HEIGHT - 220, btn_width, btn_height, "Siguiente Día", COLOR_BUTTON, COLOR_TEXT)
        buttons["add_herb"] = Button(btn_x, SCREEN_HEIGHT - 175, btn_width, btn_height, "Añadir Herbívoro", COLOR_HERBIVORO, (0,0,0))
        buttons["add_carn"] = Button(btn_x, SCREEN_HEIGHT - 130, btn_width, btn_height, "Añadir Carnívoro", COLOR_CARNIVORO, COLOR_TEXT)
        buttons["add_omni"] = Button(btn_x, SCREEN_HEIGHT - 85, btn_width, btn_height, "Añadir Omnívoro", COLOR_OMNIVORO, COLOR_TEXT)
        buttons["save"] = Button(SIM_WIDTH + 10, SCREEN_HEIGHT - 40, 85, 30, "Guardar", (0, 100, 0), COLOR_TEXT)
        buttons["load"] = Button(SIM_WIDTH + 105, SCREEN_HEIGHT - 40, 85, 30, "Cargar", (100, 100, 0), COLOR_TEXT)
        return buttons

    def _draw_text(self, text, font, color, surface, x, y):
        textobj = font.render(text, 1, color)
        textrect = textobj.get_rect()
        textrect.topleft = (x, y)
        surface.blit(textobj, textrect)

    def draw_simulation(self, ecosistema, logs, sim_over, animal_seleccionado):
        # 1. Dibujar fondos
        self.screen.fill(COLOR_BACKGROUND)
        pygame.draw.rect(self.screen, COLOR_SIM_AREA, (0, 0, SIM_WIDTH, SCREEN_HEIGHT))

        # Dibujar terreno
        for selva in ecosistema.terreno["selvas"]:
            pygame.draw.rect(self.screen, COLOR_SELVA, selva.rect)
        for montana in ecosistema.terreno["montanas"]:
            pygame.draw.rect(self.screen, COLOR_MONTANA, montana.rect)
        for rio in ecosistema.terreno["rios"]:
            pygame.draw.rect(self.screen, COLOR_RIO, rio.rect)


        # 2. Dibujar animales
        if self.sprites:
            for animal in ecosistema.animales:
                sprite = self.sprites.get(animal.__class__.__name__)
                if sprite:
                    self.screen.blit(sprite, (animal.x - 7, animal.y - 7))
        else: # Fallback a círculos si no hay sprites
            for animal in ecosistema.animales:
                color = COLOR_HERBIVORO
                if isinstance(animal, Carnivoro): color = COLOR_CARNIVORO
                elif isinstance(animal, Omnivoro): color = COLOR_OMNIVORO
                pygame.draw.circle(self.screen, color, (animal.x, animal.y), 7)
        
        # Resaltar animal seleccionado
        if animal_seleccionado:
            pygame.draw.circle(self.screen, (255, 255, 0), (animal_seleccionado.x, animal_seleccionado.y), 10, 2)

        # 3. Dibujar UI (panel de texto)
        ui_x = SIM_WIDTH + 10
        self._draw_text(f"DÍA: {ecosistema.dia_total}", self.font_header, COLOR_TEXT, self.screen, ui_x, 10)
        
        # Estado del ecosistema
        y_offset = 45
        self._draw_text(f"Estación: {ecosistema.estacion_actual}", self.font_normal, COLOR_TEXT, self.screen, ui_x, y_offset)
        y_offset += 20
        self._draw_text(f"Clima: {ecosistema.clima_actual}", self.font_normal, COLOR_TEXT, self.screen, ui_x, y_offset)
        
        # Panel de información / animal seleccionado
        y_offset = 90
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
        pygame.quit()

class SimulationController:
    """Controla el flujo de la simulación, conectando el Modelo y la Vista."""
    def __init__(self, dias_simulacion: int):
        self.ecosistema = Ecosistema()
        self.view = PygameView()
        self.dias_simulacion = dias_simulacion
        self.logs = ["¡Bienvenido! Pulsa 'Siguiente Día' para empezar."]
        self.animal_seleccionado = None

    def _poblar_ecosistema(self):
        """Método privado para añadir los animales iniciales."""
        self.ecosistema.agregar_animal(Herbivoro, "Conejo 1")
        self.ecosistema.agregar_animal(Herbivoro, "Ciervo 1")
        self.ecosistema.agregar_animal(Carnivoro, "Lobo 1")
        self.ecosistema.agregar_animal(Omnivoro, "Oso 1")
        self.ecosistema.agregar_animal(Herbivoro, "Conejo 2")

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
        while running:
            # Manejo de eventos de Pygame
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                if event.type == pygame.MOUSEBUTTONDOWN and not sim_over:
                    pos = pygame.mouse.get_pos()
                    if self.view.buttons["next_day"].rect.collidepoint(pos):
                        sim_over = self._avanzar_dia()
                        if self.animal_seleccionado and not self.animal_seleccionado.esta_vivo:
                            self.animal_seleccionado = None
                    elif self.view.buttons["add_herb"].rect.collidepoint(pos):
                        self.ecosistema.agregar_animal(Herbivoro)
                    elif self.view.buttons["add_carn"].rect.collidepoint(pos):
                        self.ecosistema.agregar_animal(Carnivoro)
                    elif self.view.buttons["add_omni"].rect.collidepoint(pos):
                        self.ecosistema.agregar_animal(Omnivoro)
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