# === ui/main_menu.py ===
from numpy import character
import pygame
import os
import random
import math
from math import sin
from game.character import Character
from core.session import GameSession
from core.settings import COLORS, get_player_sprite_path, get_player_data_path, get_star_sprite_path
from ui.character_creator import CharacterCreator

from core.settings import FONTS

pygame.font.init()

TITLE_FONT_SIZE = 64  # Ajuste selon la lisibilité
title_font = pygame.font.Font(FONTS["title"], TITLE_FONT_SIZE)


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
        scaled = pygame.transform.scale(
            frame, (int(32 * self.scale), int(32 * self.scale))
        )
        surface.blit(scaled, (self.x, self.y))


class MainMenu:
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
            print(f"[AVERTISSEMENT] Aucun sprite trouvé pour {session.name}, chargement d’un sprite par défaut.")
            self.sprite_path = "assets/sprites/default_character.png"

        self.char_pos = (350, 250)
        self.avatar_rect = pygame.Rect(self.char_pos[0], self.char_pos[1], 48, 96)
        self.play_rect = pygame.Rect(470, 250, 100, 100)

        # Animation idle/rotation: charge plusieurs frames si disponibles
        self.idle_frames = self.load_idle_frames(self.sprite_path)
        self.idle_timer = 0
        self.idle_speed = 0.15

        # Étoiles animées
        self.star_frames = self.load_star_frames(get_star_sprite_path())
        self.stars = [Star(self.star_frames, screen.get_width(), screen.get_height()) for _ in range(50)]
    def load_idle_frames(self, sprite_path):
        # Charge les frames d'animation du sprite (idle/rotation)
        # Si spritesheet, découpe les frames, sinon charge une seule image
        try:
            sheet = pygame.image.load(sprite_path).convert_alpha()
            width, height = sheet.get_size()
            # Supposons 7 frames horizontales (idle/rotation)
            frame_count = 7
            frame_w = width // frame_count if width >= frame_count * 48 else 48
            frames = []
            for i in range(frame_count):
                frame = pygame.Surface((frame_w, height), pygame.SRCALPHA)
                frame.blit(sheet, (0, 0), (i * frame_w, 0, frame_w, height))
                frames.append(frame)
            return frames
        except Exception as e:
            print(f"[ERREUR] Chargement sprite: {e}")
            return [pygame.image.load(sprite_path).convert_alpha()]


    def load_star_frames(self, path):
        sheet = pygame.image.load(path).convert_alpha()
        frames = []
        for i in range(4):
            frame = pygame.Surface((32, 32), pygame.SRCALPHA)
            frame.blit(sheet, (0, 0), (i * 32, 0, 32, 32))
            frames.append(frame)
        return frames

    def run(self):
        print(f"[MENU] Lancement du menu principal pour {self.session.name}")
        font = pygame.font.Font(None, 48)
        clock = pygame.time.Clock()

        while self.running:
            dt = clock.tick(30)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    print("[MENU] Fermeture du menu principal")
                    self.running = False
                    return "quit", self.session.name

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.avatar_rect.collidepoint(event.pos):
                        print(f"[MENU] Clic sur l’avatar à {event.pos}: retour dans CharacterCreator")
                        return "new", self.session.name

                    elif self.play_rect.collidepoint(event.pos):
                        print(f"[MENU] Clic sur la zone de jeu à {event.pos}: démarrage du jeu")
                        return "load", self.session.name

            # === AFFICHAGE ===
            self.screen.fill((10, 10, 30))  # Fond nuit
            self.screen.blit(self.bg_image, (0, 0))
            for star in self.stars:
                star.update()
                star.draw(self.screen)

            # Oscillation de teinte pour le titre
            tick = pygame.time.get_ticks()
            osc = (math.sin(tick * 0.002) + 1) / 2
            r = int(160 * (1 - osc) + 85 * osc)
            g = int(250 * (1 - osc) + 100 * osc)
            b = int(255 * (1 - osc) + 190 * osc)
            color_main = (r, g, b)
            color_shadow = (30, 30, 60)
            title_text = "ProgMyst_V0.1"
            x, y = 180, 150
            text_surface = title_font.render(title_text, True, color_main)
            glow_surface = title_font.render(title_text, True, (r, g, b, 50))
            shadow_surface = title_font.render(title_text, True, color_shadow)
            shadow_offset = 4
            self.screen.blit(shadow_surface, (x + shadow_offset, y + shadow_offset))
            self.screen.blit(glow_surface, (x - 1, y - 1))
            self.screen.blit(glow_surface, (x + 1, y + 1))
            self.screen.blit(text_surface, (x, y))

            # Animation du sprite (idle/rotation)
            self.idle_timer += self.idle_speed
            frame_idx = int(self.idle_timer) % len(self.idle_frames)
            frame = self.idle_frames[frame_idx]
            self.screen.blit(frame, self.char_pos)

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
                    if len(text) < 20:
                        text += event.unicode

        screen.fill((30, 30, 30))
        prompt = font.render("Entrez votre prénom :", True, pygame.Color("white"))
        txt_surface = font.render(text, True, color)
        width = max(400, txt_surface.get_width() + 10)
        input_box.w = width
        screen.blit(prompt, (250, 200))
        screen.blit(txt_surface, (input_box.x + 5, input_box.y + 5))
        pygame.draw.rect(screen, color, input_box, 2)

        pygame.display.flip()
        clock.tick(30)

    return text.strip()
