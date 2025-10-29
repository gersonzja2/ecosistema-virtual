# ecosistema-virtual

Un simulador de ecosistema virtual avanzado construido con Python y Pygame.

## Descripción

Este proyecto simula un ecosistema complejo donde diferentes tipos de animales (herbivoros, carnívoros y omnívoros) con rasgos genéticos interactúan entre sí y con un entorno dinámico. Los animales nacen, envejecen, buscan comida y agua, se reproducen pasando sus genes y mueren, todo ello gestionado en un ciclo de días que atraviesa diferentes estaciones y eventos climáticos.

La simulación se visualiza en una ventana de Pygame, que muestra a los animales como sprites, un panel de información detallado, un gráfico de población en tiempo real y permite una alta interactividad.

## Características

*   **Modelo Orientado a Objetos**: El ecosistema, los animales y los recursos están modelados como clases.
*   **Tipos de Animales**:
    *   **Herbívoro**: Se alimenta de hierba.
    *   **Carnívoro**: Caza activamente a herbívoros y omnívoros.
    *   **Omnívoro**: Puede cazar o buscar bayas en las selvas.
*   **Comportamiento Avanzado**:
    *   **Percepción**: Los animales tienen un rango de visión para buscar presas, agua (ríos) o comida (selvas).
    *   **Necesidades**: Además de energía, los animales ahora tienen sed y deben beber agua de los ríos para sobrevivir.
*   **Genética y Evolución**:
    *   Los animales poseen genes (energía máxima, rango de visión) que heredan a sus crías con pequeñas mutaciones, permitiendo la selección natural.
*   **Ecosistema Dinámico**:
    *   **Estaciones del Año**: El ciclo de Primavera, Verano, Otoño e Invierno afecta el crecimiento de los recursos y el coste energético de los animales.
    *   **Eventos Climáticos**: Eventos aleatorios como "Sequías" pueden ocurrir, impactando la disponibilidad de comida.
*   **Recursos Naturales**:
    *   **Hierba**: Crece en las praderas (terreno abierto) y es consumida por herbívoros.
    *   **Bayas**: Crecen exclusivamente en las zonas de selva y son consumidas por omnívoros.
*   **Entorno Interactivo**:
    *   **Montañas y Ríos**: Actúan como barreras naturales que los animales no pueden cruzar, afectando sus patrones de movimiento.
    *   **Selvas**: Son biomas específicos donde crecen las bayas.
*   **Interfaz Gráfica Avanzada**:
    *   **Sprites**: Los animales se representan con imágenes en lugar de formas simples.
    *   **Gráfico de Población**: Muestra la evolución de las poblaciones en tiempo real.
    *   **Panel Interactivo**: Permite hacer clic en un animal para ver sus estadísticas y genes detallados.
*   **Interactividad y Control**:
    *   Permite añadir nuevos animales en cualquier momento.
    *   **Guardar y Cargar**: El estado completo de la simulación se puede guardar en un archivo y cargar posteriormente.

## Cómo ejecutarlo

1.  **Instalar dependencias**: Asegúrate de tener Python y Pygame instalados.
    ```
    pip install pygame
    ```

2.  **Preparar los sprites (imágenes)**:
    *   Crea una carpeta llamada `assets` en el mismo directorio donde se encuentran los archivos `.py`.
    *   Dentro de la carpeta `assets`, coloca tres imágenes para los animales:
        *   `herbivoro.png`
        *   `carnivoro.png`
        *   `omnivoro.png`
    *   **Consejo**: Si no tienes imágenes, la simulación funcionará igualmente, mostrando círculos de colores en lugar de sprites. El programa te avisará en la consola.

3.  **Ejecutar la simulación**:
    ```
    python main.py
    ```
