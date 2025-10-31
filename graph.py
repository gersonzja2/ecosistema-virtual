import pygame

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

        # Dibujar leyenda
        legend_y = self.rect.y + 20
        for pop_type, label in self.labels.items():
            label_surf = self.font.render(label, True, self.colors[pop_type])
            surface.blit(label_surf, (self.rect.right - 80, legend_y))
            legend_y += 15
        
        if not self.history:
            return
        
        max_pop = max(max(p) for p in self.history if p) if any(self.history) else 1
        if max_pop == 0: max_pop = 1

        for i, pop_type in enumerate(["herb", "carn", "omni"]):
            points = []
            for day, pops in enumerate(self.history):
                x_pos = self.rect.x + day
                y_pos = self.rect.bottom - int((pops[i] / max_pop) * (self.rect.height - 20))
                points.append((x_pos, y_pos))
            if len(points) > 1:
                pygame.draw.lines(surface, self.colors[pop_type], False, points, 1)