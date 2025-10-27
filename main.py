import random
from abc import ABC, abstractmethod

# --- Clases del Modelo (antes en model.py) ---

class Animal(ABC):
    """Clase base para todos los animales. Contiene la lógica y los datos."""
    def __init__(self, nombre: str, edad: int = 0, energia: int = 100):
        self.nombre = nombre
        self.edad = edad
        self.energia = energia
        self.esta_vivo = True
        # Contador para nombres únicos de crías
        self.__class__.contador = getattr(self.__class__, 'contador', 0) + 1

    @abstractmethod
    def comer(self, ecosistema) -> str:
        """Método abstracto para que el animal se alimente. Devuelve un log."""
        pass

    def moverse(self) -> str:
        """Reduce la energía del animal al moverse. Devuelve un log."""
        if self.esta_vivo:
            self.energia -= 10
            log = f"{self.nombre} se ha movido. Energía restante: {self.energia}"
            return log + self.verificar_estado()
        return ""

    def envejecer(self) -> str:
        """Incrementa la edad y reduce energía. Devuelve un log."""
        if self.esta_vivo:
            self.edad += 1
            self.energia -= 5
            log = f"{self.nombre} ha envejecido. Edad: {self.edad}, Energía: {self.energia}"
            return log + self.verificar_estado()
        return ""

    def verificar_estado(self) -> str:
        """Comprueba si el animal sigue vivo. Devuelve log si muere."""
        if self.esta_vivo and self.energia <= 0:
            self.esta_vivo = False
            return f" -> ¡{self.nombre} ha muerto por falta de energía!"
        return ""

    def __str__(self):
        estado = "Vivo" if self.esta_vivo else "Muerto"
        return f"Animal: {self.nombre}, Tipo: {self.__class__.__name__}, Edad: {self.edad}, Energía: {self.energia}, Estado: {estado}"

class Herbivoro(Animal):
    """Animal que solo come plantas."""
    def comer(self, ecosistema) -> str:
        if self.esta_vivo and ecosistema.plantas > 0:
            ecosistema.plantas -= 1
            self.energia += 20
            return f"{self.nombre} (Herbívoro) ha comido plantas. Energía: {self.energia}"
        return f"{self.nombre} (Herbívoro) no encontró plantas."

class Carnivoro(Animal):
    """Animal que come otros animales."""
    def comer(self, ecosistema) -> str:
        if not self.esta_vivo:
            return ""
        
        presa = ecosistema.encontrar_presa(self)
        if presa:
            self.energia += 50
            presa.energia = 0 # La presa muere instantáneamente
            log_muerte = presa.verificar_estado()
            return f"{self.nombre} (Carnívoro) ha cazado y comido a {presa.nombre}." + log_muerte
        else:
            self.energia -= 15
            log = f"{self.nombre} (Carnívoro) no encontró presas y perdió energía."
            return log + self.verificar_estado()

class Omnivoro(Animal):
    """Animal que puede comer tanto plantas como otros animales."""
    def comer(self, ecosistema) -> str:
        if not self.esta_vivo:
            return ""
        
        cazar = random.choice([True, False])
        presa_disponible = ecosistema.encontrar_presa(self) is not None

        if cazar and presa_disponible:
            return Carnivoro.comer(self, ecosistema)
        elif ecosistema.plantas > 0:
            return Herbivoro.comer(self, ecosistema)
        elif presa_disponible: # Si no hay plantas, intenta cazar
            return Carnivoro.comer(self, ecosistema)
        else:
            return f"{self.nombre} (Omnívoro) no encontró nada que comer."

class Ecosistema:
    """Gestiona el estado del entorno y los animales."""
    def __init__(self):
        self.animales = []
        self.plantas = 100

    def agregar_animal(self, animal):
        self.animales.append(animal)

    def encontrar_presa(self, depredador):
        presas_posibles = [
            animal for animal in self.animales 
            if isinstance(animal, Herbivoro) and animal.esta_vivo and animal != depredador
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

# --- Clase de la Vista (antes en view.py) ---

class ConsoleView:
    """Se encarga de mostrar la información de la simulación en la consola."""
    def mostrar_bienvenida(self):
        print("Iniciando la simulación del ecosistema virtual...")

    def mostrar_inicio_dia(self, dia: int):
        print(f"\n================== DÍA {dia} ==================")

    def mostrar_log_dia(self, logs: list[str]):
        print("\n--- Eventos del Día ---")
        for log in logs:
            print(log)

    def mostrar_estado_ecosistema(self, ecosistema):
        print("\n--- Estado Actual del Ecosistema ---")
        print(f"Recursos: {ecosistema.plantas} plantas.")
        for animal in ecosistema.animales:
            print(animal)

# --- Clase del Controlador (antes en controller.py) ---

class SimulationController:
    """Controla el flujo de la simulación, conectando el Modelo y la Vista."""
    def __init__(self, dias_simulacion: int):
        self.ecosistema = Ecosistema()
        self.view = ConsoleView()
        self.dias_simulacion = dias_simulacion

    def _poblar_ecosistema(self):
        """Método privado para añadir los animales iniciales."""
        self.ecosistema.agregar_animal(Herbivoro("Conejo 1"))
        self.ecosistema.agregar_animal(Herbivoro("Ciervo 1"))
        self.ecosistema.agregar_animal(Carnivoro("Lobo 1"))
        self.ecosistema.agregar_animal(Omnivoro("Oso 1"))
        self.ecosistema.agregar_animal(Herbivoro("Conejo 2"))

    def run(self):
        self._poblar_ecosistema()
        self.view.mostrar_bienvenida()
        for dia in range(1, self.dias_simulacion + 1):
            self.view.mostrar_inicio_dia(dia)
            logs = self.ecosistema.simular_dia()
            self.view.mostrar_log_dia(logs)
            self.view.mostrar_estado_ecosistema(self.ecosistema)

# --- Ejecución Principal ---

def main():
    """Función principal para ejecutar la simulación."""
    # Define cuántos días durará la simulación
    dias_simulacion = 10

    # Crea el controlador y corre la simulación
    controlador = SimulationController(dias_simulacion)
    controlador.run()

if __name__ == "__main__":
    main()