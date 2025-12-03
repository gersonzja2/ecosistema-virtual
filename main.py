import pygame
import os
import threading
from copy import deepcopy
from src.Logica.Logica import Ecosistema, Herbivoro, Carnivoro, Omnivoro, Conejo, Raton, Cabra, Leopardo, Gato, Cerdo, Mono, Halcon, Insecto
from src.Interfaz.Interfaz import PygameView
from src.Interfaz.Menu_view import Menu
import src.Persistencia.Persistencia as persistencia # Importamos el nuevo módulo

class SimulationController:
    def __init__(self, dias_simulacion: int):
        pygame.init()  # Asegurar que pygame está inicializado
        pygame.mixer.init() # Asegurar que el mixer está listo para la música del menú
        self.view = PygameView()
        self.ecosistema = Ecosistema()
        self.dias_simulacion = dias_simulacion
        
        # El controlador ahora es responsable de obtener los datos para el menú
        users = persistencia.obtener_lista_usuarios()
        self.menu = Menu(self.view.screen, self.view.font_header, self.view.font_normal, self.view.font_small, users)
        
        self.current_state = "MENU" # Estados: "MENU", "SIMULATION", "SAVING"
        self.pending_load_info = None # Almacena la información para la confirmación de carga
        self.save_path = None
        self.current_user = None
        
        self.autosave_interval = 30 # Días entre autoguardados. None para desactivado.
        self.is_autosaving = False # Flag para mostrar el icono
        self.trigger_autosave = False # Flag para iniciar el proceso de guardado en el bucle principal
        self.autosave_icon_end_time = None # Temporizador para la visibilidad del icono

        self.animal_seleccionado = None
        self.pareja_seleccionada = None
        self.paused = True
        
        self.sim_speed_multiplier = 3
        self.special_sound_channel = None # Canal para sonidos especiales PUNTUALES (reproducción, etc.)
        self.music_volume_before_fade = 0.2 # Almacena el volumen de la música antes de atenuarla

        self.base_time_per_hour = 50 # Ralentizamos un poco para mejor visualización
        self.last_update_time = pygame.time.get_ticks()
        self.clock = pygame.time.Clock()
        self._play_menu_music()
        # Asegurarse de que el botón de música refleje el estado inicial
        if "music" in self.view.buttons:
            self.view.buttons["music"].text = "Música ON"
        self._load_reproduction_sound()

    def _play_menu_music(self):
        """Carga y reproduce la música del menú."""
        try:
            pygame.mixer.music.load("assets/Ciclo Sin Fin.mp3")
            pygame.mixer.music.set_volume(0.2) # Volumen moderado para el menú
            pygame.mixer.music.play(-1)
        except pygame.error as e:
            print(f"No se pudo cargar la música del menú 'Ciclo Sin Fin.mp3': {e}")

    def _load_reproduction_sound(self):
        """Carga el sonido para el modo de reproducción."""
        self.reproduction_sound = None
        try:
            self.reproduction_sound = pygame.mixer.Sound("assets/reproduccion_1.mp3")
            self.reproduction_sound.set_volume(0.7) # Volumen más alto para destacar
        except pygame.error as e:
            print(f"No se pudo cargar el sonido de reproducción 'reproduccion_1.mp3': {e}")

    def _poblar_ecosistema(self):
        tipos_de_animales = [Conejo, Raton, Cabra, Leopardo, Gato, Cerdo, Mono, Halcon, Insecto]
        for tipo in tipos_de_animales:
            for _ in range(2):
                nuevo_animal = self.ecosistema.agregar_animal(tipo)
                self.view.play_animal_sound(nuevo_animal.__class__.__name__)

    def _avanzar_dia(self):
        for _ in range(24):
            self.ecosistema.simular_hora()
            if self.ecosistema.dia_total >= self.dias_simulacion or not self.ecosistema.animales:
                return True
        
        self._actualizar_grafico()
        return self.ecosistema.dia_total >= self.dias_simulacion or not self.ecosistema.animales
    
    def _actualizar_grafico(self):
        poblaciones = (
            sum(1 for a in self.ecosistema.animales if isinstance(a, Herbivoro)),
            sum(1 for a in self.ecosistema.animales if isinstance(a, Carnivoro)),
            sum(1 for a in self.ecosistema.animales if isinstance(a, Omnivoro))
        )
        self.view.graph.update(poblaciones)

    def _check_autosave(self):
        """Comprueba si debe activarse el autoguardado basado en el día actual."""
        if self.autosave_interval is not None and self.autosave_interval > 0:
            # Usamos el módulo para asegurarnos de que se active en los múltiplos exactos del intervalo.
            # Se activa en el día 30, 60, 90... para un intervalo de 30.
            if self.ecosistema.dia_total > 0 and self.ecosistema.dia_total % self.autosave_interval == 0:
                self.trigger_autosave = True # Activamos el trigger para el bucle principal

    def _avanzar_hora(self):
        self.ecosistema.simular_hora()
        if self.ecosistema.dia_total >= self.dias_simulacion or not self.ecosistema.animales:
            return True
        if self.ecosistema.hora_actual == 0:
            self._actualizar_grafico()
            self._check_autosave() # Comprobar si es día de autoguardado
        return self.ecosistema.dia_total >= self.dias_simulacion or not self.ecosistema.animales

    def _setup_button_actions(self):
        animal_map = {
            "conejo": Conejo, "raton": Raton, "cabra": Cabra,
            "leopardo": Leopardo, "gato": Gato, "halcon": Halcon,
            "cerdo": Cerdo, "mono": Mono, "insecto": Insecto
        }

        self.button_actions = {
            "save": self._action_save,
            "load": self._action_load,
            "music": self.view.toggle_music,
            "pause_resume": self._action_toggle_pause,
            "next_day": self._action_advance_day,
            "restart": self._action_restart,
            "save_as": self._action_save_as,
            "feed_herbivores": self._action_feed_all_herbivores,
            "force_reproduce": self._action_force_reproduce,
            "hunt": self._action_toggle_hunt_mode
        }

        # Mapeo dinámico para los botones de "añadir animal"
        for name, cls in animal_map.items():
            # La acción ahora también reproduce el sonido a través de la vista
            self.button_actions[f"add_{name}"] = lambda species=cls: \
                self.view.play_animal_sound(self.ecosistema.agregar_animal(species).__class__.__name__)

    def _save_in_background(self, save_path, sim_speed, autosave_interval):
        """
        Copia el ecosistema y lo guarda en un hilo separado para no bloquear la simulación.
        """
        ecosistema_copiado = deepcopy(self.ecosistema)
        persistencia.guardar_partida(ecosistema_copiado, save_path, autosave=True, sim_speed_multiplier=sim_speed, autosave_interval=autosave_interval)

        
    def _action_save(self, autosave=False):
        """Utiliza la clase Persistencia para guardar el estado del ecosistema."""
        if self.save_path:
            persistencia.guardar_partida(self.ecosistema, self.save_path, autosave=autosave, sim_speed_multiplier=self.sim_speed_multiplier, autosave_interval=self.autosave_interval)
        else:
            print("Error: No hay una ruta de guardado definida.")

    def _display_message(self, message, duration_ms=3000, is_error=False):
        """Muestra un mensaje temporal en la pantalla a través de la vista."""
        # Asume que PygameView tiene un método display_message(message, duration_ms, is_error)
        self.view.display_message(message, duration_ms, is_error)

    def _action_load(self):
        """Utiliza la clase Persistencia para cargar el estado del ecosistema.
        Devuelve True si la carga fue exitosa, False en caso contrario."""
        if not self.save_path:
            self._display_message("Error: No se ha seleccionado una ruta de guardado.", is_error=True)
            return False

        try:
            loaded_ecosystem, loaded_speed, loaded_autosave = persistencia.cargar_partida(self.save_path)
            if loaded_ecosystem:
                self.ecosistema = loaded_ecosystem
                self.view.graph.history.clear()
                # Restaurar configuraciones si se encontraron en el archivo de guardado
                if loaded_speed is not None:
                    self.sim_speed_multiplier = loaded_speed
                if loaded_autosave is not None:
                    self.autosave_interval = loaded_autosave

                # Restaurar configuraciones de la simulación desde el ecosistema cargado
                # Asegurarse de que el modo de caza se restaure correctamente
                # (el estado se guarda en el ecosistema, pero el botón de la vista necesita actualizarse)
                # Si el ecosistema cargado no tiene este atributo, se inicializará a False por defecto.
                if not hasattr(self.ecosistema, 'modo_caza_carnivoro_activo'):
                    self.ecosistema.modo_caza_carnivoro_activo = False
                
                # Restaurar el estado de caza y el sonido correspondiente.
                if self.ecosistema.modo_caza_carnivoro_activo:
                    self.view.buttons["hunt"].text = "Regresar Carnívoros"
                    # Al cargar, si el modo caza estaba activo, cambiamos la música a la de caza.
                    pygame.mixer.music.load("assets/atacar_1.mp3")
                    pygame.mixer.music.set_volume(0.25) # Volumen de caza
                    pygame.mixer.music.play(-1)
                else:
                    self.view.buttons["hunt"].text = "Cazar Herbívoros"
                    # Al cargar, si el modo caza no está activo, iniciamos la música normal.
                    self.view.start_simulation_music() # Asegura que se cargue la música correcta

                self._setup_button_actions() # Volver a configurar las acciones con el nuevo ecosistema
                self.view.needs_static_redraw = True
                self._display_message(f"Partida '{os.path.basename(self.save_path)}' cargada con éxito.", is_error=False)
                return True # Carga exitosa
            else:
                # This 'else' branch is for when persistencia.cargar_partida returns (None, None, None)
                # without raising an explicit exception, indicating a general failure or file not found.
                error_message = f"Error al cargar la partida '{os.path.basename(self.save_path)}'. El archivo podría estar corrupto o no existe."
                self._display_message(error_message, duration_ms=5000, is_error=True)
                # No cambiamos el ecosistema, simplemente fallamos la carga y el controlador volverá al menú.
                return False # Carga fallida o archivo no existe
        except FileNotFoundError:
            error_message = f"Error: El archivo de partida '{os.path.basename(self.save_path)}' no se encontró."
            self._display_message(error_message, duration_ms=5000, is_error=True)
            # No es necesario crear un nuevo ecosistema aquí, ya que la carga falló.
            # El controlador manejará el regreso al menú.
            return False
        except Exception as e:
            # Catch any other unexpected errors during loading, e.g., JSON parsing errors
            error_message = f"Error inesperado al cargar la partida '{os.path.basename(self.save_path)}': {e}"
            self.ecosistema = Ecosistema()
            self._setup_button_actions()
            self._display_message(error_message, is_error=True)
            return False

    def _action_restart(self):
        self.ecosistema = Ecosistema()
        self._poblar_ecosistema()
        self.view.graph.history.clear()
        self.animal_seleccionado = None
        self.pareja_seleccionada = None
        self.view.needs_static_redraw = True
        self.paused = True
        # No es necesario reiniciar sim_over aquí, ya que se gestiona en el bucle principal.
        print("Simulación reiniciada a su estado inicial.")

    def _action_save_as(self):
        """Inicia el modo 'Guardar como...'."""
        self.current_state = "SAVING"
        self.paused = True # Pausar la simulación mientras se guarda
        # Preparar el menú de guardado
        self.save_menu_saves = persistencia.obtener_partidas_usuario(self.current_user)
        self.save_menu_input = ""

        # Asegurarse de que la partida actual (especialmente si es nueva) esté en la lista para ser mostrada.
        current_save_name = os.path.basename(self.save_path) if self.save_path else None
        # Comprobar si el nombre de archivo ya existe en la lista de diccionarios
        if current_save_name and not any(d.get('filename') == current_save_name for d in self.save_menu_saves):
            # Si la partida actual no está en la lista (porque es nueva y no se ha guardado), la añadimos.
            # La añadimos como un diccionario para mantener la consistencia de la lista.
            self.save_menu_saves.append({'filename': current_save_name, 'metadata': None})

        # Ordenar la lista de diccionarios por el 'filename'
        self.save_menu_saves.sort(key=lambda x: x.get('filename', ''))
        
        # Pre-seleccionar la partida actual en el menú de "Guardar como..."
        if self.save_path:
            self.save_menu_selected = os.path.basename(self.save_path)
        else:
            self.save_menu_selected = None

    def _action_toggle_pause(self): self.paused = not self.paused
    def _action_advance_day(self):
        if self.ecosistema.dia_total < self.dias_simulacion and self.ecosistema.animales:
            return self._avanzar_dia()
        return True
    
    def _action_feed_all_herbivores(self):
        """Da la orden de comer a todos los herbívoros y omnívoros con baja energía."""
        print("Dando orden de comer a herbívoros y omnívoros hambrientos...")
        for animal in self.ecosistema.animales:
            if not isinstance(animal, Carnivoro) and (animal.energia / animal.max_energia) < 0.8:
                animal.buscar_comida(forzado=True)

    def _action_toggle_hunt_mode(self):
        """Activa o desactiva el modo de caza para carnívoros."""
        self.ecosistema.activar_modo_caza_carnivoro()
        # Actualizar texto del botón
        if self.ecosistema.modo_caza_carnivoro_activo:
            # Cambiar la música de fondo a la de caza
            pygame.mixer.music.load("assets/atacar_1.mp3")
            pygame.mixer.music.set_volume(0.25) # Volumen de caza
            pygame.mixer.music.play(-1)
            self.view.buttons["hunt"].text = "Regresar Carnívoros"
        else:
            # Restaurar la música de fondo normal de la simulación
            self.view.start_simulation_music()
            self.view.buttons["hunt"].text = "Cazar Herbívoros"

    def _play_special_sound_and_fade_music(self, sound, loops=0):
        """Atenúa la música y reproduce un sonido especial. La restauración del volumen se maneja en el bucle principal."""
        # Si ya hay un sonido especial sonando, no hacemos nada para evitar conflictos.
        if self.special_sound_channel and self.special_sound_channel.get_busy(): # Usamos el canal para sonidos puntuales
            return
        
        # Guardamos el volumen original de la música antes de atenuarla.
        self.music_volume_before_fade = pygame.mixer.music.get_volume()
        pygame.mixer.music.set_volume(self.music_volume_before_fade * 0.3)
        
        # Reproducimos el sonido y guardamos el canal para monitorearlo.
        self.special_sound_channel = sound.play(loops=0) # Forzar a que no haya bucle para sonidos puntuales



    def _action_force_reproduce(self):
        if self.animal_seleccionado and self.pareja_seleccionada:
            # Asegurarse de que son de la misma especie antes de intentar la reproducción
            if type(self.animal_seleccionado) == type(self.pareja_seleccionada):
                # Reproducimos el sonido una sola vez, sin bucle. La restauración se gestiona en el bucle principal.
                self._play_special_sound_and_fade_music(self.reproduction_sound) # loops=0 es el valor por defecto
                self.animal_seleccionado.buscar_pareja_para_reproducir(self.pareja_seleccionada)
                # La restauración del volumen de la música se gestiona automáticamente en el bucle principal.
            else:
                self._display_message(f"{self.animal_seleccionado.nombre} y {self.pareja_seleccionada.nombre} no son de la misma especie.", is_error=True)

    def _action_select_animal_at(self, pos):
        """Selecciona un animal en la posición dada o deselecciona si se hace clic en un espacio vacío."""
        animal_clicado = self.ecosistema.get_animal_at(pos)
        
        if not animal_clicado:
            # Si se hace clic en espacio vacío, se deselecciona todo.
            self.animal_seleccionado = None
            self.pareja_seleccionada = None
            # Si se deselecciona todo, detener el sonido de reproducción si está sonando.
            if self.special_sound_channel and self.special_sound_channel.get_sound() == self.reproduction_sound:
                self.special_sound_channel.stop()

        elif not self.animal_seleccionado or self.animal_seleccionado == animal_clicado:
            # Seleccionar el animal principal (o deseleccionar la pareja si se vuelve a clicar)
            # Si se vuelve a hacer clic en el animal ya seleccionado, se deselecciona la pareja.
            self.animal_seleccionado = animal_clicado
            self.pareja_seleccionada = None
            # Si se deselecciona la pareja, detener el sonido de reproducción si está sonando.
            if self.special_sound_channel and self.special_sound_channel.get_sound() == self.reproduction_sound:
                self.special_sound_channel.stop()

        else:
            # Si ya hay un animal seleccionado y se clica en otro diferente, se selecciona como pareja.
            self.pareja_seleccionada = animal_clicado

    def run(self):
        running = True
        sim_over = False
        self._setup_button_actions()

        while running:
            self.clock.tick(60)  # Mantener 60 FPS constantes
            
            if self.current_state == "MENU":
                # Al volver al menú, siempre recargamos los usuarios y las partidas del usuario seleccionado.
                # Esto asegura que los cambios (nuevas partidas, renombrados) se reflejen.
                self.menu.users = persistencia.obtener_lista_usuarios()
                if self.menu.selected_user:
                    # Sincronizar el estado del autoguardado del controlador con el menú
                    self.menu.selected_autosave_interval = self.autosave_interval
                    self.menu.saves = persistencia.obtener_partidas_usuario(self.menu.selected_user)

                self.menu.draw()
                running = self.handle_menu_events()
            
            elif self.current_state == "SIMULATION":
                current_time = pygame.time.get_ticks()
                # Si se vuelve a la simulación desde el menú de guardado, reanudar si no estaba pausada antes.
                # Esto evita que el juego se quede pausado al usar "Guardar como".
                if self.view.needs_static_redraw: # Un indicador de que volvemos de otro estado
                    if not hasattr(self, '_was_paused_before_saving') or not self._was_paused_before_saving:
                        self.paused = False

                delta_time = current_time - self.last_update_time

                # Comprobar si el icono de autoguardado debe desaparecer
                if self.is_autosaving and self.autosave_icon_end_time and current_time >= self.autosave_icon_end_time:
                    self.is_autosaving = False
                    self.autosave_icon_end_time = None
                
                # --- Lógica de restauración de volumen de música ---
                if self.special_sound_channel and not self.special_sound_channel.get_busy():
                    # Si el sonido especial ha terminado, restauramos el volumen de la música.
                    if pygame.mixer.music.get_busy():
                        pygame.mixer.music.set_volume(self.music_volume_before_fade)
                    self.special_sound_channel = None # Limpiamos la referencia al canal.

                if not self.paused and not sim_over and delta_time > self.base_time_per_hour / self.sim_speed_multiplier:
                    sim_over = self._avanzar_hora()
                    self.last_update_time = current_time
                running, sim_over = self.handle_simulation_events(running, sim_over) # type: ignore

                # --- Lógica de Autoguardado ---
                if self.trigger_autosave:
                    self.trigger_autosave = False # Reseteamos el trigger
                    self.is_autosaving = True
                    self.autosave_icon_end_time = pygame.time.get_ticks() + 3000 # 3 segundos
                    
                    print(f"Autoguardando partida... (Intervalo: {self.autosave_interval} días)")
                    # Iniciar el guardado en un hilo separado para no pausar la simulación.
                    save_thread = threading.Thread(target=self._save_in_background, args=(self.save_path, self.sim_speed_multiplier, self.autosave_interval))
                    save_thread.start()

                self.view.draw_simulation(self.ecosistema, sim_over, self.animal_seleccionado, self.pareja_seleccionada, self.sim_speed_multiplier, self.is_autosaving)
            
            elif self.current_state == "SAVING":
                self.view.draw_save_menu(self.save_menu_saves, self.save_menu_input, self.save_menu_selected) # Pasamos el save seleccionado
                running = self.handle_saving_events()

            elif self.current_state == "CONFIRM_LOAD":
                if self.pending_load_info:
                    self.view.draw_load_confirmation(self.pending_load_info)
                running = self.handle_load_confirmation_events()
    
        self.view.close()

    def handle_menu_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                return False
            
            command = self.menu.handle_event(event)
            if command:
                command_type = command.get("type")

                if command_type == "create_user":
                    username = command["username"]
                    persistencia.crear_usuario(username)
                    self.menu.users = persistencia.obtener_lista_usuarios()
                    self.menu.selected_user = username
                    self.menu.saves = persistencia.obtener_partidas_usuario(username)
                
                elif command_type == "rename_user":
                    success = persistencia.renombrar_usuario(command["old_name"], command["new_name"])
                    if success:
                        self.menu.users = persistencia.obtener_lista_usuarios()
                        self.menu.selected_user = command["new_name"]
                        # Las partidas se recargarán en el siguiente ciclo del menú

                elif command_type == "delete_user":
                    success = persistencia.eliminar_usuario(command["username"])
                    if success:
                        self.menu.users = persistencia.obtener_lista_usuarios()
                        self.menu.selected_user = None
                        self.menu.selected_save = None
                        self.menu.saves = []


                elif command_type == "rename_save":
                    success = persistencia.renombrar_partida(
                        command["user"],
                        command["old_name"],
                        command["new_name"]
                    )
                    if success:
                        self.menu.selected_save = {"filename": command["new_name"], "metadata": None} # Actualizar la selección
                        self.menu.saves = persistencia.obtener_partidas_usuario(command["user"])

                elif command_type == "delete_save":
                    save_filename = command["save"]["filename"] # Extraer el nombre de archivo del diccionario
                    success = persistencia.eliminar_partida(command["user"], save_filename)
                    if success:
                        # Actualizar la vista del menú para reflejar la eliminación
                        self.menu.selected_save = None
                        self.menu.saves = persistencia.obtener_partidas_usuario(command["user"])

                elif command_type == "select_user":
                    username = command["username"]
                    self.menu.saves = persistencia.obtener_partidas_usuario(username)

                elif command_type == "create_save":
                    # Este comando solo crea la referencia en el menú, no inicia el juego
                    new_save_info = {"filename": command["save"], "metadata": None}
                    if not any(s['filename'] == new_save_info['filename'] for s in self.menu.saves):
                        self.menu.saves.append(new_save_info)
                        self.menu.selected_save = command["save"]

                elif command_type == "select_save":
                    user = command["user"]
                    save_file = command["save"]["filename"] # Extraer el nombre de archivo del diccionario
                    save_path = os.path.join("saves", user, save_file)
                    date = persistencia.obtener_fecha_guardado(save_path)
                    population = persistencia.obtener_info_poblacion(save_path)
                    cycle = persistencia.obtener_ciclo_guardado(save_path)
                    self.menu.selected_save_date = date
                    self.menu.selected_save_population = population
                    self.menu.selected_save_cycle = cycle

                elif command_type == "cycle_autosave":
                    # This command is new, it will be handled by the menu to cycle through options
                    # and the result will be sent with "start_game" or "set_autosave"
                    pass # The logic is handled within Menu_view.py, controller just needs to acknowledge.

                elif command_type == "set_autosave":
                    self.autosave_interval = command["interval"]
                    print(f"Intervalo de autoguardado establecido en: {self.autosave_interval} días.")

                elif command_type == "start_game":
                    user = command["user"]
                    save_data = command["save"]
                    # El comando puede devolver un string (para partidas nuevas) o un dict (para partidas existentes)
                    if isinstance(save_data, dict):
                        save_file = save_data.get("filename")
                        is_new_game = False
                    else:
                        save_file = save_data # Ya es un string
                        is_new_game = True

                    self.current_user = user # Guardamos el usuario actual
                    self.save_path = os.path.join("saves", user, save_file) # type: ignore
                    self.autosave_interval = command.get("autosave") # Obtener el intervalo del menú
                    
                    if is_new_game or not os.path.exists(self.save_path):
                        # Si es una partida nueva, no hay nada que cargar, poblamos y empezamos.
                        print("Archivo de guardado no encontrado. Creando un nuevo mundo y poblándolo.")
                        self._poblar_ecosistema()
                        pygame.mixer.music.stop() # Detenemos la música del menú
                        self.view.start_simulation_music() # Iniciamos la música de la simulación
                        self.current_state = "SIMULATION"
                        self.paused = False # Empezar la simulación activa
                    else:
                        # Si es una partida existente, preparamos la confirmación.
                        self.pending_load_info = {
                            "path": self.save_path,
                            "date": persistencia.obtener_fecha_guardado(self.save_path),
                            "population": persistencia.obtener_info_poblacion(self.save_path),
                            "cycle": persistencia.obtener_ciclo_guardado(self.save_path)
                        }
                        self.current_state = "CONFIRM_LOAD"

        return True
    
    def handle_simulation_events(self, running, sim_over):
        for event in pygame.event.get():
            # La vista procesa el evento y devuelve un comando de alto nivel
            command = self.view.handle_event(event, self.ecosistema, self.animal_seleccionado)

            if not command:
                continue

            command_type = command.get("type")

            if command_type == "quit":
                # Si el usuario cierra la ventana durante la simulación
                if event.type == pygame.QUIT:
                    running = False # Termina el bucle principal
                    break
                self._play_menu_music() # Poner la música del menú al salir de la simulación
                self.current_state = "MENU" # Volver al menú
            elif command_type == "toggle_music":
                self.view.toggle_music()
            elif command_type == "click_simulation_area" and not sim_over:
                self._action_select_animal_at(command["pos"])
            elif command_type and command_type.startswith("click_button_") and not sim_over:
                button_name = command_type.replace("click_button_", "")
                action = self.button_actions.get(button_name)
                if action:
                    print(f"DEBUG: Controller executing action for button '{button_name}'")
                    result = action()
                    # Si la acción fue avanzar el día, actualizamos el estado de sim_over
                    if button_name == "next_day" and result:
                        sim_over = True

        return running, sim_over

    def handle_saving_events(self):
        """Maneja los eventos en el menú 'Guardar como...'."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._was_paused_before_saving = self.paused
                    self.current_state = "SIMULATION" # Cancelar y volver a la simulación
                    return True
                elif event.key == pygame.K_RETURN:
                    # Determinar el nombre del archivo a guardar
                    if self.save_menu_input: # Prioridad al texto introducido
                        save_name = self.save_menu_input.strip().replace(" ", "_") + ".json"
                    elif self.save_menu_selected: # Si no hay texto, usar la selección
                        save_name = self.save_menu_selected
                    else: # No hay nada que guardar
                        return True

                    # Guardar la partida
                    new_save_path = os.path.join("saves", self.current_user, save_name)
                    persistencia.guardar_partida(self.ecosistema, new_save_path, sim_speed_multiplier=self.sim_speed_multiplier, autosave_interval=self.autosave_interval)
                    self.save_path = new_save_path # Actualizar la ruta de guardado actual
                    
                    # Volver a la simulación
                    self._was_paused_before_saving = self.paused
                    self.current_state = "SIMULATION"
                    return True
                elif event.key == pygame.K_BACKSPACE:
                    self.save_menu_input = self.save_menu_input[:-1]
                else:
                    self.save_menu_input += event.unicode
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Lógica para seleccionar una partida de la lista
                save_slot_rects = self.view.get_save_slot_rects(self.save_menu_saves)
                for i, rect in enumerate(save_slot_rects):
                    if rect.collidepoint(event.pos):
                        self.save_menu_selected = self.save_menu_saves[i].get("filename")
                        self.save_menu_input = "" # Limpiar el input al seleccionar
        return True

    def handle_load_confirmation_events(self):
        """Maneja los eventos en la pantalla de confirmación de carga."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # Cancelar la carga y volver al menú principal
                    self.current_state = "MENU"
                    self.pending_load_info = None
                    return True
                elif event.key == pygame.K_RETURN:
                    # Confirmar la carga
                    if self.pending_load_info:
                        self.save_path = self.pending_load_info["path"]
                        load_successful = self._action_load()
                        if not load_successful:
                            # Si por alguna razón falla, volvemos al menú
                            # _action_load ya muestra el mensaje de error.
                            self.current_state = "MENU"
                            self.paused = True # Asegurarse de que el menú esté pausado
                            self._play_menu_music() # Volver a poner la música del menú si la carga falla
                        else:
                            pygame.mixer.music.stop() # Detenemos la música del menú
                            self.view.start_simulation_music() # Iniciamos la música de la simulación
                            self.current_state = "SIMULATION"
                            self.paused = False # Iniciar la simulación activa
                        self.pending_load_info = None
                    return True
        return True

def main():
    # Limpiar archivos temporales de sesiones anteriores antes de empezar
    persistencia.limpiar_archivos_temporales_antiguos()
    controlador = SimulationController(dias_simulacion=200)
    controlador.run()
    

if __name__ == "__main__":
    main()