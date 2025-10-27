import pygame
import time
import random
from model import Ecosistema, Herbivoro, Carnivoro, Omnivoro

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
COLOR_BUTTON = (26, 188, 156)

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
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Simulador de Ecosistema Virtual")
        self.font_header = pygame.font.SysFont("helvetica", 24, bold=True)
        self.font_normal = pygame.font.SysFont("consola", 16)
        self.font_small = pygame.font.SysFont("consola", 14)
        self.buttons = self._create_buttons()

    def _create_buttons(self):
        """Crea los botones de la interfaz."""
        buttons = {}
        btn_width, btn_height = 160, 40
        btn_x = SIM_WIDTH + (UI_WIDTH - btn_width) / 2
        buttons["next_day"] = Button(btn_x, SCREEN_HEIGHT - 210, btn_width, btn_height, "Siguiente Día", COLOR_BUTTON, COLOR_TEXT)
        buttons["add_herb"] = Button(btn_x, SCREEN_HEIGHT - 160, btn_width, btn_height, "Añadir Herbívoro", COLOR_HERBIVORO, (0,0,0))
        buttons["add_carn"] = Button(btn_x, SCREEN_HEIGHT - 110, btn_width, btn_height, "Añadir Carnívoro", COLOR_CARNIVORO, COLOR_TEXT)
        buttons["add_omni"] = Button(btn_x, SCREEN_HEIGHT - 60, btn_width, btn_height, "Añadir Omnívoro", COLOR_OMNIVORO, COLOR_TEXT)
        return buttons

    def _draw_text(self, text, font, color, surface, x, y):
        textobj = font.render(text, 1, color)
        textrect = textobj.get_rect()
        textrect.topleft = (x, y)
        surface.blit(textobj, textrect)

    def draw_simulation(self, ecosistema, logs, dia_actual, sim_over):
        # 1. Dibujar fondos
        self.screen.fill(COLOR_BACKGROUND)
        pygame.draw.rect(self.screen, COLOR_SIM_AREA, (0, 0, SIM_WIDTH, SCREEN_HEIGHT))

        # 2. Dibujar animales
        for animal in ecosistema.animales:
            color = COLOR_HERBIVORO
            if isinstance(animal, Carnivoro):
                color = COLOR_CARNIVORO
            elif isinstance(animal, Omnivoro):
                color = COLOR_OMNIVORO
            pygame.draw.circle(self.screen, color, (animal.x, animal.y), 7)

        # 3. Dibujar UI (panel de texto)
        ui_x = SIM_WIDTH + 10
        self._draw_text(f"DÍA: {dia_actual}", self.font_header, COLOR_TEXT, self.screen, ui_x, 20)
        
        # Estado del ecosistema
        self._draw_text("--- ESTADO ---", self.font_normal, COLOR_TEXT, self.screen, ui_x, 60)
        self._draw_text(f"Plantas: {ecosistema.plantas}", self.font_normal, COLOR_TEXT, self.screen, ui_x, 90)
        y_offset = 120
        for animal in ecosistema.animales:
            self._draw_text(f"{animal.nombre} (E:{animal.energia})", self.font_small, COLOR_TEXT, self.screen, ui_x, y_offset)
            y_offset += 20
        if not ecosistema.animales:
            self._draw_text("¡No quedan animales vivos!", self.font_normal, COLOR_TEXT, self.screen, ui_x, y_offset)

        # Logs del día
        y_offset += 30
        self._draw_text("--- EVENTOS DEL DÍA ---", self.font_normal, COLOR_TEXT, self.screen, ui_x, y_offset)
        y_offset += 25
        # Ajustar el espacio para los logs dependiendo de si la simulación ha terminado
        log_display_count = 10 if not sim_over else 15
        for log in logs[-log_display_count:]:
            self._draw_text(log, self.font_small, COLOR_TEXT, self.screen, ui_x, y_offset)
            y_offset += 18

        # 4. Dibujar botones
        if not sim_over:
            for button in self.buttons.values():
                button.draw(self.screen)
        
        # Instrucciones
        self._draw_text("Pulsa ESC para salir", self.font_normal, COLOR_TEXT, self.screen, 10, SCREEN_HEIGHT - 30)
        
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
        self.dia_actual = 0
        self.logs = ["¡Bienvenido! Pulsa 'Siguiente Día' para empezar."]

    def _poblar_ecosistema(self):
        """Método privado para añadir los animales iniciales."""
        self.ecosistema.agregar_animal(Herbivoro, "Conejo 1")
        self.ecosistema.agregar_animal(Herbivoro, "Ciervo 1")
        self.ecosistema.agregar_animal(Carnivoro, "Lobo 1")
        self.ecosistema.agregar_animal(Omnivoro, "Oso 1")
        self.ecosistema.agregar_animal(Herbivoro, "Conejo 2")

    def _avanzar_dia(self):
        """Avanza un día en la simulación."""
        self.dia_actual += 1
        self.logs = self.ecosistema.simular_dia()
        if self.dia_actual >= self.dias_simulacion or not self.ecosistema.animales:
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
                    elif self.view.buttons["add_herb"].rect.collidepoint(pos):
                        self.ecosistema.agregar_animal(Herbivoro)
                        self.logs.append(f"¡Ha nacido un nuevo Herbívoro!")
                    elif self.view.buttons["add_carn"].rect.collidepoint(pos):
                        self.ecosistema.agregar_animal(Carnivoro)
                        self.logs.append(f"¡Ha nacido un nuevo Carnívoro!")
                    elif self.view.buttons["add_omni"].rect.collidepoint(pos):
                        self.ecosistema.agregar_animal(Omnivoro)
                        self.logs.append(f"¡Ha nacido un nuevo Omnívoro!")
                    # Refrescar logs inmediatamente para ver el nuevo animal
                    self.logs = self.logs[-10:] # Mantiene los logs cortos
            # Dibujar todo
            self.view.draw_simulation(self.ecosistema, self.logs, self.dia_actual, sim_over)

        self.view.close()

# --- Ejecución Principal ---

def main():
    """Función principal para ejecutar la simulación."""
    controlador = SimulationController(dias_simulacion=50) # Puedes ajustar el total de días
    controlador.run()

if __name__ == "__main__":
    main()