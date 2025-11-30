import random
import math
import pygame

MAX_HIERBA_NORMAL = 70
MAX_HIERBA_PRADERA = 120

class Carcasa:
    def __init__(self, x, y, energia_restante=60):
        self.x = x
        self.y = y
        self.energia_restante = energia_restante
        self.dias_descomposicion = 0

class Pez:
    def __init__(self, x, y, rio=None):
        self.x = x
        self.y = y
        self.rio = rio
        self.energia = 50
        self.fue_comido = False
        self.velocidad = 1
        self.direccion = random.uniform(0, 2 * math.pi)

    def actualizar(self):
        """Mueve el pez y lo mantiene dentro de los límites de su río."""
        if self.fue_comido:
            return

        # Mover el pez
        self.x += self.velocidad * math.cos(self.direccion)
        self.y += self.velocidad * math.sin(self.direccion)

        # Rebotar en los bordes del río
        if not self.rio.rect.collidepoint(self.x, self.y):
            self.x = max(self.rio.rect.left, min(self.x, self.rio.rect.right))
            self.y = max(self.rio.rect.top, min(self.y, self.rio.rect.bottom))
            # Cambiar de dirección al chocar
            self.direccion = random.uniform(0, 2 * math.pi)

class Terreno:
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)
        

class Rio(Terreno):
    def __init__(self, rect):
        super().__init__(rect)
        self.max_peces = 20
        self.peces = []
        self._generar_peces_iniciales()

    def _generar_peces_iniciales(self):
        for _ in range(10):
            x = random.randint(self.rect.left + 5, self.rect.right - 5)
            y = random.randint(self.rect.top + 5, self.rect.bottom - 5)
            pez = Pez(x, y, self)
            self.peces.append(pez)

    def crecer_recursos(self, factor_crecimiento):
        if len(self.peces) < 50:
            if random.random() < 0.1 * factor_crecimiento:
                x = random.randint(self.rect.left + 5, self.rect.right - 5)
                y = random.randint(self.rect.top + 5, self.rect.bottom - 5)
                self.peces.append(Pez(x, y, self))

class Selva(Terreno):
    def __init__(self, rect):
        super().__init__(rect)
        self.bayas = 25

    def crecer_recursos(self, factor_crecimiento):
        self.bayas += int(3 * factor_crecimiento)

class Pradera(Terreno):
    def __init__(self, rect):
        super().__init__(rect)
        self.max_hierba = MAX_HIERBA_PRADERA
        self.tasa_crecimiento = 2