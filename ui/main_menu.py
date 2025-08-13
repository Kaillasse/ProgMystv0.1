# === ui/main_menu.py ===
import os
import pygame
from core.settings import get_star_sprite_path, FONTS
from ui.uitools import (BorderManager, load_star_frames, load_background_image, 
                       create_starry_background, draw_starry_background, 
                       draw_stylish_button, oscillate_color, draw_text_with_effects)

pygame.font.init()
title_font = pygame.font.Font(FONTS["title"], 64)
button_font = pygame.font.Font(FONTS["button"], 24)


class MainMenu:
    def __init__(self, screen, session):
        self.screen = screen
        self.running = True
        self.session = session

        # Chargement du fond et des étoiles avec uitools
        self.bg_image = load_background_image("assets/other/blueaura.png", (screen.get_width(), screen.get_height()))
        self.star_frames = load_star_frames(get_star_sprite_path())
        self.stars = create_starry_background(self.star_frames, screen.get_width(), screen.get_height(), 50)

        # Sprite du personnage (idle/rotation)
        self.data_path = session.data_path
        self.sprite_path = session.sprite_path
        if not os.path.exists(self.sprite_path):
            print(f"[AVERTISSEMENT] Aucun sprite trouvé pour {session.name}, chargement d'un sprite par défaut.")
            self.sprite_path = "assets/sprites/default_character.png"

        # Double la taille d'affichage et centre le personnage et le bouton
        self.sprite_scale = 2
        screen_w, screen_h = self.screen.get_width(), self.screen.get_height()
        title_y = 150
        button_y = 400 + 25  # bouton centré verticalement (y + hauteur/2)
        char_y = (title_y + button_y) // 2 - (96 * self.sprite_scale) // 2
        char_x = (screen_w // 2) - (48 * self.sprite_scale) // 2
        self.char_pos = (char_x, char_y)
        self.avatar_rect = pygame.Rect(self.char_pos[0], self.char_pos[1], 48 * self.sprite_scale, 96 * self.sprite_scale)
        self.play_rect = pygame.Rect((screen_w - 150) // 2, 400, 150, 50)
        self.border_mgr = BorderManager(session=session)

        # Animation idle/rotation: charge plusieurs frames si disponibles
        self.idle_frames = self.load_idle_frames(self.sprite_path)
        self.hover_frames = self.load_hover_frames(self.sprite_path)
        self.electric_frames = self.load_electric_frames()
        self.idle_timer = 0
        self.idle_speed = 0.15

        # États d'interaction
        self.avatar_clicked = False
        self.electric_timer = 0
        self.electric_speed = 0.2
        self.char_opacity = 255
    
    def load_idle_frames(self, sprite_path):
        """Charge les frames d'animation spécifiques du sprite (grille 12x8, frames: 1,4,13,28,37,40,25,16)"""
        try:
            sheet = pygame.image.load(sprite_path).convert_alpha()
            frame_width, frame_height = 48, 96
            columns = 12
            frame_indices = [1, 4, 13, 28, 37, 40, 25, 16]
            frames = []
            for idx in frame_indices:
                col = idx % columns
                row = idx // columns
                rect = pygame.Rect(col * frame_width, row * frame_height, frame_width, frame_height)
                frame = sheet.subsurface(rect)
                # Double la taille d'affichage
                frame = pygame.transform.scale(frame, (frame_width * self.sprite_scale, frame_height * self.sprite_scale))
                frames.append(frame)
            return frames
        except Exception as e:
            print(f"[ERREUR] Chargement sprite: {e}")
            fallback = pygame.Surface((48 * self.sprite_scale, 96 * self.sprite_scale))
            fallback.fill((255, 0, 255))
            return [fallback]

    def load_hover_frames(self, sprite_path):
        """Charge les frames d'animation hover du sprite (frames: 49, 52, 61, 76, 85, 88, 73, 64)"""
        try:
            sheet = pygame.image.load(sprite_path).convert_alpha()
            frame_width, frame_height = 48, 96
            columns = 12
            frame_indices = [49, 52, 61, 76, 85, 88, 73, 64]
            frames = []
            for idx in frame_indices:
                col = idx % columns
                row = idx // columns
                rect = pygame.Rect(col * frame_width, row * frame_height, frame_width, frame_height)
                frame = sheet.subsurface(rect)
                frame = pygame.transform.scale(frame, (frame_width * self.sprite_scale, frame_height * self.sprite_scale))
                frames.append(frame)
            return frames
        except Exception as e:
            print(f"[ERREUR] Chargement sprite hover: {e}")
            return self.idle_frames if hasattr(self, 'idle_frames') else [pygame.Surface((48 * self.sprite_scale, 96 * self.sprite_scale))]

    def load_electric_frames(self):
        """Charge l'animation électrique depuis assets/other/electricaura.png (480x192, 2x5 grille, 7 frames)"""
        try:
            sheet = pygame.image.load("assets/other/electricaura.png").convert_alpha()
            frame_width, frame_height = 96, 96
            scale = self.sprite_scale
            frames = []
            for row in range(2):
                for col in range(5 if row == 0 else 2):
                    if len(frames) >= 7:
                        break
                    rect = pygame.Rect(col * frame_width, row * frame_height, frame_width, frame_height)
                    frame = sheet.subsurface(rect)
                    frame = pygame.transform.scale(frame, (frame_width * scale, frame_height * scale))
                    frames.append(frame)
                if len(frames) >= 7:
                    break
            return frames
        except Exception as e:
            print(f"[ERREUR] Chargement animation électrique: {e}")
            fallback = pygame.Surface((96 * self.sprite_scale, 96 * self.sprite_scale))
            fallback.fill((0, 255, 255, 100))
            return [fallback]

    def is_hovered(self, rect):
        """Vérifie si la souris survole un rectangle"""
        mouse_pos = pygame.mouse.get_pos()
        return rect.collidepoint(mouse_pos)

    def get_clicked(self, rect):
        """Vérifie si un rectangle est cliqué"""
        return self.is_hovered(rect) and pygame.mouse.get_pressed()[0]

    def run(self):
        print(f"[MENU] Lancement du menu principal pour {self.session.name}")
        clock = pygame.time.Clock()

        while self.running:
            clock.tick(30)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    print("[MENU] Fermeture du menu principal")
                    self.running = False
                    return "quit", self.session.name

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.avatar_rect.collidepoint(event.pos):
                        print(f"[MENU] Clic sur l'avatar à {event.pos}: animation électrique")
                        self.avatar_clicked = True
                        self.electric_timer = 0
                        self.char_opacity = 255

                    elif self.play_rect.collidepoint(event.pos):
                        print(f"[MENU] Clic sur le bouton Jouer à {event.pos}: démarrage du jeu")
                        return "load", self.session.name

            # Gestion de l'animation électrique
            if self.avatar_clicked:
                self.electric_timer += self.electric_speed
                # Calculer l'opacité décroissante
                progress = self.electric_timer / len(self.electric_frames)
                self.char_opacity = max(0, int(255 * (1 - progress)))
                
                # Si l'animation est terminée, retourner au créateur de personnage
                if self.electric_timer >= len(self.electric_frames):
                    print("[MENU] Animation électrique terminée, retour au créateur")
                    return "new", self.session.name

            # === AFFICHAGE ===
            # Fond étoilé avec uitools
            draw_starry_background(self.screen, self.stars, self.bg_image)

            # Titre avec oscillation (utilise uitools)
            tick = pygame.time.get_ticks()
            color_main = oscillate_color(tick)
            title_text = "ProgMyst_V0.1"
            title_pos = (self.screen.get_width() // 2, 150)  # Centré horizontalement
            draw_text_with_effects(self.screen, title_font, title_text, title_pos, color_main, (4, 4), 1)

            # Animation du sprite avec états hover/clicked
            avatar_hovered = self.is_hovered(self.avatar_rect)
            
            # --- Affichage du personnage animé et de l'aura ---
            frame_list = self.idle_frames
            if self.avatar_clicked:
                # Animation électrique
                electric_frame_idx = int(self.electric_timer) % len(self.electric_frames)
                electric_frame = self.electric_frames[electric_frame_idx]
                if self.char_opacity > 0:
                    self.idle_timer += self.idle_speed
                    frame_idx = int(self.idle_timer) % len(self.idle_frames)
                    char_frame = self.idle_frames[frame_idx].copy()
                    char_frame.set_alpha(self.char_opacity)
                    self.screen.blit(char_frame, self.char_pos)
                electric_pos = (self.char_pos[0] - 24 * self.sprite_scale, self.char_pos[1])
                self.screen.blit(electric_frame, electric_pos)
            elif avatar_hovered:
                frame_list = self.hover_frames
            if not self.avatar_clicked:
                self.idle_timer += self.idle_speed
                frame_idx = int(self.idle_timer) % len(frame_list)
                frame = frame_list[frame_idx]
                self.screen.blit(frame, self.char_pos)

            # --- BOUTON Jouer refactorisé avec uitools ---
            button_hovered = self.is_hovered(self.play_rect)
            button_clicked = self.get_clicked(self.play_rect)
            draw_stylish_button(
                self.screen,
                self.border_mgr,
                self.play_rect,
                "Jouer",
                button_font,
                tick,
                hovered=button_hovered,
                clicked=button_clicked,
                color_base=color_main
            )

            pygame.display.flip()


# === Input du nom du joueur au lancement (si aucun fichier JSON trouvé) ===
def ask_player_name(screen):
    clock = pygame.time.Clock()
    input_box = pygame.Rect(200, 280, 400, 60)
    active = False
    text = ''
    done = False
    
    # Initialisation des éléments d'interface avec uitools
    border_mgr = BorderManager()  # Pas de session lors de la saisie du nom
    star_frames = load_star_frames(get_star_sprite_path())
    stars = create_starry_background(star_frames, screen.get_width(), screen.get_height(), 50)
    bg_image = load_background_image("assets/other/blueaura.png", (screen.get_width(), screen.get_height()))

    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return None
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if input_box.collidepoint(event.pos):
                    active = not active
                else:
                    active = False
            elif event.type == pygame.KEYDOWN and active:
                if event.key == pygame.K_RETURN:
                    if text.strip():  # S'assurer qu'il y a du texte
                        done = True
                elif event.key == pygame.K_BACKSPACE:
                    text = text[:-1]
                else:
                    if len(text) < 20:  # Limiter la longueur du nom
                        text += event.unicode

        # === AFFICHAGE ===
        # Fond étoilé avec uitools
        draw_starry_background(screen, stars, bg_image)

        # Titre oscillant avec uitools
        tick = pygame.time.get_ticks()
        color_main = oscillate_color(tick)
        
        # Question principale avec uitools
        question_text = "Quel est votre nom ?"
        question_pos = (screen.get_width() // 2, 200)
        draw_text_with_effects(screen, button_font, question_text, question_pos, color_main, (2, 2), 1)

        # Cadre d'entrée de texte avec bordure uitools
        # Ajuster la taille en fonction du texte
        if text:
            text_surface = button_font.render(text, True, (255, 255, 255))
            text_width = text_surface.get_width()
        else:
            text_width = 0
        
        # Taille minimale et adaptation au texte
        box_width = max(300, text_width + 40)
        input_box.width = box_width
        input_box.centerx = screen.get_width() // 2
        
        # Dessiner le cadre avec uitools
        if active:
            border_mgr.draw_border(screen, input_box, border_thickness=6)
        else:
            border_mgr.draw_border(screen, input_box, border_thickness=4)
        
        # Fond semi-transparent pour la zone de texte
        text_bg = pygame.Surface((input_box.width - 20, input_box.height - 20))
        text_bg.fill((20, 20, 40))
        text_bg.set_alpha(180)
        screen.blit(text_bg, (input_box.x + 10, input_box.y + 10))
        
        # Texte entré par l'utilisateur
        if text:
            text_surface = button_font.render(text, True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=(input_box.centerx, input_box.centery))
            screen.blit(text_surface, text_rect)
        
        # Curseur clignotant si actif
        if active and (tick // 500) % 2:  # Clignote toutes les 500ms
            cursor_x = input_box.centerx + (text_width // 2) if text else input_box.centerx
            pygame.draw.line(screen, (255, 255, 255), 
                           (cursor_x + 5, input_box.y + 15), 
                           (cursor_x + 5, input_box.y + input_box.height - 15), 2)
        
        # Instructions en bas avec uitools
        instruction_font = pygame.font.Font(FONTS["button"], 18)
        if not active and not text:
            instruction_text = "Cliquez dans le cadre pour saisir votre nom"
            instruction_pos = (screen.get_width() // 2, 380)
            draw_text_with_effects(screen, instruction_font, instruction_text, instruction_pos, (150, 150, 150), (1, 1), 0)
        elif active:
            instruction_text = "Appuyez sur Entrée pour valider"
            instruction_pos = (screen.get_width() // 2, 380)
            draw_text_with_effects(screen, instruction_font, instruction_text, instruction_pos, color_main, (1, 1), 0)

        pygame.display.flip()
        clock.tick(30)

    return text
