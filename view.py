class ConsoleView:
    """
    Se encarga de mostrar la información de la simulación en la consola.
    """
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