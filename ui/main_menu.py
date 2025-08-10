# === ui/main_menu.py ===
import os
import random
import math
import pygame
from core.settings import get_star_sprite_path, COLORS
from ui.uitools import BorderManager
from core.settings import FONTS

pygame.font.init()
title_font = pygame.font.Font(FONTS["title"], 64)
button_font = pygame.font.Font(FONTS["button"], 24)


class Star:
    def __init__(self, frames, width, height):
        self.frames = frames
        self.x = random.randint(0, width)
        self.y = random.randint(0, height)
        self.scale = random.uniform(0.5, 1.5)
        self.timer = random.uniform(0, 2)
        self.speed = random.uniform(0.05, 0.15)

    def update(self):
        self.timer += self.speed
        if self.timer >= len(self.frames):
            self.timer = 0

    def draw(self, surface):
        frame = self.frames[int(self.timer)]
        scaled = pygame.transform.scale(frame, (int(32 * self.scale), int(32 * self.scale)))
        surface.blit(scaled, (self.x, self.y))


class MainMenu:
    def draw_button(self, rect, text, hovered=False, clicked=False, color_base=(255,255,255), color_osc=None):
        """Affiche un bouton stylé avec oscillation, hover/click, ombre, glow, descente, sans modifier les assets en place."""
        # Descendre le bouton si hovered
        button_rect = rect.copy()
        if hovered:
            button_rect.y += 3

        # Cadre (toujours normal, jamais modifié en place)
        self.border_mgr.draw_border(self.screen, button_rect, border_thickness=4)

        # Couleur oscillante
        r, g, b = color_base
        if color_osc:
            r, g, b = color_osc

        # Sombre si hovered/clicked
        if hovered:
            r = max(30, int(r * 0.7))
            g = max(30, int(g * 0.7))
            b = max(30, int(b * 0.7))
        if clicked:
            r = max(20, int(r * 0.5))
            g = max(20, int(g * 0.5))
            b = max(20, int(b * 0.5))
        button_color = (r, g, b)
        button_shadow = (20, 20, 40)

        play_font = button_font
        play_text = play_font.render(text, True, button_color)
        glow_text = play_font.render(text, True, (r, g, b, 80 if hovered else 50))
        shadow_text = play_font.render(text, True, button_shadow)
        text_rect = play_text.get_rect(center=button_rect.center)

        # Ombre du texte (pas d'ombre si hovered)
        if not hovered:
            self.screen.blit(shadow_text, (text_rect.x + 2, text_rect.y + 2))
        # Glow
        self.screen.blit(glow_text, (text_rect.x - 1, text_rect.y - 1))
        self.screen.blit(glow_text, (text_rect.x + 1, text_rect.y + 1))
        # Texte principal
        self.screen.blit(play_text, text_rect)
    def __init__(self, screen, session):
        self.screen = screen
        self.running = True
        self.session = session
        self.bg_image = pygame.image.load("assets/other/blueaura.png").convert()
        self.bg_image = pygame.transform.scale(self.bg_image, (screen.get_width(), screen.get_height()))
        
        # Sprite du personnage (idle/rotation)
        self.data_path = session.data_path
        self.sprite_path = session.sprite_path
        if not os.path.exists(self.sprite_path):
            print(f"[AVERTISSEMENT] Aucun sprite trouvé pour {session.name}, chargement d'un sprite par défaut.")
            self.sprite_path = "assets/sprites/default_character.png"

        self.char_pos = (350, 250)
        self.avatar_rect = pygame.Rect(self.char_pos[0], self.char_pos[1], 48, 96)
        self.play_rect = pygame.Rect(300, 400, 150, 50)
        self.border_mgr = BorderManager()

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

        # Étoiles animées
        self.star_frames = self.load_star_frames(get_star_sprite_path())
        self.stars = [Star(self.star_frames, self.screen.get_width(), self.screen.get_height()) for _ in range(50)]
    
    def load_idle_frames(self, sprite_path):
        """Charge les frames d'animation spécifiques du sprite (grille 12x8, frames: 1,4,13,28,37,40,25,16)"""
        try:
            sheet = pygame.image.load(sprite_path).convert_alpha()
            frame_width, frame_height = 48, 96
            columns, rows = 12, 8
            
            # Frames spécifiques à charger (indices 0-based: 0,3,12,27,36,39,24,15)
            frame_indices = [1, 4, 13, 28, 37, 40, 25, 16]
            frames = []
            
            for idx in frame_indices:
                col = idx % columns
                row = idx // columns
                rect = pygame.Rect(col * frame_width, row * frame_height, frame_width, frame_height)
                frame = sheet.subsurface(rect)
                frames.append(frame)
            
            return frames
        except (pygame.error, FileNotFoundError) as e:
            print(f"[ERREUR] Chargement sprite: {e}")
            # Fallback: créer une frame de substitution
            fallback = pygame.Surface((48, 96))
            fallback.fill((255, 0, 255))  # Magenta pour debug
            return [fallback]

    def load_hover_frames(self, sprite_path):
        """Charge les frames d'animation hover du sprite (frames: 49, 52, 61, 76, 85, 88, 73, 64)"""
        try:
            sheet = pygame.image.load(sprite_path).convert_alpha()
            frame_width, frame_height = 48, 96
            columns = 12
            
            # Frames pour hover (indices 0-based)
            frame_indices = [49, 52, 61, 76, 85, 88, 73, 64]
            frames = []
            
            for idx in frame_indices:
                col = idx % columns
                row = idx // columns
                rect = pygame.Rect(col * frame_width, row * frame_height, frame_width, frame_height)
                frame = sheet.subsurface(rect)
                frames.append(frame)
            
            return frames
        except (pygame.error, FileNotFoundError) as e:
            print(f"[ERREUR] Chargement sprite hover: {e}")
            # Fallback: utiliser les frames idle
            return self.idle_frames if hasattr(self, 'idle_frames') else [pygame.Surface((48, 96))]

    def load_electric_frames(self):
        """Charge l'animation électrique depuis assets/other/electricaura.png (480x192, 2x5 grille, 7 frames)"""
        try:
            sheet = pygame.image.load("assets/other/electricaura.png").convert_alpha()
            frame_width, frame_height = 96, 96  # 480/5 = 96, 192/2 = 96
            frames = []
            
            # Charger les 7 premières frames (ligne 1: 5 frames, ligne 2: 2 frames)
            for row in range(2):
                for col in range(5 if row == 0 else 2):
                    if len(frames) >= 7:  # Arrêter à 7 frames
                        break
                    rect = pygame.Rect(col * frame_width, row * frame_height, frame_width, frame_height)
                    frame = sheet.subsurface(rect)
                    frames.append(frame)
                if len(frames) >= 7:
                    break
            
            return frames
        except (pygame.error, FileNotFoundError) as e:
            print(f"[ERREUR] Chargement animation électrique: {e}")
            # Fallback: créer une frame vide
            fallback = pygame.Surface((96, 96))
            fallback.fill((0, 255, 255, 100))  # Cyan semi-transparent
            return [fallback]

    def load_star_frames(self, path):
        sheet = pygame.image.load(path).convert_alpha()
        frames = []
        for i in range(4):
            frame = sheet.subsurface(pygame.Rect(i * 32, 0, 32, 32))
            frames.append(frame)
        return frames

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
            self.screen.fill((10, 10, 30))  # Fond nuit
            self.screen.blit(self.bg_image, (0, 0))
            for star in self.stars:
                star.update()
                star.draw(self.screen)

            # Titre avec oscillation
            tick = pygame.time.get_ticks()
            osc = (math.sin(tick * 0.002) + 1) / 2
            r, g, b = int(160 * (1 - osc) + 85 * osc), int(250 * (1 - osc) + 100 * osc), int(255 * (1 - osc) + 190 * osc)
            color_main = (r, g, b)
            color_shadow = (30, 30, 60)
            title_text = "ProgMyst_V0.1"
            x, y = 180, 150
            
            text_surface = title_font.render(title_text, True, color_main)
            glow_surface = title_font.render(title_text, True, (r, g, b, 50))
            shadow_surface = title_font.render(title_text, True, color_shadow)
            
            self.screen.blit(shadow_surface, (x + 4, y + 4))
            self.screen.blit(glow_surface, (x - 1, y - 1))
            self.screen.blit(glow_surface, (x + 1, y + 1))
            self.screen.blit(text_surface, (x, y))

            # Animation du sprite avec états hover/clicked
            avatar_hovered = self.is_hovered(self.avatar_rect)
            
            if self.avatar_clicked:
                # Animation électrique
                electric_frame_idx = int(self.electric_timer) % len(self.electric_frames)
                electric_frame = self.electric_frames[electric_frame_idx]
                
                # Afficher le sprite avec opacité décroissante
                if self.char_opacity > 0:
                    self.idle_timer += self.idle_speed
                    frame_idx = int(self.idle_timer) % len(self.idle_frames)
                    char_frame = self.idle_frames[frame_idx].copy()
                    char_frame.set_alpha(self.char_opacity)
                    self.screen.blit(char_frame, self.char_pos)
                
                # Afficher l'effet électrique par-dessus
                electric_pos = (self.char_pos[0]- 24, self.char_pos[1])  # Centrer l'effet
                self.screen.blit(electric_frame, electric_pos)
                
            elif avatar_hovered:
                # Animation hover
                self.idle_timer += self.idle_speed
                frame_idx = int(self.idle_timer) % len(self.hover_frames)
                frame = self.hover_frames[frame_idx]
                self.screen.blit(frame, self.char_pos)
            else:
                # Animation idle normale
                self.idle_timer += self.idle_speed
                frame_idx = int(self.idle_timer) % len(self.idle_frames)
                frame = self.idle_frames[frame_idx]
                self.screen.blit(frame, self.char_pos)

            # --- BOUTON JOUER refactorisé ---
            button_hovered = self.is_hovered(self.play_rect)
            button_clicked = self.get_clicked(self.play_rect)
            self.draw_button(
                self.play_rect,
                "JOUER",
                hovered=button_hovered,
                clicked=button_clicked,
                color_base=(r, g, b),
                color_osc=(r, g, b)
            )

            pygame.display.flip()


# === Input du nom du joueur au lancement (si aucun fichier JSON trouvé) ===
def ask_player_name(screen):
    font = pygame.font.Font(None, 36)
    clock = pygame.time.Clock()
    input_box = pygame.Rect(200, 250, 400, 50)
    color_inactive = COLORS['text_highlight']
    color_active = COLORS['primary_bg']
    color = color_inactive
    active = False
    text = ''
    done = False

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
                color = color_active if active else color_inactive
            elif event.type == pygame.KEYDOWN and active:
                if event.key == pygame.K_RETURN:
                    done = True
                elif event.key == pygame.K_BACKSPACE:
                    text = text[:-1]
                else:
                    text += event.unicode

        screen.fill(COLORS['primary_bg'])
        txt_surface = font.render(text, True, color)
        width = max(200, txt_surface.get_width()+10)
        input_box.w = width
        screen.blit(txt_surface, (input_box.x+5, input_box.y+5))
        pygame.draw.rect(screen, color, input_box, 2)
        pygame.display.flip()
        clock.tick(30)

    return text
