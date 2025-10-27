import random
from abc import ABC, abstractmethod

class Animal(ABC):
    """
    Clase base abstracta para todos los animales del ecosistema.
    Define los atributos y comportamientos comunes.
    """
    def __init__(self, nombre: str, edad: int = 0, energia: int = 100):
        self.nombre = nombre
        self.edad = edad
        self.energia = energia
        self.esta_vivo = True

    @abstractmethod
    def comer(self, ecosistema):
        """Método abstracto para que el animal se alimente."""
        pass

    def moverse(self):
        """Reduce la energía del animal al moverse."""
        if self.esta_vivo:
            self.energia -= 10
            print(f"{self.nombre} se ha movido. Energía restante: {self.energia}")
            self.verificar_estado()

    def envejecer(self):
        """Incrementa la edad del animal y verifica si sobrevive."""
        if self.esta_vivo:
            self.edad += 1
            self.energia -= 5 # El simple hecho de vivir consume energía
            print(f"{self.nombre} ha envejecido. Edad: {self.edad}, Energía: {self.energia}")
            self.verificar_estado()

    def verificar_estado(self):
        """Comprueba si el animal sigue vivo basado en su energía."""
        if self.energia <= 0:
            self.esta_vivo = False
            print(f"¡{self.nombre} ha muerto por falta de energía!")

    def __str__(self):
        estado = "Vivo" if self.esta_vivo else "Muerto"
        return f"Animal: {self.nombre}, Edad: {self.edad}, Energía: {self.energia}, Estado: {estado}"

class Herbivoro(Animal):
    """Animal que solo come plantas."""
    def comer(self, ecosistema):
        if self.esta_vivo and ecosistema.plantas > 0:
            ecosistema.plantas -= 1
            self.energia += 20
            print(f"{self.nombre} (Herbívoro) ha comido plantas. Energía: {self.energia}")

class Carnivoro(Animal):
    """Animal que come otros animales (específicamente herbívoros en esta simulación)."""
    def comer(self, ecosistema):
        if not self.esta_vivo:
            return
        
        presa = ecosistema.encontrar_presa(self)
        if presa:
            print(f"{self.nombre} (Carnívoro) ha cazado y comido a {presa.nombre}.")
            self.energia += 50
            presa.energia = 0
            presa.verificar_estado()
        else:
            print(f"{self.nombre} (Carnívoro) no encontró presas y perdió energía.")
            self.energia -= 15
            self.verificar_estado()

class Omnivoro(Animal):
    """Animal que puede comer tanto plantas como otros animales."""
    def comer(self, ecosistema):
        if not self.esta_vivo:
            return
        # Decide aleatoriamente si cazar o comer plantas
        if random.choice([True, False]) and ecosistema.encontrar_presa(self):
            Carnivoro.comer(self, ecosistema)
        elif ecosistema.plantas > 0:
            Herbivoro.comer(self, ecosistema)
        else: # Si no hay ni presas ni plantas, intenta cazar de nuevo
            Carnivoro.comer(self, ecosistema)