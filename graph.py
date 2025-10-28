import pygame

class PopulationGraph:
    """Dibuja un gráfico de la población a lo largo del tiempo."""
    def __init__(self, x, y, width, height, font):
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.history = [] # Almacenará tuplas de (herb, carn, omni)
        self.colors = {
            "herb": (255, 255, 255),
            "carn": (231, 76, 60),
            "omni": (52, 152, 219)
        }

    def update(self, populations):
        """Añade un nuevo punto de datos al historial."""
        self.history.append(populations)
        # Limitar el historial para que el gráfico no se comprima demasiado
        if len(self.history) > self.rect.width:
            self.history.pop(0)

    def draw(self, surface):
        """Dibuja el gráfico completo en la superficie dada."""
        # Fondo del gráfico y título
        pygame.draw.rect(surface, (40, 40, 40), self.rect)
        title_surf = self.font.render("Población", True, (236, 240, 241))
        surface.blit(title_surf, (self.rect.x + 5, self.rect.y + 5))

        if not self.history:
            return

        max_pop = max(max(p) for p in self.history) if self.history else 1
        if max_pop == 0: max_pop = 1 # Evitar división por cero

        # Dibujar líneas para cada tipo de animal
        for i, pop_type in enumerate(["herb", "carn", "omni"]):
            points = []
            for day, pops in enumerate(self.history):
                x_pos = self.rect.x + day
                y_pos = self.rect.bottom - int((pops[i] / max_pop) * (self.rect.height - 20)) # -20 para padding
                points.append((x_pos, y_pos))
            if len(points) > 1:
                pygame.draw.lines(surface, self.colors[pop_type], False, points, 1)