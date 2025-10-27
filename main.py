from controller import SimulationController

def main():
    """Función principal para ejecutar la simulación."""
    # Define cuántos días durará la simulación
    dias_simulacion = 10
    
    # Crea el controlador y corre la simulación
    controlador = SimulationController(dias_simulacion)
    controlador.run()

if __name__ == "__main__":
    main()