import math
import random
import pygame
from abc import ABC, abstractmethod
import src.Logica.SoundBank.SoundBank as Sb # Tipos will be defined in this file
from src.Logica.Terrenos.Terrenos import Rio

SIM_WIDTH = 800
SCREEN_HEIGHT = 700
CELL_SIZE = 20
BORDE_MARGEN = 20 # Margen de seguridad para que los animales no se acerquen a los bordes

class Animal(ABC):
    contador = 0

    def __init__(self, nombre: str, x: int, y: int, edad: int = 0, energia: int = 100, max_energia=None):
        self._nombre = nombre
        self._x_float = float(x)
        self._y_float = float(y)
        self._edad = max(0, edad)
        if max_energia is None:
            max_energia = max(80, min(120, 100 + random.randint(-10, 10)))
        self.max_energia = max_energia
        self._energia = max(0, min(energia, self.max_energia))
        self._esta_vivo = True
        self.estado = "deambulando" # Estados: deambulando, buscando_comida, buscando_agua, cazando, huyendo
        self.objetivo = None  # Puede ser una tupla (x,y) o un objeto Animal
                # === BEGIN AUDIO FIELDS ===
        self.sonidos = Sb.SoundBank.get_for(type(self).__name__)
        self._last_walk_tick = 0
        # === END AUDIO FIELDS ===

        
        self.estado = "deambulando"
        self.velocidad = 1.5 + random.uniform(-0.2, 0.2)
        self.target_x = None
        self.target_y = None
        self.tiempo_deambulando = 0
        self.ticks_desde_ultimo_paso = random.randint(0, 300) # Inicialización aleatoria para desincronizar
        self.ecosistema = None
        self.pareja_objetivo = None
        self.objetivo_puente = None
        self.puente_cruzado = None # Para recordar qué puente usó para cazar
        self.modo_caza_activado = False
        
        self.objetivo_comida = None # Puede ser un río, una carcasa, etc.
        type(self).contador = getattr(type(self), 'contador', 0) + 1

    @property
    def nombre(self):
        return self._nombre
    def reproducir_sonido(self, tipo: int, volume: float = 1.0):
        """tipo: 1=aparece, 2=camina, 3=muere"""
        if 1 <= tipo <= 3 and self.sonidos and pygame.mixer.get_init():
            snd = self.sonidos[tipo-1] if len(self.sonidos) >= tipo else None
            if snd:
                try:
                    orig = snd.get_volume()
                    snd.set_volume(max(0.0, min(1.0, orig * volume)))
                    snd.play()
                    snd.set_volume(orig)
                except Exception as e:
                    print("[Sound] Error al reproducir:", e)


    @property
    def x(self):
        return int(self._x_float)

    @property
    def y(self):
        return int(self._y_float)

    @property
    def edad(self):
        return self._edad

    @property
    def energia(self):
        return self._energia

    @property
    def esta_vivo(self):
        return self._energia > 0

    def __str__(self):
        estado = "Vivo" if self.esta_vivo else "Muerto"
        return f"Animal: {self._nombre}, Tipo: {self.__class__.__name__}, Edad: {self._edad}, Energía: {self._energia}, Estado: {estado}"

    def _obtener_zona_deambulacion(self):
        """Devuelve el rectángulo (x, y, w, h) de la zona de deambulación."""
        center_x = SIM_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2
        thickness = 60
        
        rio_borde_izq = center_x - thickness // 2
        rio_borde_der = center_x + thickness // 2
        rio_borde_sup = center_y - thickness // 2

        if isinstance(self, Carnivoro) and not self.modo_caza_activado:
            # Cuadrante superior izquierdo
            return (BORDE_MARGEN, BORDE_MARGEN, rio_borde_izq - BORDE_MARGEN * 2, rio_borde_sup - BORDE_MARGEN * 2)
        elif isinstance(self, Herbivoro):
            # Cuadrante inferior (todo el ancho)
            return (BORDE_MARGEN, rio_borde_sup + thickness, SIM_WIDTH - BORDE_MARGEN * 2, SCREEN_HEIGHT - (rio_borde_sup + thickness) - BORDE_MARGEN)
        elif isinstance(self, Omnivoro):
            # Cuadrante superior derecho
            return (rio_borde_der, BORDE_MARGEN, SIM_WIDTH - rio_borde_der - BORDE_MARGEN, rio_borde_sup - BORDE_MARGEN * 2)
        return (BORDE_MARGEN, BORDE_MARGEN, SIM_WIDTH - 2 * BORDE_MARGEN, SCREEN_HEIGHT - 2 * BORDE_MARGEN)

    def deambular(self):
        """Comportamiento de movimiento errático dentro de una zona."""
        if self.target_x is None or self.tiempo_deambulando <= 0:
            zona_x, zona_y, zona_w, zona_h = self._obtener_zona_deambulacion()
            self.target_x = random.randint(zona_x, zona_x + zona_w)
            self.target_y = random.randint(zona_y, zona_y + zona_h)
            self.tiempo_deambulando = random.randint(50, 150) # Ticks para deambular hacia el objetivo

        dx = self.target_x - self._x_float
        dy = self.target_y - self._y_float
        dist = math.sqrt(dx**2 + dy**2)

        if dist < self.velocidad:
            self._x_float = self.target_x
            self._y_float = self.target_y
            self.target_x = None # Forzar nuevo objetivo
        else:
            self._x_float += (dx / dist) * self.velocidad
            self._y_float += (dy / dist) * self.velocidad

        # Asegurarse de que el animal no se salga de los límites de la simulación
        self._x_float = max(BORDE_MARGEN, min(self._x_float, SIM_WIDTH - BORDE_MARGEN))
        self._y_float = max(BORDE_MARGEN, min(self._y_float, SCREEN_HEIGHT - BORDE_MARGEN))

        self.ticks_desde_ultimo_paso += 1
        if self.ticks_desde_ultimo_paso > 300:  # 300 ticks = 5 segundos a 60 FPS
            self.reproducir_sonido(2, volume=0.3)  # Tipo 2 es el sonido de caminar
            self.ticks_desde_ultimo_paso = random.randint(-50, 50) # Reinicio aleatorio para mantener la desincronización


        self.tiempo_deambulando -= 1

    def buscar_comida(self, forzado=False):
        """Método para iniciar la búsqueda de comida."""
        # Esta es una implementación básica. Se puede expandir en las subclases.
        # Por ahora, simplemente cambia el estado para que la lógica en 'actualizar' se active.
        if forzado:
            self.estado = "buscando_comida"
            print(f"{self.nombre} forzado a buscar comida.")

    def buscar_pareja_para_reproducir(self, pareja_potencial):
        """Método para iniciar el comportamiento de reproducción con una pareja específica."""
        # Condiciones simplificadas: misma especie y ambos vivos.
        if self.esta_vivo and pareja_potencial.esta_vivo and type(self) == type(pareja_potencial):
            print(f"Iniciando reproducción entre {self.nombre} y {pareja_potencial.nombre}.")
            self.estado = "buscando_pareja"
            self.pareja_objetivo = pareja_potencial
            pareja_potencial.estado = "buscando_pareja"
            pareja_potencial.pareja_objetivo = self
        else:
            print(f"No se puede reproducir: {self.nombre} y {pareja_potencial.nombre} no son de la misma especie.")

    def _dar_a_luz(self):
        print(f"¡{self.nombre} ha dado a luz!")
        self.ecosistema.agregar_animal(type(self), es_cria=True, pos=(self.x, self.y))

    def actualizar(self, ecosistema):
        if not self.esta_vivo:
            return

        if self.ecosistema is None:
            self.ecosistema = ecosistema

        # Lógica de comportamiento principal
        if self.estado == "buscando_pareja":
            if self.pareja_objetivo and self.pareja_objetivo.esta_vivo and self.pareja_objetivo.estado == "buscando_pareja":
                # Moverse hacia la pareja
                dx = self.pareja_objetivo.x - self._x_float
                dy = self.pareja_objetivo.y - self._y_float
                dist = math.sqrt(dx**2 + dy**2)

                if dist < 10: # Umbral de cercanía para reproducirse
                    # Reproducción instantánea
                    print(f"¡{self.nombre} y {self.pareja_objetivo.nombre} se han encontrado y reproducido!")
                    self._dar_a_luz()
                    # self._energia -= 30 # Coste de energía por reproducirse (eliminado)
                    
                    # Ambos vuelven a deambular
                    self.pareja_objetivo.estado = "deambulando"
                    self.pareja_objetivo.pareja_objetivo = None
                    self.estado = "deambulando"
                    self.pareja_objetivo = None
                    return # Terminar actualización de este tick tras reproducir
                else:
                    self._x_float += (dx / dist) * self.velocidad
                    self._y_float += (dy / dist) * self.velocidad
            else:
                # La pareja ya no está disponible
                self.estado = "deambulando"
                self.pareja_objetivo = None
        elif self.estado == "buscando_comida":
            # Lógica para comer hierba si no es carnívoro
            if not isinstance(self, Carnivoro):
                grid_x = self.x // CELL_SIZE
                grid_y = self.y // CELL_SIZE
                
                # Asegurarse de que las coordenadas están dentro de los límites del grid
                if 0 <= grid_x < ecosistema.grid_width and 0 <= grid_y < ecosistema.grid_height:
                    if ecosistema.grid_hierba[grid_x][grid_y] > 10:
                        ecosistema.grid_hierba[grid_x][grid_y] -= 10
                        self._energia = min(self.max_energia, self._energia + 15)
                        print(f"{self.nombre} ha comido hierba.")
                    else:
                        print(f"{self.nombre} intentó comer, pero no hay suficiente hierba aquí.")
                else:
                    print(f"{self.nombre} está fuera de los límites del grid para comer.")
            
            # Después de intentar comer (o si es carnívoro), vuelve a deambular
            self.estado = "deambulando"
        elif self.estado == "cazando_pez":
            if self.objetivo_comida and isinstance(self.objetivo_comida, Rio):
                rio = self.objetivo_comida
                # Moverse hacia el borde del río
                target_x, target_y = rio.rect.centerx, rio.rect.centery # Simplificación: ir al centro
                dx, dy = target_x - self._x_float, target_y - self._y_float
                dist = math.sqrt(dx**2 + dy**2)

                if dist < 40: # Si está cerca del río
                    # Buscar un pez en el río
                    pez_cercano = next((p for p in rio.peces if not p.fue_comido and math.sqrt((self.x - p.x)**2 + (self.y - p.y)**2) < 50), None)
                    if pez_cercano:
                        print(f"{self.nombre} ha cazado un pez!")
                        pez_cercano.fue_comido = True
                        self._energia = min(self.max_energia, self._energia + pez_cercano.energia)
                        self.estado = "deambulando"
                        self.objetivo_comida = None
                    else: # No hay peces cerca, vuelve a deambular
                        self.estado = "deambulando"
                else: # Moverse hacia el río
                    self._x_float += (dx / dist) * self.velocidad
                    self._y_float += (dy / dist) * self.velocidad

        elif self.estado == "yendo_a_cazar":
            if self.objetivo_puente:
                px, py = self.objetivo_puente
                dx, dy = px - self._x_float, py - self._y_float
                dist = math.sqrt(dx**2 + dy**2)
                if dist < 10:
                    # Ha llegado al puente, ahora puede empezar a cazar
                    self.estado = "deambulando"
                    self.puente_cruzado = self.objetivo_puente # Recuerda el puente que cruzó
                    self.objetivo_puente = None
                else:
                    self._x_float += (dx / dist) * self.velocidad
                    self._y_float += (dy / dist) * self.velocidad
            else: # No se asignó puente, volver a deambular
                self.estado = "deambulando"

        elif self.estado == "regresando_de_cazar":
            if self.objetivo_puente:
                px, py = self.objetivo_puente
                dx, dy = px - self._x_float, py - self._y_float
                dist = math.sqrt(dx**2 + dy**2)
                if dist < 10:
                    # Ha llegado al puente, ahora puede regresar a su zona
                    self.estado = "regresando_a_zona"
                    self.puente_cruzado = None # Olvida el puente al regresar a su lado
                    self.objetivo_puente = None
                else:
                    self._x_float += (dx / dist) * self.velocidad
                    self._y_float += (dy / dist) * self.velocidad
            else: # No se asignó puente, simplemente intentar regresar a la zona
                self.estado = "regresando_a_zona"
        
        elif self.estado == "cazando_herbivoro":
            if self.objetivo_comida and self.objetivo_comida.esta_vivo:
                # Moverse hacia la presa
                dx = self.objetivo_comida.x - self._x_float
                dy = self.objetivo_comida.y - self._y_float
                dist = math.sqrt(dx**2 + dy**2)

                if dist < 10: # Si está cerca, ataca
                    print(f"¡{self.nombre} ha cazado a {self.objetivo_comida.nombre}!")
                    # La presa pierde energía, el cazador gana
                    energia_ganada = self.objetivo_comida.energia * 0.8
                    self.objetivo_comida._energia = 0 # La presa muere
                    self._energia = min(self.max_energia, self._energia + energia_ganada)
                    
                    # Vuelve a deambular (en la zona de caza)
                    self.estado = "deambulando"
                    self.objetivo_comida = None
                else:
                    self._x_float += (dx / dist) * self.velocidad
                    self._y_float += (dy / dist) * self.velocidad
            else: # La presa murió o desapareció, buscar otra o deambular
                self.estado = "deambulando"
                self.objetivo_comida = None

        elif self.estado == "regresando_a_zona":
            zona_x, zona_y, zona_w, zona_h = self._obtener_zona_deambulacion()
            if zona_x <= self.x < zona_x + zona_w and zona_y <= self.y < zona_y + zona_h:
                # Ya está en su zona, vuelve a deambular normal
                self.estado = "deambulando"
            else:
                self.deambular() # Usa deambular para moverse hacia su zona

        elif self.estado == "deambulando":
            self.deambular()

        self._energia -= 0.05 # Coste base por hora
        self._energia = max(0, self._energia)

        if self._energia <= 0:
            ecosistema.agregar_carcasa(self.x, self.y)
            self.reproducir_sonido(3) #Reproducir sonido al morir

