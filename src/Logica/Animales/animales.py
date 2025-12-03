import math
import random
import pygame
from abc import ABC, abstractmethod
from src.Logica.Animales.Animal import Herbivoro, Carnivoro, Omnivoro


class Conejo(Herbivoro):
    def __init__(self, nombre: str, x: int, y: int, edad: int = 0, energia: int = 100, max_energia=None):
        if max_energia is None:
            max_energia = max(70, min(90, 80 + random.randint(-5, 5)))
        super().__init__(nombre, x, y, edad, energia, max_energia)

class Cabra(Herbivoro):
    def __init__(self, nombre: str, x: int, y: int, edad: int = 0, energia: int = 100, max_energia=None):
        if max_energia is None:
            max_energia = max(90, min(110, 100 + random.randint(-5, 5)))
        super().__init__(nombre, x, y, edad, energia, max_energia)
        
class Raton(Herbivoro):
    def __init__(self, nombre: str, x: int, y: int, edad: int = 0, energia: int = 100, max_energia=None):
        if max_energia is None:
            max_energia = max(30, min(50, 40 + random.randint(-5, 5)))
        super().__init__(nombre, x, y, edad, energia, max_energia)

class Insecto(Herbivoro):
    def __init__(self, nombre: str, x: int, y: int, edad: int = 0, energia: int = 100, max_energia=None):
        if max_energia is None:
            max_energia = max(30, min(50, 40 + random.randint(-5, 5)))
        super().__init__(nombre, x, y, edad, energia, max_energia)
        # Cargar el sonido del grillo
        self.sonido_grillo = pygame.mixer.Sound("Sounds/grillo 1.wav")
        self.sonidos = [self.sonido_grillo, self.sonido_grillo, self.sonido_grillo] # 1:aparece, 2:camina, 3:muere

    # No es necesario sobreescribir reproducir_sonido, usamos el de la clase Animal base
    # que ya funciona con la lista self.sonidos.

class Leopardo(Carnivoro):
    def __init__(self, nombre: str, x: int, y: int, edad: int = 0, energia: int = 100, max_energia=None):
        if max_energia is None:
            max_energia = max(100, min(120, 110 + random.randint(-5, 5)))
        super().__init__(nombre, x, y, edad, energia, max_energia)

class Gato(Carnivoro):
    def __init__(self, nombre: str, x: int, y: int, edad: int = 0, energia: int = 100, max_energia=None):
        if max_energia is None:
            max_energia = max(75, min(95, 85 + random.randint(-5, 5)))
        super().__init__(nombre, x, y, edad, energia, max_energia)
        
class Halcon(Carnivoro):
    def __init__(self, nombre: str, x: int, y: int, edad: int = 0, energia: int = 100, max_energia=None):
        if max_energia is None:
            max_energia = max(70, min(90, 80 + random.randint(-5, 5)))
        super().__init__(nombre, x, y, edad, energia, max_energia)
        
class Cerdo(Omnivoro):
    def __init__(self, nombre: str, x: int, y: int, edad: int = 0, energia: int = 100, max_energia=None):
        if max_energia is None:
            max_energia = max(110, min(130, 120 + random.randint(-5, 5)))
        super().__init__(nombre, x, y, edad, energia, max_energia)
        
class Mono(Omnivoro):
    def __init__(self, nombre: str, x: int, y: int, edad: int = 0, energia: int = 100, max_energia=None):
        if max_energia is None:
            max_energia = max(80, min(100, 90 + random.randint(-5, 5)))
        super().__init__(nombre, x, y, edad, energia, max_energia)