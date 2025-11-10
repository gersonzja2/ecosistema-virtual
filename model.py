from abc import ABC, abstractmethod
import pygame
import json
import math
import random
import os
# === BEGIN SOUNDBANK ===
class SoundBank:
    """
    Carga perezosa/cache de 3 sonidos por especie:
    1=aparece, 2=camina, 3=muere
    Busca en 'assets' y 'assets/Sonidos listos'.
    """
    _cache = {}
    _folders = ["assets", os.path.join("assets", "Sonidos listos")]

    # Mapa nombre de clase -> prefijo de archivo
    _alias = {
        "Cabra": "cabra",
        "Raton": "rata",      # clase Raton usa archivos "rata X.wav"
        "Halcon": "halcon",
        "Leopardo": "leopardo",
        "Conejo": "conejo",
        "Cerdo": "cerdo",
        "Mono": "mono",
        "Gato": "gato",
    }

    @classmethod
    def _find_file(cls, base, idx):
        candidates = [f"{base} {idx}.wav", f"{base}{idx}.wav", f"{base}_{idx}.wav"]
        for folder in cls._folders:
            for name in candidates:
                path = os.path.join(folder, name)
                if os.path.isfile(path):
                    return path
        return None

    @classmethod
    def get_for(cls, class_name):
        if class_name not in cls._alias:
            return [None, None, None]
        key = cls._alias[class_name]
        if key in cls._cache:
            return cls._cache[key]

        sounds = [None, None, None]
        if pygame.mixer.get_init():
            for i in (1, 2, 3):
                path = cls._find_file(key, i)
                if path:
                    try:
                        s = pygame.mixer.Sound(path)
                        s.set_volume(0.65)  # volumen base
                        sounds[i-1] = s
                    except Exception as e:
                        print(f"[SoundBank] No se pudo cargar {path}: {e}")
                        sounds[i-1] = None
        cls._cache[key] = sounds
        return sounds
# === END SOUNDBANK ===


SIM_WIDTH = 800
SCREEN_HEIGHT = 700
CELL_SIZE = 20
MAX_HIERBA_NORMAL = 70
BORDE_MARGEN = 20 # Margen de seguridad para que los animales no se acerquen a los bordes
MAX_HIERBA_PRADERA = 120

class Terreno:
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)

class Carcasa:
    def __init__(self, x, y, energia_restante=60):
        self.x = x
        self.y = y
        self.energia_restante = energia_restante
        self.dias_descomposicion = 0

class Pez:
    def __init__(self, x, y, rio=None):
        self.x = x
        self.y = y
        self.rio = rio
        self.energia = 50
        self.fue_comido = False
        self.velocidad = 1
        self.direccion = random.uniform(0, 2 * math.pi)

    def actualizar(self):
        """Mueve el pez y lo mantiene dentro de los límites de su río."""
        if self.fue_comido:
            return

        # Mover el pez
        self.x += self.velocidad * math.cos(self.direccion)
        self.y += self.velocidad * math.sin(self.direccion)

        # Rebotar en los bordes del río
        if not self.rio.rect.collidepoint(self.x, self.y):
            self.x = max(self.rio.rect.left, min(self.x, self.rio.rect.right))
            self.y = max(self.rio.rect.top, min(self.y, self.rio.rect.bottom))
            # Cambiar de dirección al chocar
            self.direccion = random.uniform(0, 2 * math.pi)

class Rio(Terreno):
    def __init__(self, rect):
        super().__init__(rect)
        self.max_peces = 20
        self.peces = []
        self._generar_peces_iniciales()

    def _generar_peces_iniciales(self):
        for _ in range(10):
            x = random.randint(self.rect.left + 5, self.rect.right - 5)
            y = random.randint(self.rect.top + 5, self.rect.bottom - 5)
            pez = Pez(x, y, self)
            self.peces.append(pez)

    def crecer_recursos(self, factor_crecimiento):
        if len(self.peces) < 50:
            if random.random() < 0.1 * factor_crecimiento:
                x = random.randint(self.rect.left + 5, self.rect.right - 5)
                y = random.randint(self.rect.top + 5, self.rect.bottom - 5)
                self.peces.append(Pez(x, y, self))

class Selva(Terreno):
    def __init__(self, rect):
        super().__init__(rect)
        self.bayas = 25

    def crecer_recursos(self, factor_crecimiento):
        self.bayas += int(3 * factor_crecimiento)

