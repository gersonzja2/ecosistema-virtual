import pygame
import random

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