# --- Tipos de Animales ---

class Herbivoro(Animal):
    def actualizar(self, ecosistema):
        # Lógica de decisión para herbívoros
        if self.estado == "deambulando" and self.energia < self.max_energia * 0.7:
            # Si tiene hambre, busca comida (hierba)
            self.estado = "buscando_comida"
            # La lógica de 'actualizar' en la clase Animal se encargará de comer hierba.

        # Ejecutar la lógica normal de Animal
        super().actualizar(ecosistema)

class Carnivoro(Animal):
    def _buscar_presas(self, ecosistema):
        """Lógica de búsqueda de presas para carnívoros y omnívoros."""
        if self.modo_caza_activado and self.energia < self.max_energia * 0.8:
            # Modo caza activado: buscar herbívoros cercanos
            presas_cercanas = [
                animal for animal in ecosistema.obtener_animales_cercanos(self.x, self.y, radio=15)
                if isinstance(animal, Herbivoro)
            ]
            if presas_cercanas:
                presa_elegida = random.choice(presas_cercanas)
                print(f"{self.nombre} ha detectado a {presa_elegida.nombre} y va a cazarlo.")
                self.estado = "cazando_herbivoro"
                self.objetivo_comida = presa_elegida
                return True # Presa encontrada

        elif not self.modo_caza_activado and self.energia < self.max_energia * 0.5:
            # Modo caza desactivado: buscar peces si tiene hambre
            grid_x, grid_y = self.x // CELL_SIZE, self.y // CELL_SIZE
            if (grid_x, grid_y) in ecosistema.terrain_cache["rio"]:
                rio_cercano = ecosistema.terrain_cache["rio"][(grid_x, grid_y)]
                if rio_cercano and any(not p.fue_comido for p in rio_cercano.peces):
                    print(f"{self.nombre} tiene hambre y va a cazar peces al río.")
                    self.estado = "cazando_pez"
                    self.objetivo_comida = rio_cercano
                    return True # Presa encontrada
        return False # No se encontró presa

    def actualizar(self, ecosistema):
        # Lógica de decisión para carnívoros
        if self.estado == "deambulando":
            if self._buscar_presas(ecosistema):
                # Si se encontró una presa, la lógica de estado de Animal se encargará del resto.
                pass
        
        # Si no se tomó una decisión especial, ejecutar la lógica normal de Animal
        super().actualizar(ecosistema)

class Omnivoro(Animal):
    def actualizar(self, ecosistema):
        # Primero, intenta comportarse como un carnívoro
        if self.estado == "deambulando":
            # Llama a la lógica de búsqueda de presas refactorizada
            Carnivoro._buscar_presas(self, ecosistema)

        # Si después de la lógica de caza sigue deambulando y tiene hambre, busca hierba.
        if self.estado == "deambulando" and self.energia < self.max_energia * 0.7:
            self.estado = "buscando_comida"

        # Ejecutar la lógica de estado principal de la clase Animal (movimiento, comer hierba, etc.)
        super().actualizar(ecosistema)