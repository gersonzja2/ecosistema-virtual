from model import Ecosistema, Herbivoro, Carnivoro, Omnivoro
from view import ConsoleView

class SimulationController:
    """
    Controla el flujo de la simulación, conectando el Modelo y la Vista.
    """
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