# 💻 Simulador de Ecosistema Virtual 🌿

Proyecto de un simulador de ecosistema virtual, desarrollado en Python con la librería Pygame.

El objetivo es crear un pequeño mundo digital donde diferentes especies de animales (herbívoros, carnívoros y omnívoros) interactúan entre sí y con su entorno. Los animales nacen, buscan comida, beben agua, huyen de los depredadores, se reproducen y mueren, todo de forma controlada.

## ✨ Características Principales

- **IA de Animales:** Cada animal tiene sus propias necesidades (hambre, sed) y estados (deambulando, cazando, huyendo). Toman decisiones sobre qué hacer a continuación.
- **Diversidad de Especies:**
  - **Herbívoros:** Conejo, Ratón, Cabra, Insecto.
  - **Carnívoros:** Leopardo, Gato, Halcón.
  - **Omnívoros:** Cerdo, Mono.
- **Entorno Dinámico:**
  - **Ciclo Día/Noche y Estaciones:** El paso del tiempo afecta el crecimiento de los recursos y el comportamiento de los animales.
  - **Terrenos Múltiples:** Praderas con hierba, selvas con bayas y ríos con peces.
- **Interfaz Gráfica Interactiva:**
  - Visualización en tiempo real de todos los animales y recursos.
  - Panel de control para pausar/reanudar la simulación, avanzar los días y añadir nuevos animales.
  - Gráfico que muestra la evolución de las poblaciones a lo largo del tiempo.
  - Posibilidad de hacer clic en un animal para ver sus estadísticas detalladas.
- **Persistencia:** ¡Puedes guardar el estado de tu simulación y cargarlo más tarde para continuar donde lo dejaste!
- **Música de fondo y sonidos:** Para hacer la experiencia más amena :)

## ⚙️ Requisitos

Para ejecutar este proyecto, solo necesitas tener Python y Pygame instalados.

- **Python 3.x**
- **Pygame**

## 🚀 Cómo Empezar

1.  **Clona o descarga este repositorio:**
    ```bash
    git clone https://github.com/tu-usuario/tu-repositorio.git
    cd tu-repositorio
    ```

2.  **Instala Pygame:**
    Si no lo tienes instalado, puedes hacerlo con pip:
    ```bash
    pip install pygame
    ```

3.  **(Opcional pero recomendado) Sprites y Música:**
    El simulador funciona sin imágenes, usando círculos de colores. Pero para una mejor experiencia, crea una carpeta llamada `assets` en la raíz del proyecto y coloca dentro los archivos de imagen (`.png`) para cada animal y los archivos de música (`.mp3`).

4.  **Ejecuta el simulador:**
    ```bash
    python main.py
    ```

¡Y listo! La simulación comenzará en modo de pausa. Puedes usar los botones de la interfaz para empezar.

## 🎮 Controles

- **Pausa/Reanudar:** Inicia o detiene el paso del tiempo.
- **Adelantar Día:** Simula un día completo de forma instantánea.
- **Añadir Animal:** Introduce un nuevo animal de la especie seleccionada en el ecosistema.
- **Guardar/Cargar/Reiniciar:** Gestiona el estado de la simulación.
- **Clic en un animal:** Muestra sus detalles en el panel de información.
- **ESC:** Cierra la aplicación.

## 👥 Roles del Equipo

Este proyecto fue desarrollado por un equipo dedicado de estudiantes apasionados por la programación y la biología computacional.

- **Encargado de la logica y el comportamiento animal(Backend):** Responsable de la implementación de la lógica del ecosistema, el modelo de datos y la inteligencia artificial de los animales.
  - *Encargado: Gerson Zambrana*
- **Desarrollador de Interfaz de Usuario (Frontend):** A cargo del diseño y la implementación de la interfaz gráfica con Pygame, la visualización de datos, los controles interactivos y la experiencia de usuario.
  - *Encargada: Hans Mamani*
- **Control de Calidad de sonido:** Encargado de realizar las pruebas funcionales, identificar y reportar errores, y la implementacion de sonidos y musica de fondo
  - *Encargado: Juan Ojeda*

## � Posibles Mejoras (TO-DO)

- [ ] **Comportamientos más complejos:** Implementar caza en manada para algunos carnívoros o comportamiento de rebaño para herbívoros.
- [ ] **Mejorar el terreno:** Añadir terrenos no transitables como montañas o rocas.
- [ ] **Más eventos climáticos:** Como lluvias que aceleren el crecimiento de la hierba o inviernos más duros.
- [ ] **Optimizar la detección de presas:** Mejorar la lógica para que los depredadores elijan presas de forma más inteligente (ej. la más débil o la más cercana).
- [ ] **Refactorizar el código de la UI:** Separar la lógica de la interfaz en su propio módulo para que `main.py` quede más limpio.

---
*Proyecto realizado como parte de un ejercicio de programación y simulación.*