class Pradera(Terreno):
    def __init__(self, rect):
        super().__init__(rect)
        self.max_hierba = MAX_HIERBA_PRADERA
        self.tasa_crecimiento = 2

class Animal(ABC):
    contador = 0

    def __init__(self, nombre: str, x: int, y: int, edad: int = 0, energia: int = 100, max_energia=None):
        self._nombre = nombre
        self._x_float = float(x)
        self._y_float = float(y)
        self._edad = max(0, edad)
        self._sed = 0
        if max_energia is None:
            max_energia = max(80, min(120, 100 + random.randint(-10, 10)))
        self.max_energia = max_energia
        self._energia = max(0, min(energia, self.max_energia))
        self._esta_vivo = True
        self.estado = "deambulando" # Estados: deambulando, buscando_comida, buscando_agua, cazando, huyendo
        self.objetivo = None  # Puede ser una tupla (x,y) o un objeto Animal
                # === BEGIN AUDIO FIELDS ===
        self.sonidos = SoundBank.get_for(type(self).__name__)
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
                        ecosistema.hierba_cambio = True
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

class Herbivoro(Animal):
    pass

class Carnivoro(Animal):
    def actualizar(self, ecosistema):
        # Lógica de decisión para carnívoros
        if self.estado == "deambulando":
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
                    super().actualizar(ecosistema) # Llama a la lógica de persecución
                    return 

            elif not self.modo_caza_activado and self.energia < self.max_energia * 0.5:
                # Modo caza desactivado: buscar peces si tiene hambre
                grid_x, grid_y = self.x // CELL_SIZE, self.y // CELL_SIZE
                if (grid_x, grid_y) in ecosistema.terrain_cache["rio"]:
                    rio_cercano = ecosistema.terrain_cache["rio"][(grid_x, grid_y)]
                    if rio_cercano and any(not p.fue_comido for p in rio_cercano.peces):
                        print(f"{self.nombre} tiene hambre y va a cazar peces al río.")
                        self.estado = "cazando_pez"
                        self.objetivo_comida = rio_cercano
                        super().actualizar(ecosistema)
                        return



        # Si no se tomó una decisión especial, ejecutar la lógica normal de Animal
        super().actualizar(ecosistema)

class Omnivoro(Animal):
    pass

class Conejo(Herbivoro):
    def __init__(self, nombre: str, x: int, y: int, edad: int = 0, energia: int = 100, max_energia=None):
        if max_energia is None:
            max_energia = max(70, min(90, 80 + random.randint(-5, 5)))
        super().__init__(nombre, x, y, edad, energia, max_energia)

class Cabra(Herbivoro):
    def __init__(self, nombre: str, x: int, y: int, edad: int = 0, energia: int = 100, max_energia=None):
        if max_energia is None:
            max_energia = max(90, min(110, 100 + random.randint(-5, 5)))
        super().__init__(nombre, x, y, edad, energia, max_energia)
        
class Raton(Herbivoro):
    def __init__(self, nombre: str, x: int, y: int, edad: int = 0, energia: int = 100, max_energia=None):
        if max_energia is None:
            max_energia = max(30, min(50, 40 + random.randint(-5, 5)))
        super().__init__(nombre, x, y, edad, energia, max_energia)

class Insecto(Herbivoro):
    def __init__(self, nombre: str, x: int, y: int, edad: int = 0, energia: int = 100, max_energia=None):
        if max_energia is None:
            max_energia = max(30, min(50, 40 + random.randint(-5, 5)))
        super().__init__(nombre, x, y, edad, energia, max_energia)

class Leopardo(Carnivoro):
    def __init__(self, nombre: str, x: int, y: int, edad: int = 0, energia: int = 100, max_energia=None):
        if max_energia is None:
            max_energia = max(100, min(120, 110 + random.randint(-5, 5)))
        super().__init__(nombre, x, y, edad, energia, max_energia)

class Gato(Carnivoro):
    def __init__(self, nombre: str, x: int, y: int, edad: int = 0, energia: int = 100, max_energia=None):
        if max_energia is None:
            max_energia = max(75, min(95, 85 + random.randint(-5, 5)))
        super().__init__(nombre, x, y, edad, energia, max_energia)
        
class Halcon(Carnivoro):
    def __init__(self, nombre: str, x: int, y: int, edad: int = 0, energia: int = 100, max_energia=None):
        if max_energia is None:
            max_energia = max(70, min(90, 80 + random.randint(-5, 5)))
        super().__init__(nombre, x, y, edad, energia, max_energia)
        
