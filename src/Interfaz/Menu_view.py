import pygame
from .Constantes import SIM_WIDTH, SCREEN_HEIGHT, COLOR_BACKGROUND, COLOR_TEXT, COLOR_BUTTON, COLOR_SELECTED, UI_WIDTH

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
        self.input_user_active = False
        self.input_save_active = False
        self.rename_active = False

        self.buttons = {
            "new_user": pygame.Rect(SIM_WIDTH + 50, 200, 300, 40),
            "new_save": pygame.Rect(SIM_WIDTH + 50, 450, 300, 40),
            "rename_save": pygame.Rect(SIM_WIDTH + 50, 500, 300, 40),
            "delete_save": pygame.Rect(SIM_WIDTH + 50, 550, 145, 40),
            "start_game": pygame.Rect(SIM_WIDTH + 205, 550, 145, 40)
        }

    def handle_event(self, event):
        """Maneja los eventos de Pygame para el menú."""
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
                    self.input_save_active = False # Resetear input de guardado
                    # Devuelve una solicitud para que el controlador cargue las partidas de este usuario
                    return {"type": "select_user", "username": user}

            # Lógica para seleccionar partidas
            save_y_start = 300
            for i, save in enumerate(self.saves or []):
                save_rect = pygame.Rect(SIM_WIDTH + 50, save_y_start + i * 30, 300, 30)
                if save_rect.collidepoint(event.pos):
                    self.selected_save = save
                    self.rename_active = False
                    # Solicitar al controlador que obtenga la fecha de esta partida
                    return {"type": "select_save", "user": self.selected_user, "save": save}

            # Lógica para botones
            if self.buttons["new_user"].collidepoint(event.pos):
                self.input_user_active = True
                self.rename_active = False
                self.input_save_active = False
                self.input_text = ""
                return None
            
            if self.buttons["new_save"].collidepoint(event.pos) and self.selected_user:
                # Activar input para el nombre de la nueva partida
                self.input_save_active = True
                self.input_user_active = False
                self.rename_active = False
                self.input_text = ""
                return None

            if self.buttons["rename_save"].collidepoint(event.pos) and self.selected_save:
                self.rename_active = True
                self.input_save_active = False
                self.input_user_active = False
                # Pre-rellenar el campo de texto con el nombre actual sin la extensión
                self.input_text = self.selected_save.replace(".json", "").replace("_", " ")
                return None

            if self.buttons["delete_save"].collidepoint(event.pos) and self.selected_user and self.selected_save:
                # Devuelve el comando para eliminar la partida seleccionada
                return {"type": "delete_save", "user": self.selected_user, "save": self.selected_save}



            if self.buttons["start_game"].collidepoint(event.pos) and self.selected_user and self.selected_save:
                return {"type": "start_game", "user": self.selected_user, "save": self.selected_save}

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                if self.input_user_active and self.input_text:
                    username = self.input_text
                    self.input_user_active = False
                    self.input_text = ""
                    return {"type": "create_user", "username": username}
                elif self.input_save_active and self.input_text and self.selected_user:
                    # Cuando se confirma el nombre de la nueva partida, se inicia el juego
                    # El nombre se limpia y se le añade .json
                    save_name = self.input_text.strip().replace(" ", "_") + ".json"
                    self.selected_save = save_name
                    self.input_save_active = False
                    self.input_text = ""
                    # Se devuelve el comando para iniciar el juego con la nueva partida
                    return {"type": "start_game", "user": self.selected_user, "save": self.selected_save}
                elif self.rename_active and self.input_text and self.selected_user and self.selected_save:
                    new_name = self.input_text.strip().replace(" ", "_") + ".json"
                    command = {
                        "type": "rename_save",
                        "user": self.selected_user,
                        "old_name": self.selected_save,
                        "new_name": new_name
                    }
                    self.rename_active = False
                    return command

            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            else:
                self.input_text += event.unicode
        
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
        if self.input_user_active:
            input_surf = self.font_normal.render(self.input_text + "|", True, COLOR_TEXT)
        else:
            input_surf = self.font_normal.render("Nuevo Usuario", True, COLOR_TEXT)
        self.screen.blit(input_surf, (self.buttons["new_user"].x + 10, self.buttons["new_user"].y + 10))

        # Sección de Partidas
        if self.selected_user:
            self.screen.blit(self.font_header.render(f"Partidas de {self.selected_user}", True, COLOR_TEXT), (SIM_WIDTH + 20, 250))
            save_y_start = 300
            for i, save in enumerate(self.saves or []):
                color = COLOR_SELECTED if save == self.selected_save else COLOR_TEXT
                save_name = save.replace(".json", "").replace("_", " ").capitalize()
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
                    pass # Si hay error en el formato, simplemente no se muestra.
            
            # Botón para nueva partida
            pygame.draw.rect(self.screen, COLOR_BUTTON, self.buttons["new_save"]) # Botón de nueva partida
            if self.input_save_active and not self.rename_active:
                new_save_surf = self.font_normal.render(self.input_text + "|", True, COLOR_TEXT)
            else:
                new_save_surf = self.font_normal.render("Nueva Partida", True, COLOR_TEXT)
            self.screen.blit(new_save_surf, (self.buttons["new_save"].x + 10, self.buttons["new_save"].y + 10))

            # Botón para renombrar partida (solo visible si hay una partida seleccionada)
            if self.selected_save:
                pygame.draw.rect(self.screen, COLOR_BUTTON, self.buttons["rename_save"])
                if self.rename_active:
                    rename_surf = self.font_normal.render(self.input_text + "|", True, COLOR_TEXT)
                else:
                    rename_surf = self.font_normal.render("Renombrar Partida", True, COLOR_TEXT)
                self.screen.blit(rename_surf, (self.buttons["rename_save"].x + 10, self.buttons["rename_save"].y + 10))
                
                # Botón para Eliminar Partida
                pygame.draw.rect(self.screen, (200, 50, 50), self.buttons["delete_save"])
                delete_surf = self.font_normal.render("Eliminar", True, COLOR_TEXT)
                self.screen.blit(delete_surf, (self.buttons["delete_save"].centerx - delete_surf.get_width() // 2, self.buttons["delete_save"].centery - delete_surf.get_height() // 2))

                # Botón para Iniciar
                pygame.draw.rect(self.screen, (0, 150, 0), self.buttons["start_game"])
                start_text = "Cargar"
                start_surf = self.font_normal.render(start_text, True, COLOR_TEXT)
                self.screen.blit(start_surf, (self.buttons["start_game"].centerx - start_surf.get_width() // 2, self.buttons["start_game"].centery - start_surf.get_height() // 2))

        pygame.display.flip()