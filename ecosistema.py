import random
from animal import Herbivoro, Carnivoro

class Ecosistema:
    """
    Gestiona el entorno, los animales y las interacciones dentro de la simulación.
    """
    def __init__(self):
        self.animales = []
        self.plantas = 100  # Recurso inicial de plantas

    def agregar_animal(self, animal):
        """Añade un animal a la lista del ecosistema."""
        self.animales.append(animal)
        print(f"Se ha añadido a {animal.nombre} al ecosistema.")

    def encontrar_presa(self, depredador):
        """Busca una presa adecuada para un carnívoro u omnívoro."""
        presas_posibles = [
            animal for animal in self.animales 
            if isinstance(animal, Herbivoro) and animal.esta_vivo and animal != depredador
        ]
        if presas_posibles:
            return random.choice(presas_posibles)
        return None

    def simular_dia(self):
        """Ejecuta un ciclo de simulación (un día)."""
        print("\n--- Nuevo Día en el Ecosistema ---")
        
        # Las plantas crecen un poco cada día
        self.plantas += 10
        print(f"Las plantas han crecido. Total de plantas: {self.plantas}")

        # Mezclar los animales para que el orden de acción sea aleatorio
        random.shuffle(self.animales)

        for animal in self.animales:
            if animal.esta_vivo:
                animal.envejecer()
                animal.moverse()
                animal.comer(self)
        
        # Eliminar animales muertos del ecosistema
        self.animales = [animal for animal in self.animales if animal.esta_vivo]

    def mostrar_estado(self):
        """Imprime el estado actual de todos los animales en el ecosistema."""
        print("\n--- Estado Actual del Ecosistema ---")
        print(f"Recursos: {self.plantas} plantas.")
        for animal in self.animales:
            print(animal)