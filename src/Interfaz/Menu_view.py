import pygame
from .Constantes import SIM_WIDTH, SCREEN_HEIGHT, SCREEN_WIDTH, COLOR_BACKGROUND, COLOR_TEXT, COLOR_BUTTON, COLOR_SELECTED, UI_WIDTH

class Menu:
    def __init__(self, screen, font_header, font_normal, font_small, users, saves_for_selected_user=None):
        self.screen = screen
        self.font_header = font_header
        self.font_normal = font_normal
        self.font_small = font_small
        self.users = users
        self.saves = saves_for_selected_user or []
        self.selected_user = None
        self.selected_save = None
        self.selected_save_population = None
        self.selected_save_cycle = None
        self.selected_save_date = None
        self.input_text = ""
        self.input_active = False # Para la creación de usuarios # Este parece ser un remanente, lo mantenemos por si acaso pero no se usa en la lógica nueva.
        self.input_user_active = False
        self.input_save_active = False
        self.autosave_options = [None, 10, 30, 50]  # None significa Desactivado
        self.rename_active = False
        self.rename_user_active = False
        self.current_autosave_index = 0
        self.scroll_x = 0
        self.background_image = None
        try:
            # Cargar la imagen de fondo del menú
            original_image = pygame.image.load("assets/fondo_menu.png").convert()
            # Escalar la imagen para que su altura coincida con la de la pantalla
            original_width, original_height = original_image.get_size()
            aspect_ratio = original_width / original_height
            scaled_height = SCREEN_HEIGHT
            scaled_width = int(scaled_height * aspect_ratio)
            scaled_image = pygame.transform.scale(original_image, (scaled_width, scaled_height))

            # Crear una superficie el doble de ancha para el bucle de desplazamiento
            self.background_image = pygame.Surface((scaled_width * 2, scaled_height))
            self.background_image.blit(scaled_image, (0, 0))
            self.background_image.blit(scaled_image, (scaled_width, 0))
        except (pygame.error, FileNotFoundError):
            print("Advertencia: No se pudo cargar la imagen de fondo del menú 'fondo_menu.png'. Se usará un color sólido.")
            self.background_image = None

        self.panel_background_image = None
        try:
            # Cargar la imagen de fondo para el panel derecho
            panel_image_original = pygame.image.load("assets/fondo_menu_1.png").convert()
            # Escalar la imagen para que coincida con el tamaño del panel
            self.panel_background_image = pygame.transform.scale(panel_image_original, (UI_WIDTH, SCREEN_HEIGHT))
        except (pygame.error, FileNotFoundError):
            print("Advertencia: No se pudo cargar la imagen 'fondo_menu_1.png' para el panel. Se usará un color sólido.")
            self.panel_background_image = None

        # Los botones se crearán dinámicamente en el método draw,
        # pero mantenemos el diccionario para acceder a sus rectángulos.
        self.buttons = {
            "new_user": None, "rename_user": None, "delete_user": None,
            "new_save": None, "rename_save": None, "delete_save": None,
            "start_game": None, "autosave": None
        }
        # Rectángulos para elementos de lista (que no son botones fijos)
        self.list_rects = {
            "users": [], "saves": []
        }
        self.selected_autosave_interval = self.autosave_options[self.current_autosave_index]

    def handle_event(self, event):
        """Maneja los eventos de Pygame para el menú."""
        # Primero, manejar eventos de teclado si un campo de texto está activo
        is_input_active = self.input_user_active or self.input_save_active or self.rename_user_active or self.rename_active
        if event.type == pygame.KEYDOWN and is_input_active:
            return self.handle_text_input(event)

        # Luego, manejar clics del ratón
        if event.type == pygame.MOUSEBUTTONDOWN:
            return self.handle_mouse_click(event)

        return None

    def handle_mouse_click(self, event):
        """Procesa los clics del ratón en botones y listas."""
        if self.buttons["start_game"] and self.buttons["start_game"].collidepoint(event.pos) and self.selected_user and self.selected_save:
            return {
                "type": "start_game",
                "user": self.selected_user,
                "save": self.selected_save,
                "autosave": self.selected_autosave_interval,
            }

        # Comprobar clics en botones
        for name, rect in self.buttons.items():
            if rect and rect.collidepoint(event.pos):
                if name == "new_user":
                    self.input_user_active = True; self.rename_user_active = False; self.rename_active = False; self.input_save_active = False
                    self.input_text = ""
                    return None
                elif name == "new_save" and self.selected_user:
                    self.input_save_active = True; self.input_user_active = False; self.rename_user_active = False; self.rename_active = False
                    self.input_text = ""
                    return None
                elif name == "rename_user" and self.selected_user:
                    self.rename_user_active = True; self.input_user_active = False; self.rename_active = False; self.input_save_active = False
                    self.input_text = self.selected_user
                    return None
                elif name == "delete_user" and self.selected_user:
                    return {"type": "delete_user", "username": self.selected_user}
                elif name == "rename_save" and self.selected_save:
                    self.rename_active = True; self.input_save_active = False; self.input_user_active = False; self.rename_user_active = False
                    self.input_text = self.selected_save["filename"].replace(".json", "").replace("_", " ")
                    return None
                elif name == "delete_save" and self.selected_user and self.selected_save:
                    return {"type": "delete_save", "user": self.selected_user, "save": self.selected_save}
                elif name == "start_game" and self.selected_user and self.selected_save:
                    return {"type": "start_game", "user": self.selected_user, "save": self.selected_save, "autosave": self.selected_autosave_interval}
                elif name == "autosave":
                        self.current_autosave_index = (self.current_autosave_index + 1) % len(self.autosave_options)
                        self.selected_autosave_interval = self.autosave_options[self.current_autosave_index]
                        # Devolvemos un comando para que el controlador pueda estar al tanto si es necesario
                        return {"type": "set_autosave", "interval": self.selected_autosave_interval}



        # Comprobar clics en elementos de lista (usuarios y partidas)
        for i, (user, rect) in enumerate(self.list_rects["users"]):
            if rect.collidepoint(event.pos):
                self.selected_user = user
                self.selected_save = None; self.selected_save_population = None; self.selected_save_cycle = None; self.selected_save_date = None
                self.rename_user_active = False; self.rename_active = False; self.input_save_active = False; self.input_user_active = False
                return {"type": "select_user", "username": user}

        if self.selected_user:
            for i, (save, rect) in enumerate(self.list_rects["saves"]):
                if rect.collidepoint(event.pos):
                    self.selected_save = save
                    self.rename_active = False
                    return {"type": "select_save", "user": self.selected_user, "save": save}
        return None

    def handle_text_input(self, event):
        """Procesa la entrada de teclado para los campos de texto activos."""
        if event.key == pygame.K_RETURN:
            if self.input_user_active and self.input_text:
                username = self.input_text
                self.input_user_active = False
                self.input_text = ""
                return {"type": "create_user", "username": username}
            elif self.input_save_active and self.input_text and self.selected_user:
                save_name = {"filename": self.input_text.strip().replace(" ", "_") + ".json", "metadata": None}
                self.selected_save = save_name
                self.input_save_active = False
                self.input_text = ""
                return {"type": "start_game", "user": self.selected_user, "save": self.selected_save, "autosave": self.selected_autosave_interval}
            elif self.rename_user_active and self.input_text and self.selected_user:
                new_name = self.input_text.strip().replace(" ", "_")
                command = {
                    "type": "rename_user",
                    "old_name": self.selected_user,
                    "new_name": new_name
                }
                self.rename_user_active = False
                self.input_text = ""
                return command
            elif self.rename_active and self.input_text and self.selected_user and self.selected_save:
                new_name = self.input_text.strip().replace(" ", "_") + ".json"
                command = {
                    "type": "rename_save",
                    "user": self.selected_user,
                    "old_name": self.selected_save["filename"],
                    "new_name": new_name
                }
                self.rename_active = False
                self.input_text = ""
                return command

        elif event.key == pygame.K_BACKSPACE:
            self.input_text = self.input_text[:-1]
        elif event.unicode:
            self.input_text += event.unicode
        return None

    def draw(self):
        """Dibuja el menú completo en la pantalla."""
        if self.background_image:
            # Ancho de una sola imagen (la mitad de la superficie total)
            bg_width = self.background_image.get_width() // 2
            
            # Dibujar la superficie de fondo dos veces para el bucle
            self.screen.blit(self.background_image, (self.scroll_x, 0))
            
            # Mover el fondo
            self.scroll_x -= 0.2  # Velocidad de desplazamiento (ajusta este valor)
            
            # Si la imagen se ha desplazado completamente, reiniciar el scroll
            if self.scroll_x <= -bg_width:
                self.scroll_x = 0
        else:
            self.screen.fill(COLOR_BACKGROUND)
        
        # Título
        title_surf = self.font_header.render("Simulador de Ecosistema", True, COLOR_TEXT)
        self.screen.blit(title_surf, (SIM_WIDTH // 2 - title_surf.get_width() // 2, 200))
        
        # Panel derecho
        panel_rect = pygame.Rect(SIM_WIDTH, 0, UI_WIDTH, SCREEN_HEIGHT)
        if self.panel_background_image:
            self.screen.blit(self.panel_background_image, (SIM_WIDTH, 0))
        else:
            pygame.draw.rect(self.screen, (40, 40, 40), panel_rect)
        
        # --- Posicionamiento dinámico ---
        x_margin = SIM_WIDTH + 20
        list_x_offset = x_margin + 20
        current_y = 20
        
        # Sección de Usuarios
        self.screen.blit(self.font_header.render("Perfiles de Usuario", True, COLOR_TEXT), (x_margin, current_y))
        current_y += 40
        
        self.list_rects["users"] = [] # Limpiar rectángulos de la iteración anterior
        # Lista de usuarios
        for i, user in enumerate(self.users or []):
            color = COLOR_SELECTED if user == self.selected_user else COLOR_TEXT
            user_surf = self.font_normal.render(user, True, color)
            user_rect = self.screen.blit(user_surf, (list_x_offset, current_y))
            self.list_rects["users"].append((user, user_rect))
            current_y += 25
        current_y += 15
        
        # Botón/Input para nuevo usuario
        self.buttons["new_user"] = pygame.Rect(x_margin, current_y, UI_WIDTH - 40, 35)
        pygame.draw.rect(self.screen, COLOR_BUTTON, self.buttons["new_user"])
        if self.input_user_active or self.rename_user_active:
            input_surf = self.font_normal.render(self.input_text + "|", True, COLOR_TEXT)
        else:
            input_surf = self.font_normal.render("Crear Nuevo Usuario", True, COLOR_TEXT)
        self.screen.blit(input_surf, (self.buttons["new_user"].x + 10, self.buttons["new_user"].y + 5))
        current_y += 45
        
        # Botones de gestión de usuario (solo si hay un usuario seleccionado)
        if self.selected_user:
            btn_width = (UI_WIDTH - 40 - 10) // 2
            self.buttons["rename_user"] = pygame.Rect(x_margin, current_y, btn_width, 30)
            self.buttons["delete_user"] = pygame.Rect(x_margin + btn_width + 10, current_y, btn_width, 30)

            pygame.draw.rect(self.screen, COLOR_BUTTON, self.buttons["rename_user"])
            if self.rename_user_active:
                rename_text_surf = self.font_small.render("OK (Enter)", True, COLOR_TEXT)
            else:
                rename_text_surf = self.font_small.render("Renombrar Usuario", True, COLOR_TEXT)
            self.screen.blit(rename_text_surf, (self.buttons["rename_user"].centerx - rename_text_surf.get_width() // 2, self.buttons["rename_user"].centery - rename_text_surf.get_height() // 2))

            pygame.draw.rect(self.screen, (200, 50, 50), self.buttons["delete_user"])
            delete_text_surf = self.font_small.render("Eliminar Usuario", True, COLOR_TEXT)
            self.screen.blit(delete_text_surf, (self.buttons["delete_user"].centerx - delete_text_surf.get_width() // 2, self.buttons["delete_user"].centery - delete_text_surf.get_height() // 2))
            current_y += 40

        pygame.draw.line(self.screen, (80, 80, 80), (x_margin, current_y), (SIM_WIDTH + UI_WIDTH - 20, current_y), 2)
        current_y += 20
        
        # Sección de Partidas
        if self.selected_user:
            self.screen.blit(self.font_header.render(f"Partidas de {self.selected_user}", True, COLOR_TEXT), (x_margin, current_y))
            current_y += 40

            self.list_rects["saves"] = [] # Limpiar rectángulos de la iteración anterior
            for i, save in enumerate(self.saves or []):
                is_selected = False
                if self.selected_save and isinstance(self.selected_save, dict):
                    is_selected = (save["filename"] == self.selected_save.get("filename"))

                color = COLOR_SELECTED if is_selected else COLOR_TEXT
                save_name = save["filename"].replace(".json", "").replace("_", " ").capitalize()
                save_surf = self.font_normal.render(save_name, True, color)
                save_rect = self.screen.blit(save_surf, (list_x_offset, current_y + 5))
                self.list_rects["saves"].append((save, save_rect))
                current_y += 30 # Aumentamos el espaciado vertical
            current_y += 15
            
            # Mostrar información de la partida seleccionada
            if self.selected_save:
                if self.selected_save_population:
                    animales, plantas = self.selected_save_population
                    pop_str = f"Población: {animales} Animales, {plantas} Plantas"
                    pop_surf = self.font_small.render(pop_str, True, COLOR_TEXT)
                    self.screen.blit(pop_surf, (list_x_offset, current_y))
                    current_y += 15

                if self.selected_save_cycle:
                    dia, hora = self.selected_save_cycle
                    cycle_str = f"Ciclo: Día {dia} - {hora:02d}:00"
                    cycle_surf = self.font_small.render(cycle_str, True, COLOR_TEXT)
                    self.screen.blit(cycle_surf, (list_x_offset, current_y))
                    current_y += 15

                try:
                    if self.selected_save_date:
                        from datetime import datetime
                        date_obj = datetime.fromisoformat(self.selected_save_date)
                        date_str = date_obj.strftime("%d/%m/%Y - %H:%M:%S")
                        date_surf = self.font_small.render(f"Guardado: {date_str}", True, COLOR_TEXT)
                        self.screen.blit(date_surf, (list_x_offset, current_y))
                        current_y += 15
                except (ValueError, ImportError):
                    pass
                current_y += 20

            self.buttons["new_save"] = pygame.Rect(x_margin, current_y, UI_WIDTH - 40, 35)
            pygame.draw.rect(self.screen, COLOR_BUTTON, self.buttons["new_save"])
            if self.input_save_active and not self.rename_active:
                new_save_surf = self.font_normal.render(self.input_text + "|", True, COLOR_TEXT)
            else:
                new_save_surf = self.font_normal.render("Nueva Partida", True, COLOR_TEXT)
            self.screen.blit(new_save_surf, (self.buttons["new_save"].x + 10, self.buttons["new_save"].y + 5))
            current_y += 45

            if self.selected_save:
                self.buttons["rename_save"] = pygame.Rect(x_margin, current_y, UI_WIDTH - 40, 35)
                pygame.draw.rect(self.screen, COLOR_BUTTON, self.buttons["rename_save"])
                if self.rename_active:
                    rename_surf = self.font_normal.render(self.input_text + "|", True, COLOR_TEXT)
                else:
                    rename_surf = self.font_normal.render("Renombrar Partida", True, COLOR_TEXT)
                self.screen.blit(rename_surf, (self.buttons["rename_save"].x + 10, self.buttons["rename_save"].y + 5))
                current_y += 45

                btn_width = (UI_WIDTH - 40 - 10) // 2
                self.buttons["delete_save"] = pygame.Rect(x_margin, current_y, btn_width, 40)
                self.buttons["start_game"] = pygame.Rect(x_margin + btn_width + 10, current_y, btn_width, 40)

                pygame.draw.rect(self.screen, (200, 50, 50), self.buttons["delete_save"])
                delete_surf = self.font_normal.render("Eliminar", True, COLOR_TEXT)
                self.screen.blit(delete_surf, (self.buttons["delete_save"].centerx - delete_surf.get_width() // 2, self.buttons["delete_save"].centery - delete_surf.get_height() // 2))

                pygame.draw.rect(self.screen, (0, 150, 0), self.buttons["start_game"])
                start_text = "Cargar"
                start_surf = self.font_normal.render(start_text, True, COLOR_TEXT)
                self.screen.blit(start_surf, (self.buttons["start_game"].centerx - start_surf.get_width() // 2, self.buttons["start_game"].centery - start_surf.get_height() // 2))

        # --- Sección de Autoguardado ---
        # Se muestra siempre en la parte inferior derecha del panel.
        autosave_y = SCREEN_HEIGHT - 50
        self.buttons["autosave"] = pygame.Rect(x_margin, autosave_y, UI_WIDTH - 40, 35)
        
        # Texto del botón
        interval = self.selected_autosave_interval
        if interval is None:
            autosave_text = "Autoguardado: Desactivado"
        else:
            autosave_text = f"Autoguardado: Cada {interval} días"
        
        pygame.draw.rect(self.screen, COLOR_BUTTON, self.buttons["autosave"])
        autosave_surf = self.font_small.render(autosave_text, True, COLOR_TEXT)
        self.screen.blit(autosave_surf, (self.buttons["autosave"].centerx - autosave_surf.get_width() // 2, self.buttons["autosave"].centery - autosave_surf.get_height() // 2))

        pygame.display.flip()