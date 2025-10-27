from abc import ABC, abstractmethod
import random

# --- Constantes de la Simulación ---
# Estas constantes definen los límites del área donde los animales pueden moverse.
SIM_WIDTH = 800
SCREEN_HEIGHT = 700

# --- Clases del Modelo ---

class Animal(ABC):
    """Clase base para todos los animales. Contiene la lógica y los datos."""
    def __init__(self, nombre: str, x: int, y: int, edad: int = 0, energia: int = 100):
        self._nombre = nombre
        self.x = x
        self.y = y
        self._edad = edad
        self._energia = energia
        self._esta_vivo = True
        # Contador para nombres únicos de crías
        type(self).contador = getattr(type(self), 'contador', 0) + 1

    @property
    def nombre(self):
        return self._nombre

    @property
    def edad(self):
        return self._edad

    @property
    def energia(self):
        return self._energia

    @property
    def esta_vivo(self):
        return self._esta_vivo

    @abstractmethod
    def comer(self, ecosistema) -> str:
        """Método abstracto para que el animal se alimente. Devuelve un log."""
        pass

    def moverse(self) -> str:
        """Reduce la energía del animal al moverse. Devuelve un log."""
        if self._esta_vivo:
            self._energia -= 5 # Reducimos menos para que la simulación dure más
            # Movimiento aleatorio dentro del área de simulación
            self.x += random.randint(-10, 10)
            self.y += random.randint(-10, 10)
            self.x = max(0, min(self.x, SIM_WIDTH - 10))
            self.y = max(0, min(self.y, SCREEN_HEIGHT - 10))
            log = f"{self._nombre} se ha movido. Energía restante: {self._energia}"
            return log + self.verificar_estado()
        return ""

    def envejecer(self) -> str:
        """Incrementa la edad y reduce energía. Devuelve un log."""
        if self._esta_vivo:
            self._edad += 1
            self._energia -= 2
            log = f"{self._nombre} ha envejecido. Edad: {self._edad}, Energía: {self._energia}"
            return log + self.verificar_estado()
        return ""

    def verificar_estado(self) -> str:
        """Comprueba si el animal sigue vivo. Devuelve log si muere."""
        if self._esta_vivo and self._energia <= 0:
            self._esta_vivo = False
            return f" -> ¡{self._nombre} ha muerto por falta de energía!"
        return ""

    def __str__(self):
        estado = "Vivo" if self._esta_vivo else "Muerto"
        return f"Animal: {self._nombre}, Tipo: {self.__class__.__name__}, Edad: {self._edad}, Energía: {self._energia}, Estado: {estado}"

class Herbivoro(Animal):
    """Animal que solo come plantas."""
    def comer(self, ecosistema) -> str:
        if self._esta_vivo and ecosistema.plantas > 0:
            ecosistema.plantas -= 1
            self._energia += 20
            return f"{self._nombre} (Herbívoro) ha comido plantas. Energía: {self._energia}"
        return f"{self._nombre} (Herbívoro) no encontró plantas."

class Carnivoro(Animal):
    """Animal que come otros animales."""
    def comer(self, ecosistema) -> str:
        if not self._esta_vivo:
            return ""
        
        presa = ecosistema.encontrar_presa(self)
        if presa:
            self._energia += 50
            presa._energia = 0 # La presa muere instantáneamente
            log_muerte = presa.verificar_estado()
            return f"{self._nombre} (Carnívoro) ha cazado y comido a {presa.nombre}." + log_muerte
        else:
            self._energia -= 15
            log = f"{self._nombre} (Carnívoro) no encontró presas y perdió energía."
            return log + self.verificar_estado()

class Omnivoro(Animal):
    """Animal que puede comer tanto plantas como otros animales."""
    def comer(self, ecosistema) -> str:
        if not self._esta_vivo:
            return ""
        
        cazar = random.choice([True, False])
        presa_disponible = ecosistema.encontrar_presa(self) is not None

        if cazar and presa_disponible:
            presa = ecosistema.encontrar_presa(self)
            if presa:
                self._energia += 50
                presa._energia = 0
                log_muerte = presa.verificar_estado()
                return f"{self._nombre} (Omnívoro) ha cazado y comido a {presa.nombre}." + log_muerte
        elif ecosistema.plantas > 0:
            # Lógica de herbívoro directamente aquí para un log más claro
            ecosistema.plantas -= 1
            self._energia += 20
            return f"{self._nombre} (Omnívoro) ha comido plantas. Energía: {self._energia}"
        elif presa_disponible: # Si no hay plantas, intenta cazar
            presa = ecosistema.encontrar_presa(self)
            if presa:
                self._energia += 50
                presa._energia = 0
                log_muerte = presa.verificar_estado()
                return f"{self._nombre} (Omnívoro) ha cazado y comido a {presa.nombre}." + log_muerte
        # Si no encuentra comida
        self._energia -= 10 # Pierde algo de energía buscando
        log = f"{self._nombre} (Omnívoro) no encontró nada que comer."
        return log + self.verificar_estado()

class Ecosistema:
    """Gestiona el estado del entorno y los animales."""
    def __init__(self):
        self.animales: list[Animal] = []
        self.plantas = 100

    def encontrar_presa(self, depredador):
        presas_posibles = [
            animal for animal in self.animales 
            if not isinstance(animal, Carnivoro) and animal.esta_vivo and animal != depredador
        ]
        return random.choice(presas_posibles) if presas_posibles else None

    def simular_dia(self) -> list[str]:
        """Ejecuta un ciclo de simulación y devuelve los logs del día."""
        logs_dia = []
        self.plantas += 10
        logs_dia.append(f"Las plantas han crecido. Total de plantas: {self.plantas}")

        random.shuffle(self.animales)
        for animal in self.animales:
            if animal.esta_vivo:
                logs_dia.append(animal.envejecer())
                logs_dia.append(animal.moverse())
                logs_dia.append(animal.comer(self))
        
        self.animales = [animal for animal in self.animales if animal.esta_vivo]
        return [log for log in logs_dia if log] # Filtra logs vacíos

    def agregar_animal(self, tipo_animal, nombre=None):
        """Crea un animal con un nombre único y lo añade al ecosistema."""
        # Si no se proporciona un nombre, se genera uno automáticamente.
        if nombre is None:
            nombre = f"{tipo_animal.__name__} {getattr(tipo_animal, 'contador', 0) + 1}"

        x = random.randint(20, SIM_WIDTH - 20)
        y = random.randint(20, SCREEN_HEIGHT - 20)
        nuevo_animal = tipo_animal(nombre, x, y)
        self.animales.append(nuevo_animal)