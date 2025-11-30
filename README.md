# Simulador de Ecosistema Virtual

Este proyecto es una simulación de un ecosistema 2D desarrollada en Python utilizando la librería Pygame. El simulador modela las interacciones entre diferentes especies de animales (herbívoros, carnívoros y omnívoros) y su entorno dinámico.

## Características Principales

- **Fauna Diversa**: Incluye múltiples especies como conejos, cabras, leopardos, cerdos, y más, cada una con su propia dieta y comportamiento.
- **Entorno Dinámico**: El mapa contiene diferentes biomas como praderas, selvas y ríos, que influyen en la disponibilidad de recursos.
- **Ciclo de Vida Completo**: Los animales nacen, crecen, se reproducen, buscan comida y eventualmente mueren, dejando carcasas que pueden ser consumidas.
- **Comportamientos Complejos**:
  - Los herbívoros pastan en busca de hierba.
  - Los carnívoros pueden cazar herbívoros o pescar en los ríos.
  - Los omnívoros adaptan su dieta según la disponibilidad, comiendo hierba, bayas o cazando.
  - Los animales buscan pareja para reproducirse.
- **Sistema Climático y de Día/Noche**: La simulación avanza hora por hora, con un ciclo de 24 horas. El clima puede cambiar, afectando el crecimiento de los recursos (ej. "Sequía").
- **Interfaz de Usuario Interactiva**: Un panel de control permite monitorear el estado del ecosistema, controlar la simulación y añadir nuevos animales.
- **Visualización de Datos**: Un gráfico en tiempo real muestra la evolución de las poblaciones de herbívoros, carnívoros y omnívoros.
- **Sistema de Guardado y Carga**:
  - Crea perfiles de usuario.
  - Guarda y carga múltiples partidas por cada perfil.

## Actualizaciones Recientes 
- **Mejoras Visuales**: Se optimizaron las texturas del entorno (praderas, santuarios) con un estilo *pixel art* para una mejor estética. También se mejoró la animación del agua y se implementaron nubes dinámicas, plantas y árboles.
- **Sonido Inmersivo**: Se corrigieron y añadieron nuevos sonidos para los animales, mejorando la inmersión en el ecosistema.

## Características Principales
- **Visualización de Datos**: Un gráfico en tiempo real muestra la evolución de las poblaciones de herbívoros, carnívoros y omnívoros.
- **Sistema de Guardado y Carga**:
  - Crea perfiles de usuario.
  - Guarda y carga múltiples partidas por cada perfil.

## Tecnologías Utilizadas

- **Python 3**
- **Pygame**

## ¿Cómo Ejecutar el Proyecto?

1.  **Prerrequisitos**:
    - Asegúrate de tener Python 3 instalado.
    - Necesitarás la librería Pygame. Puedes instalarla con pip:
      ```bash
      pip install pygame
      ```

2.  **Estructura de Archivos**:
    - El proyecto requiere una carpeta `assets/` en el mismo directorio que los scripts, la cual debe contener las imágenes (sprites, texturas) y la música (`.mp3`).
    - Se creará una carpeta `saves/` automáticamente para almacenar las partidas guardadas.

3.  **Ejecución**:
    - Para iniciar el simulador, ejecuta el archivo `main.py` desde tu terminal:
      ```bash
      python main.py
      ```

## Controles y Funcionalidades de la Interfaz

### Menú Principal
- **Selección de Usuario**: Haz clic en un nombre de usuario para ver sus partidas guardadas.
- **Crear Nuevo Usuario**: Escribe un nombre y presiona `Enter` para crear un nuevo perfil.
- **Selección de Partida**: Elige una partida existente para cargarla o selecciona "Nueva Partida" para empezar desde cero.
- **Empezar/Cargar**: Inicia la simulación con la configuración seleccionada.

### En la Simulación
- **Clic izquierdo sobre un animal**: Selecciona un animal para ver sus detalles en el panel de información.
- **Clic izquierdo sobre un segundo animal**: Si ya tienes uno seleccionado, el segundo será elegido como posible pareja para la reproducción.
- **Tecla `ESC`**: Guarda el estado actual de la partida y vuelve al menú principal.

### Panel de Control (UI)
- **Añadir Animales**: Botones para introducir nuevas especies al ecosistema.
- **Pausa/Reanudar**: Detiene o continúa el paso del tiempo en la simulación.
- **Adelantar Día**: Avanza la simulación 24 horas de golpe.
- **Guardar/Cargar/Reiniciar**: Gestiona el estado de la partida actual.
- **Música ON/OFF**: Activa o desactiva la música de fondo.
- **Alimentar Herbívoros**: Ordena a todos los herbívoros y omnívoros con baja energía que busquen comida.
- **Cazar Herbívoros / Regresar Carnívoros**: Activa un modo de caza donde los carnívoros cruzan los ríos para cazar en el territorio de los herbívoros. Al desactivarlo, regresan a su zona.
- **Forzar Reproducción**: Con dos animales de la misma especie seleccionados, inicia el comportamiento de apareamiento entre ellos.

---
*Registro de desarrollo en `bitacora.txt`.*