class Cerdo(Omnivoro):
    def __init__(self, nombre: str, x: int, y: int, edad: int = 0, energia: int = 100, max_energia=None):
        if max_energia is None:
            max_energia = max(110, min(130, 120 + random.randint(-5, 5)))
        super().__init__(nombre, x, y, edad, energia, max_energia)
        
class Mono(Omnivoro):
    def __init__(self, nombre: str, x: int, y: int, edad: int = 0, energia: int = 100, max_energia=None):
        if max_energia is None:
            max_energia = max(80, min(100, 90 + random.randint(-5, 5)))
        super().__init__(nombre, x, y, edad, energia, max_energia)
        
class Ecosistema:
    def __init__(self):
        # Carga el sonido del río
        self.sonido_rio = pygame.mixer.Sound("assets/Sonidos listos/rio 1.wav")  # Ajusta la ruta si es necesario
        self.sonido_rio.set_volume(1.5)# Ajusta el volumen si es necesario
        # Otros atributos del ecosistema
        self.animales = []
        self.clima_actual = "Soleado"  # Clima inicial
        self._ticks_clima = 0  # Contador de clima

    def reproducir_sonido_rio(self):
        """Reproduce el sonido del río en bucle"""
        self.sonido_rio.play(-1)  # -1 para hacer que suene en bucle

    def __init__(self):
        self.tipos_de_animales = [Conejo, Raton, Cabra, Leopardo, Gato, Cerdo, Mono, Halcon, Insecto]
        self.animales: list[Animal] = []
        self.terreno = {
            "praderas": [
                Pradera((50, 50, 250, 150)),      # Pradera en la esquina superior izquierda
                Pradera((500, 80, 200, 100)),     # Pradera en la zona superior derecha
                Pradera((50, 450, 250, 200)),     # Gran pradera en la esquina inferior izquierda
                Pradera((550, 480, 200, 150)),    # Pradera en la esquina inferior derecha
            ],
            "rios": [],
            "selvas": [
                Selva((350, 500, 150, 100)),      # Pequeña selva en la parte inferior central
            ],
            "montanas": [],
            "santuarios": [],
            "arboles": [],
            "plantas": [],
            "plantas_2": [],
            "puentes": []
        }
        self.recursos = {
            "carcasas": []
        }
        self.grid_width = SIM_WIDTH // CELL_SIZE
        self.grid_height = SCREEN_HEIGHT // CELL_SIZE
        self.grid_hierba = [[0 for _ in range(self.grid_height)] for _ in range(self.grid_width)]
        self.terrain_grid = [[None for _ in range(self.grid_height)] for _ in range(self.grid_width)]
        self.is_river = [[False for _ in range(self.grid_height)] for _ in range(self.grid_width)]

        # Construir ríos nuevos: pool central + brazos hacia esquinas (aproximación con rects)
        # Parámetros geométricos
        center_x = SIM_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2
        thickness = 60

        # Área central donde confluyen los ríos
        pool = Rio((center_x - thickness // 2, center_y - thickness // 2, thickness, thickness))

        # Brazo izquierdo horizontal: desde el borde izquierdo hasta la izquierda del pool
        left_arm = Rio((0, center_y - thickness // 2, center_x - thickness // 2, thickness))

        # Brazo derecho horizontal: desde la derecha del pool hasta el borde derecho
        right_arm = Rio((center_x + thickness // 2, center_y - thickness // 2, SIM_WIDTH - (center_x + thickness // 2), thickness))

        # Brazo superior vertical: desde el borde superior hasta la parte superior del pool
        top_arm = Rio((center_x - thickness // 2, 0, thickness, center_y - thickness // 2))

        # Añadir a la lista de ríos
        self.terreno["rios"].extend([left_arm, right_arm, top_arm, pool])

        # Añadir puentes en ubicaciones estratégicas sobre los brazos horizontales
        self.terreno["puentes"].append((150, center_y))
        self.terreno["puentes"].append((SIM_WIDTH - 150, center_y))
        self.terreno["puentes"].append((SIM_WIDTH // 4, center_y))
        self.terreno["puentes"].append((center_x + 2, 150)) # Nuevo puente en el río superior, movido 2px a la derecha

        # Establecer la jerarquía de terrenos (el primero tiene más prioridad)
        terrain_hierarchy = [
            ("montanas", "montana"),
            ("santuarios", "santuario"),
            ("selvas", "selva"),
            ("praderas", "pradera")
        ]

        for gx in range(self.grid_width):
            for gy in range(self.grid_height):
                cell_rect = pygame.Rect(gx * CELL_SIZE, gy * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                
                if any(rio.rect.colliderect(cell_rect) for rio in self.terreno["rios"]):
                    self.grid_hierba[gx][gy] = 0
                    self.terrain_grid[gx][gy] = "rio" # Marcar como río
                    self.is_river[gx][gy] = True
                    continue

                # Asignar tipo de terreno basado en la jerarquía
                for terrain_list_name, terrain_type_name in terrain_hierarchy:
                    if any(t.rect.colliderect(cell_rect) for t in self.terreno[terrain_list_name]):
                        self.terrain_grid[gx][gy] = terrain_type_name
                        break
                
                # Calcular hierba inicial
                max_val = MAX_HIERBA_PRADERA if self.terrain_grid[gx][gy] == "pradera" else MAX_HIERBA_NORMAL
                self.grid_hierba[gx][gy] = random.randint(0, max_val)

        self.dia_total = 1
        self.hora_actual = 0
        self.clima_actual = "Normal"
        self.factor_crecimiento_base = 1.5 # Factor de crecimiento constante
        self.animales_nuevos = []
        self.hierba_cambio = False # Flag para optimización de renderizado

        self.grid_animales = {}
        self.modo_caza_carnivoro_activo = False
        self._poblar_decoraciones()
        self.terrain_cache = {"rio": {}, "selva": {}}
        self._precalcular_terrenos_cercanos()

    def choca_con_terreno(self, x, y):
        radio_tronco = 5
        return any(math.sqrt((ax - x)**2 + (ay - y)**2) < radio_tronco for ax, ay in self.terreno["arboles"])

    def agregar_carcasa(self, x, y):
        if not self.choca_con_terreno(x, y):
            nueva_carcasa = Carcasa(x, y)
            self.recursos["carcasas"].append(nueva_carcasa)
    
    def _es_posicion_valida_para_vegetacion(self, x, y, decoraciones_existentes, min_dist):
        if any(rio.rect.collidepoint(x, y) for rio in self.terreno["rios"]):
            return False
        for px, py in self.terreno["puentes"]:
            if math.sqrt((x - px)**2 + (y - py)**2) < 40: # Distancia de seguridad alrededor de los puentes
                return False
        return self._es_posicion_decoracion_valida(x, y, decoraciones_existentes, min_dist)

    def _es_posicion_decoracion_valida(self, x, y, decoraciones_existentes, min_dist):
        for dx, dy in decoraciones_existentes:
            dist = math.sqrt((x - dx)**2 + (y - dy)**2)
            if dist < min_dist:
                return False
        return True

    def _poblar_decoraciones(self):
        self.terreno["arboles"].clear()
        self.terreno["plantas"] = []
        self.terreno["plantas_2"] = []
        
        decoraciones_todas = []
        intentos_max = 80
        margen = 10

        # Poblar árboles densamente en las selvas
        for selva in self.terreno["selvas"]:
            for _ in range(40): # Número de árboles por selva
                for _ in range(intentos_max):
                    x = random.randint(selva.rect.left + margen, selva.rect.right - margen)
                    y = random.randint(selva.rect.top + margen, selva.rect.bottom - margen)
                    if self._es_posicion_valida_para_vegetacion(x, y, decoraciones_todas, min_dist=25):
                        self.terreno["arboles"].append((x, y)); decoraciones_todas.append((x, y))
                        break

        # Poblar algunos árboles en las praderas
        for pradera in self.terreno["praderas"]:
            for _ in range(15): # Número de árboles por pradera
                for _ in range(intentos_max):
                    x = random.randint(pradera.rect.left + margen, pradera.rect.right - margen)
                    y = random.randint(pradera.rect.top + margen, pradera.rect.bottom - margen)
                    if self._es_posicion_valida_para_vegetacion(x, y, decoraciones_todas, min_dist=30):
                        self.terreno["arboles"].append((x, y)); decoraciones_todas.append((x, y))
                        break
        
        # Poblar plantas en grupos sobre el fondo
        num_grupos_plantas = 15
        plantas_por_grupo = 10
        radio_grupo = 40

        for _ in range(num_grupos_plantas):
            # Elegir un centro para el grupo que no esté en un terreno ya definido
            for _ in range(intentos_max):
                centro_x = random.randint(margen, SIM_WIDTH - margen)
                centro_y = random.randint(margen, SCREEN_HEIGHT - margen)
                if not self.choca_con_terreno(centro_x, centro_y) and self.terrain_grid[centro_x // CELL_SIZE][centro_y // CELL_SIZE] is None:
                    break
            
            for _ in range(plantas_por_grupo):
                x = centro_x + random.randint(-radio_grupo, radio_grupo)
                y = centro_y + random.randint(-radio_grupo, radio_grupo)
                if self._es_posicion_valida_para_vegetacion(x, y, decoraciones_todas, min_dist=10):
                    self.terreno["plantas"].append((x, y)); decoraciones_todas.append((x, y))
        
        # Poblar plantas_2 en grupos sobre el fondo
        num_grupos_plantas_2 = 12
        plantas_por_grupo_2 = 8
        radio_grupo_2 = 35

        for _ in range(num_grupos_plantas_2):
            # Elegir un centro para el grupo que no esté en un terreno ya definido
            for _ in range(intentos_max):
                centro_x = random.randint(margen, SIM_WIDTH - margen)
                centro_y = random.randint(margen, SCREEN_HEIGHT - margen)
                if not self.choca_con_terreno(centro_x, centro_y) and self.terrain_grid[centro_x // CELL_SIZE][centro_y // CELL_SIZE] is None:
                    break
            
            for _ in range(plantas_por_grupo_2):
                x = centro_x + random.randint(-radio_grupo_2, radio_grupo_2)
                y = centro_y + random.randint(-radio_grupo_2, radio_grupo_2)
                if self._es_posicion_valida_para_vegetacion(x, y, decoraciones_todas, min_dist=10):
                    self.terreno["plantas_2"].append((x, y)); decoraciones_todas.append((x, y))

    def _precalcular_terrenos_cercanos(self):
        print("Precalculando caché de terrenos cercanos para optimización...")
        for gx in range(self.grid_width):
            for gy in range(self.grid_height):
                x, y = gx * CELL_SIZE, gy * CELL_SIZE
                
                mejor_rio, menor_dist_rio_sq = None, float('inf')
                for rio in self.terreno["rios"]:
                    dist_sq = (x - rio.rect.centerx)**2 + (y - rio.rect.centery)**2
                    if dist_sq < menor_dist_rio_sq:
                        menor_dist_rio_sq, mejor_rio = dist_sq, rio
                if mejor_rio: self.terrain_cache["rio"][(gx, gy)] = mejor_rio

                mejor_selva, menor_dist_selva_sq = None, float('inf')
                for selva in self.terreno["selvas"]:
                    dist_sq = (x - selva.rect.centerx)**2 + (y - selva.rect.centery)**2
                    if dist_sq < menor_dist_selva_sq:
                        menor_dist_selva_sq, mejor_selva = dist_sq, selva
                if mejor_selva: self.terrain_cache["selva"][(gx, gy)] = (mejor_selva, menor_dist_selva_sq)

    def _actualizar_clima(self):
        if random.random() < 0.05:
            self.clima_actual = "Sequía"
        else:
            self.clima_actual = "Normal"

    def _actualizar_grid_animales(self):
        self.grid_animales.clear()
        for animal in self.animales:
            grid_x = int(animal.x // CELL_SIZE)
            grid_y = int(animal.y // CELL_SIZE)
            key = (grid_x, grid_y)
            if key not in self.grid_animales:
                self.grid_animales[key] = []
            self.grid_animales[key].append(animal)

    def obtener_animales_cercanos(self, x, y, radio=2):
        """Obtiene los animales cercanos a una posición"""
        grid_x = int(x // CELL_SIZE)
        grid_y = int(y // CELL_SIZE)
        cercanos = []
        for dx in range(-radio, radio + 1):
            for dy in range(-radio, radio + 1):
                key = (grid_x + dx, grid_y + dy)
                if key in self.grid_animales:
                    cercanos.extend(self.grid_animales[key])
        return cercanos

    def simular_hora(self):
        self._actualizar_grid_animales()

        self.hora_actual += 1

        if self.hora_actual >= 24:
            self.hora_actual = 0
            self.dia_total += 1
            self._actualizar_clima()

            factor_crecimiento = self.factor_crecimiento_base
            if self.clima_actual == "Sequía":
                factor_crecimiento *= 0.1

            for gx in range(self.grid_width):
                for gy in range(self.grid_height):
                    if self.is_river[gx][gy]:
                        self.grid_hierba[gx][gy] = 0
                        continue

                    tasa_crecimiento_base = 1 
                    calidad_suelo_local = 1.0
                    max_capacidad = MAX_HIERBA_NORMAL
                    tasa_crecimiento_base = 1
                    
                    cell_rect = pygame.Rect(gx * CELL_SIZE, gy * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                    pradera_actual = next((p for p in self.terreno["praderas"] if p.rect.colliderect(cell_rect)), None)
                    if pradera_actual:
                        max_capacidad = pradera_actual.max_hierba
                        tasa_crecimiento_base = pradera_actual.tasa_crecimiento
                    crecimiento_real = int(tasa_crecimiento_base * factor_crecimiento * (1 - self.grid_hierba[gx][gy] / max_capacidad))
                    self.grid_hierba[gx][gy] += crecimiento_real
                    self.grid_hierba[gx][gy] = min(self.grid_hierba[gx][gy], max_capacidad)
            self.hierba_cambio = True # La hierba creció, necesita redibujarse
            
            for selva in self.terreno["selvas"]: selva.crecer_recursos(factor_crecimiento)
            for rio in self.terreno["rios"]: rio.crecer_recursos(factor_crecimiento)

            for c in self.recursos["carcasas"]: c.dias_descomposicion += 1
            self.recursos["carcasas"] = [c for c in self.recursos["carcasas"] if c.dias_descomposicion < 5]

            for animal in self.animales:
                animal._edad += 1

            self.animales_nuevos = []

        self.animales.extend(self.animales_nuevos)
        
        # Actualizar estado de cada animal
        for animal in self.animales:
            animal.actualizar(self)

        # Eliminar animales muertos de la simulación
        self.animales = [animal for animal in self.animales if animal.esta_vivo]

        # Actualizar peces en cada río
        for rio in self.terreno["rios"]:
            for pez in rio.peces:
                pez.actualizar()
        
    def _obtener_posicion_inicial(self, tipo_animal):
        """Determina la posición inicial para un nuevo animal basado en su tipo."""
        intentos = 0
        center_x = SIM_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2
        thickness = 60
        
        rio_borde_izq = center_x - thickness // 2
        rio_borde_der = center_x + thickness // 2
        rio_borde_sup = center_y - thickness // 2

        while intentos < 100:
            if issubclass(tipo_animal, Carnivoro):
                # Cuadrante superior izquierdo
                x = random.randint(BORDE_MARGEN, rio_borde_izq - BORDE_MARGEN)
                y = random.randint(BORDE_MARGEN, rio_borde_sup - BORDE_MARGEN)
            elif issubclass(tipo_animal, Herbivoro):
                # Cuadrante inferior
                x = random.randint(BORDE_MARGEN, SIM_WIDTH - BORDE_MARGEN)
                y = random.randint(rio_borde_sup + thickness, SCREEN_HEIGHT - BORDE_MARGEN)
            elif issubclass(tipo_animal, Omnivoro):
                # Cuadrante superior derecho
                x = random.randint(rio_borde_der + BORDE_MARGEN, SIM_WIDTH - BORDE_MARGEN)
                y = random.randint(BORDE_MARGEN, rio_borde_sup - BORDE_MARGEN)
            
            if not self.choca_con_terreno(x, y) and not any(rio.rect.collidepoint(x, y) for rio in self.terreno["rios"]):
                return x, y
            intentos += 1
        return random.randint(20, SIM_WIDTH - 20), random.randint(20, SCREEN_HEIGHT - 20) # Fallback

    def agregar_animal(self, tipo_animal, nombre=None, es_cria=False, pos=None):
        if es_cria:
            if pos:
                # La cría aparece cerca de la madre
                x = pos[0] + random.randint(-10, 10)
                y = pos[1] + random.randint(-10, 10)
            else: # Fallback si no se da posición
                x, y = self._obtener_posicion_inicial(tipo_animal)
            nombre = f"Cría de {tipo_animal.__name__}"
            nuevo_animal = tipo_animal(nombre, x, y, edad=-1) # Edad -1 para que en el siguiente ciclo de día se ponga a 0
        else:
            if nombre is None:
                nombre = f"{tipo_animal.__name__} {getattr(tipo_animal, 'contador', 0) + 1}"
            x, y = self._obtener_posicion_inicial(tipo_animal)
            nuevo_animal = tipo_animal(nombre, x, y)
            
        nuevo_animal.ecosistema = self # Asignar referencia al ecosistema
        self.animales.append(nuevo_animal)
                # Sonido de aparición
        if hasattr(nuevo_animal, "reproducir_sonido"):
            nuevo_animal.reproducir_sonido(1)


    def activar_modo_caza_carnivoro(self):
        self.modo_caza_carnivoro_activo = not self.modo_caza_carnivoro_activo
        for animal in self.animales:
            if isinstance(animal, Carnivoro):
                animal.modo_caza_activado = self.modo_caza_carnivoro_activo
                
                if self.modo_caza_carnivoro_activo:
                    # Encontrar el puente más cercano para cruzar
                    puentes_caza = [p for p in self.terreno["puentes"] if p[1] > 300] # Puentes horizontales
                    if not puentes_caza:
                        animal.objetivo_puente = None
                    else:
                        puente_cercano = min(puentes_caza, key=lambda p: (animal.x - p[0])**2 + (animal.y - p[1])**2)
                        animal.objetivo_puente = puente_cercano

                    print(f"{animal.nombre} entra en modo caza y se dirige a la zona de herbívoros.")
                    if animal.objetivo_puente:
                        animal.estado = "yendo_a_cazar"
                    else: # Si no hay puentes, deambula como antes
                        animal.estado = "deambulando"
                else:
                    print(f"{animal.nombre} sale del modo caza y regresa a su territorio.")
                    # Usar el puente que cruzó para regresar, si lo recuerda
                    animal.objetivo_puente = animal.puente_cruzado
                    if animal.objetivo_puente:
                        animal.estado = "regresando_de_cazar"
                    else:
                        animal.estado = "regresando_a_zona"
                    animal.objetivo_comida = None # Cancela cualquier caza actual

    def guardar_estado(self, archivo="save_state.json"):
        estado = {
            "dia_total": self.dia_total,
            "grid_hierba": self.grid_hierba,
            "selvas": [{"rect": list(s.rect), "bayas": s.bayas} for s in self.terreno["selvas"]],
            "rios": [{"rect": list(r.rect), "num_peces": len(r.peces)} for r in self.terreno["rios"]],
            "animales": [
                {
                    "tipo": a.__class__.__name__,
                    "nombre": a.nombre, "x": a.x, "y": a.y, "edad": a.edad,
                    "energia": a.energia, "sed": a._sed, "max_energia": a.max_energia
                }
                for a in self.animales
            ]
        }
        with open(archivo, 'w') as f:
            json.dump(estado, f, indent=4)

    def cargar_estado(self, archivo="save_state.json"):
        with open(archivo, 'r') as f:
            estado = json.load(f)

        self.dia_total = estado["dia_total"]
        self.grid_hierba = estado.get("grid_hierba", self.grid_hierba)
        for i, s_data in enumerate(estado["selvas"]):
            self.terreno["selvas"][i].bayas = s_data["bayas"]
        
        for i, r_data in enumerate(estado.get("rios", [])):
            rio = self.terreno["rios"][i]
            rio.peces = []
            for _ in range(r_data.get("num_peces", 20)):
                x = random.randint(rio.rect.left + 5, rio.rect.right - 5)
                y = random.randint(rio.rect.top + 5, rio.rect.bottom - 5)
                rio.peces.append(Pez(x, y, rio))

        self.animales = []
        tipos = {"Herbivoro": Herbivoro, "Carnivoro": Carnivoro, "Omnivoro": Omnivoro, "Conejo": Conejo, "Raton": Raton, "Cabra": Cabra, "Leopardo": Leopardo, "Gato": Gato, "Cerdo": Cerdo, "Mono": Mono, "Halcon": Halcon, "Insecto": Insecto}
        for a_data in estado["animales"]:
            tipo_clase = tipos.get(a_data["tipo"])
            if tipo_clase:
                max_energia_default = max(80, min(120, 100 + random.randint(-10, 10)))
                animal = tipo_clase(a_data["nombre"], a_data["x"], a_data["y"], 
                                    a_data.get("edad", 0), a_data.get("energia", 100), 
                                    max_energia=a_data.get("max_energia", max_energia_default))
                animal._sed = a_data.get("sed", 0)
                self.animales.append(animal)