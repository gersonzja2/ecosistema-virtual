import pygame
from .Constantes import SIM_WIDTH, SCREEN_HEIGHT, COLOR_BACKGROUND, COLOR_TEXT, COLOR_BUTTON, COLOR_SELECTED, UI_WIDTH, UI_WIDTH

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
        self.selected_save_date = None
        self.input_text = ""
        self.input_active = False
        self.autosave_options = [None, 10, 30, 50] # None significa Desactivado
        self.current_autosave_index = 0

        self.buttons = {
            "new_user": pygame.Rect(SIM_WIDTH + 50, 200, 300, 40),
            "new_save": pygame.Rect(SIM_WIDTH + 50, 450, 300, 40),
            "autosave": pygame.Rect(SIM_WIDTH + 50, 500, 300, 40),
            "start_game": pygame.Rect(SIM_WIDTH + 50, 550, 300, 50)
        }

    def handle_event(self, event):
        """Maneja los eventos de Pygame para el menú."""
        if event.type == pygame.KEYDOWN and self.input_active:
            if event.key == pygame.K_RETURN:
                if self.input_text:
                    username = self.input_text
                    self.input_active = False
                    self.input_text = ""
                    return {"type": "create_user", "username": username}
            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            else:
                self.input_text += event.unicode
            return None # El evento de teclado ha sido manejado

        if event.type != pygame.MOUSEBUTTONDOWN:
            return None

        # Lógica para botones que están siempre visibles o se activan con estados
        if self.buttons["new_user"].collidepoint(event.pos):
            self.input_active = True
            self.input_text = ""
            return None

        if self.buttons["start_game"].collidepoint(event.pos) and self.selected_user and self.selected_save:
            return {
                "type": "start_game",
                "user": self.selected_user,
                "save": self.selected_save,
                "autosave": self.autosave_options[self.current_autosave_index],
            }

        # Lógica para elementos que aparecen después de seleccionar un usuario
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Lógica para seleccionar usuarios
            user_y_start = 100
            for i, user in enumerate(self.users or []):
                user_rect = pygame.Rect(SIM_WIDTH + 50, user_y_start + i * 30, 300, 30)
                if user_rect.collidepoint(event.pos):
                    self.selected_user = user
                    self.selected_save = None
                    self.selected_save_date = None
                    self.rename_active = False
                    self.input_save_active = False  # Resetear input de guardado
                    # Devuelve una solicitud para que el controlador cargue las partidas de este usuario
                    return {"type": "select_user", "username": user}

            # Lógica para seleccionar partidas
            save_y_start = 300
            for i, save in enumerate(self.saves or []):
                save_rect = pygame.Rect(SIM_WIDTH + 50, save_y_start + i * 30, 300, 30)
                if save_rect.collidepoint(event.pos):
                    self.selected_save = save.get("filename")
                    self.rename_active = False
                    # Solicitar al controlador que obtenga la fecha de esta partida
                    return {"type": "select_save", "user": self.selected_user, "save": self.selected_save}

            # Lógica para botones que dependen de self.selected_user
            if self.selected_user:
                if self.buttons["new_save"].collidepoint(event.pos):
                    num_saves = len(self.saves)
                    new_save_name = f"partida_{num_saves + 1}.json"
                    self.selected_save = new_save_name
                    return {"type": "create_save", "user": self.selected_user, "save": new_save_name}

                if self.buttons["autosave"].collidepoint(event.pos):
                    # Cambia el índice y devuelve un comando para que el controlador se entere.
                    self.current_autosave_index = (self.current_autosave_index + 1) % len(self.autosave_options)
                    return {"type": "set_autosave", "interval": self.autosave_options[self.current_autosave_index]}
        
        return None

    def draw(self):
        """Dibuja el menú completo en la pantalla."""
        self.screen.fill(COLOR_BACKGROUND)
        
        # Título
        title_surf = self.font_header.render("Simulador de Ecosistema", True, COLOR_TEXT)
        self.screen.blit(title_surf, (SIM_WIDTH // 2 - title_surf.get_width() // 2, 200))
        
        # Panel derecho
        pygame.draw.rect(self.screen, (40, 40, 40), (SIM_WIDTH, 0, UI_WIDTH, SCREEN_HEIGHT))
        
        # Sección de Usuarios
        self.screen.blit(self.font_header.render("Usuarios", True, COLOR_TEXT), (SIM_WIDTH + 20, 50))
        user_y_start = 100
        for i, user in enumerate(self.users or []):
            color = COLOR_SELECTED if user == self.selected_user else COLOR_TEXT
            user_surf = self.font_normal.render(user, True, color)
            self.screen.blit(user_surf, (SIM_WIDTH + 50, user_y_start + i * 30))

        # Botón/Input para nuevo usuario
        pygame.draw.rect(self.screen, COLOR_BUTTON, self.buttons["new_user"])
        if self.input_active:
            input_surf = self.font_normal.render(self.input_text + "|", True, COLOR_TEXT)
        else:
            input_surf = self.font_normal.render("Crear Nuevo Usuario", True, COLOR_TEXT)
        self.screen.blit(input_surf, (self.buttons["new_user"].x + 10, self.buttons["new_user"].y + 10))

        # Sección de Partidas
        if self.selected_user:
            self.screen.blit(self.font_header.render(f"Partidas de {self.selected_user}", True, COLOR_TEXT), (SIM_WIDTH + 20, 250))
            save_y_start = 300
            for i, save in enumerate(self.saves or []):
                color = COLOR_SELECTED if save["filename"] == self.selected_save else COLOR_TEXT
                save_name = save["filename"].replace(".json", "").replace("_", " ").capitalize()
                save_surf = self.font_normal.render(save_name, True, color)
                self.screen.blit(save_surf, (SIM_WIDTH + 50, save_y_start + i * 30))

            # Mostrar fecha de la partida seleccionada
            if self.selected_save and self.selected_save_date:
                try:
                    from datetime import datetime
                    date_obj = datetime.fromisoformat(self.selected_save_date)
                    date_str = date_obj.strftime("%d/%m/%Y - %H:%M:%S")
                    date_surf = self.font_small.render(f"Guardado: {date_str}", True, COLOR_TEXT)
                    self.screen.blit(date_surf, (SIM_WIDTH + 50, 420))
                except (ValueError, ImportError):
                    pass  # Si hay error en el formato, simplemente no se muestra.

            # Botón para nueva partida
            pygame.draw.rect(self.screen, COLOR_BUTTON, self.buttons["new_save"])
            new_save_surf = self.font_normal.render("Nueva Partida", True, COLOR_TEXT)
            self.screen.blit(new_save_surf, (self.buttons["new_save"].x + 10, self.buttons["new_save"].y + 10))

            # Botón para Autoguardado
            pygame.draw.rect(self.screen, COLOR_BUTTON, self.buttons["autosave"])
            autosave_value = self.autosave_options[self.current_autosave_index]
            if autosave_value is None:
                autosave_text = "Autoguardado: Desactivado"
            else:
                autosave_text = f"Autoguardado: Cada {autosave_value} días"
            autosave_surf = self.font_normal.render(autosave_text, True, COLOR_TEXT)
            self.screen.blit(autosave_surf, (self.buttons["autosave"].x + 10, self.buttons["autosave"].y + 10))

        # Botón para Iniciar
        if self.selected_user and self.selected_save:
            pygame.draw.rect(self.screen, (0, 150, 0), self.buttons["start_game"])
            start_text = "Empezar / Cargar"
            if not self.selected_save.startswith("partida_"): # Heurística simple
                 start_text = "Cargar Partida"
            start_surf = self.font_header.render(start_text, True, COLOR_TEXT)
            self.screen.blit(start_surf, (self.buttons["start_game"].centerx - start_surf.get_width() // 2, self.buttons["start_game"].centery - start_surf.get_height() // 2))

        pygame.display.flip()