import pygame
import os
from src.Logica.Logica import Ecosistema, Herbivoro, Carnivoro, Omnivoro, Conejo, Raton, Cabra, Leopardo, Gato, Cerdo, Mono, Halcon, Insecto
from src.Interfaz.Interfaz import PygameView
from src.Interfaz.Menu_view import Menu
import src.Persistencia.Persistencia as persistencia # Importamos el nuevo módulo

class SimulationController:
    def __init__(self, dias_simulacion: int):
        pygame.init()  # Asegurar que pygame está inicializado
        self.view = PygameView()
        self.ecosistema = Ecosistema()
        self.dias_simulacion = dias_simulacion
        
        # El controlador ahora es responsable de obtener los datos para el menú
        users = persistencia.obtener_lista_usuarios()
        self.menu = Menu(self.view.screen, self.view.font_header, self.view.font_normal, self.view.font_small, users)
        
        self.current_state = "MENU" # Estados: "MENU", "SIMULATION", "SAVING"
        self.save_path = None
        self.current_user = None
        
        self.autosave_interval = None # Días entre autoguardados. None para desactivado.
        self.days_since_last_autosave = 0

        self.animal_seleccionado = None
        self.pareja_seleccionada = None
        self.paused = True
        
        self.sim_speed_multiplier = 3
        self.base_time_per_hour = 50 # Ralentizamos un poco para mejor visualización
        self.last_update_time = pygame.time.get_ticks()
        self.clock = pygame.time.Clock()

    def _poblar_ecosistema(self):
        tipos_de_animales = [Conejo, Raton, Cabra, Leopardo, Gato, Cerdo, Mono, Halcon, Insecto]
        for tipo in tipos_de_animales:
            for _ in range(2):
                self.ecosistema.agregar_animal(tipo)

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

    def _avanzar_hora(self):
        self.ecosistema.simular_hora()
        if self.ecosistema.dia_total >= self.dias_simulacion or not self.ecosistema.animales:
            return True
        if self.ecosistema.hora_actual == 0:
            self._actualizar_grafico()
            if self.autosave_interval is not None and self.autosave_interval > 0:
                self.days_since_last_autosave += 1
                if self.days_since_last_autosave >= self.autosave_interval:
                    print(f"Autoguardando partida... (Intervalo: {self.autosave_interval} días)")
                    self._action_save(autosave=True)
                    self.days_since_last_autosave = 0
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
            self.button_actions[f"add_{name}"] = lambda species=cls: self.ecosistema.agregar_animal(species)
        
    def _action_save(self, autosave=False):
        """Utiliza la clase Persistencia para guardar el estado del ecosistema."""
        if self.save_path:
            persistencia.guardar_partida(self.ecosistema, self.save_path, autosave=autosave)
        else:
            print("Error: No hay una ruta de guardado definida.")

    def _action_load(self):
        """Utiliza la clase Persistencia para cargar el estado del ecosistema.
        Devuelve True si la carga fue exitosa, False en caso contrario."""
        if self.save_path:
            loaded_ecosystem = persistencia.cargar_partida(self.save_path)
            if loaded_ecosystem:
                self.ecosistema = loaded_ecosystem
                self.view.graph.history.clear()
                # Restaurar configuraciones de la simulación desde el ecosistema cargado
                self.ecosistema.activar_modo_caza_carnivoro(forzar_estado=self.ecosistema.modo_caza_carnivoro_activo)
                # Actualizar el texto del botón de caza en la vista
                if self.ecosistema.modo_caza_carnivoro_activo:
                    self.view.buttons["hunt"].text = "Regresar Carnívoros"
                else:
                    self.view.buttons["hunt"].text = "Cazar Herbívoros"
                self._setup_button_actions() # Volver a configurar las acciones con el nuevo ecosistema
                self.view.needs_static_redraw = True
                return True # Carga exitosa
            else:
                self.ecosistema = Ecosistema()
                self._setup_button_actions() # También reconfigurar si la carga falla
                return False # Carga fallida o archivo no existe

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
            self.view.buttons["hunt"].text = "Regresar Carnívoros"
        else:
            self.view.buttons["hunt"].text = "Cazar Herbívoros"

    def _action_force_reproduce(self):
        if self.animal_seleccionado and self.pareja_seleccionada:
            # Asegurarse de que son de la misma especie antes de intentar la reproducción
            if type(self.animal_seleccionado) == type(self.pareja_seleccionada):
                self.animal_seleccionado.buscar_pareja_para_reproducir(self.pareja_seleccionada)
            else:
                print(f"Error: {self.animal_seleccionado.nombre} y {self.pareja_seleccionada.nombre} no son de la misma especie y no pueden reproducirse.")

    def _action_select_animal_at(self, pos):
        """Selecciona un animal en la posición dada o deselecciona si se hace clic en un espacio vacío."""
        animal_clicado = self.ecosistema.get_animal_at(pos)
        
        if not animal_clicado:
            # Si se hace clic en espacio vacío, se deselecciona todo.
            self.animal_seleccionado = None
            self.pareja_seleccionada = None
        elif not self.animal_seleccionado or self.animal_seleccionado == animal_clicado:
            # Seleccionar el animal principal (o deseleccionar la pareja si se vuelve a clicar)
            # Si se vuelve a hacer clic en el animal ya seleccionado, se deselecciona la pareja.
            self.animal_seleccionado = animal_clicado
            self.pareja_seleccionada = None
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
                    self.menu.saves = persistencia.obtener_partidas_usuario(self.menu.selected_user)

                self.menu.draw()
                running = self.handle_menu_events()
            
            elif self.current_state == "SIMULATION":
                current_time = pygame.time.get_ticks()
                delta_time = current_time - self.last_update_time

                if not self.paused and not sim_over and delta_time > self.base_time_per_hour / self.sim_speed_multiplier:
                    sim_over = self._avanzar_hora()
                    self.last_update_time = current_time
                    
                running, sim_over = self.handle_simulation_events(running, sim_over)

                self.view.draw_simulation(self.ecosistema, sim_over, self.animal_seleccionado, self.pareja_seleccionada, self.sim_speed_multiplier)
            
            elif self.current_state == "SAVING":
                self.view.draw_save_menu(self.save_menu_saves, self.save_menu_input, self.save_menu_selected) # Pasamos el save seleccionado
                running = self.handle_saving_events()
    
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

                elif command_type == "set_autosave":
                    self.autosave_interval = command["interval"]
                    print(f"Intervalo de autoguardado establecido en: {self.autosave_interval} días.")

                elif command_type == "start_game":
                    user = command["user"]
                    save_data = command["save"]
                    # El comando puede devolver un string (para partidas nuevas) o un dict (para partidas existentes)
                    if isinstance(save_data, dict):
                        save_file = save_data.get("filename")
                    else:
                        save_file = save_data # Ya es un string
                    self.current_user = user # Guardamos el usuario actual
                    self.save_path = os.path.join("saves", user, save_file) # type: ignore
                    self.autosave_interval = command.get("autosave") # Obtener el intervalo de autoguardado                    
                    
                    load_successful = self._action_load()
                    
                    # Solo poblar si la carga falló (es decir, es una partida nueva)
                    if not load_successful:
                        print("Archivo de guardado no encontrado. Creando un nuevo mundo y poblándolo.")
                        self._poblar_ecosistema()

                    self.current_state = "SIMULATION"
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
                self._action_save() # Guardar al salir
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
                    persistencia.guardar_partida(self.ecosistema, new_save_path)
                    self.save_path = new_save_path # Actualizar la ruta de guardado actual
                    
                    # Volver a la simulación
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

def main():
    # Limpiar archivos temporales de sesiones anteriores antes de empezar
    persistencia.limpiar_archivos_temporales_antiguos()
    controlador = SimulationController(dias_simulacion=200)
    controlador.run()
    

if __name__ == "__main__":
    main()