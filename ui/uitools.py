import os
import math
import random
import pygame
from core.session import SessionManager

# === Utilitaires pour couleurs et effets ===
def oscillate_color(tick, base1=(160, 250, 255), base2=(85, 100, 190)):
    """Oscille entre deux couleurs selon le temps."""
    osc = (math.sin(tick * 0.002) + 1) / 2
    r = int(base1[0] * (1 - osc) + base2[0] * osc)
    g = int(base1[1] * (1 - osc) + base2[1] * osc)
    b = int(base1[2] * (1 - osc) + base2[2] * osc)
    return (r, g, b)

def draw_text_with_effects(screen, font, text, pos, color_main, shadow_offset=(2, 2), glow_offset=1):
    """Dessine un texte avec ombre et effet de glow."""
    color_shadow = (30, 30, 60)
    
    # Surfaces de texte
    text_surface = font.render(text, True, color_main)
    shadow_surface = font.render(text, True, color_shadow)
    glow_surface = font.render(text, True, color_main)
    
    # Position centrée si pos est un tuple (x, y)
    if isinstance(pos, tuple):
        text_rect = text_surface.get_rect(center=pos)
    else:
        text_rect = pos
    
    # Dessiner ombre
    shadow_pos = (text_rect.x + shadow_offset[0], text_rect.y + shadow_offset[1])
    screen.blit(shadow_surface, shadow_pos)
    
    # Dessiner glow
    for dx in [-glow_offset, glow_offset]:
        for dy in [-glow_offset, glow_offset]:
            if dx != 0 or dy != 0:
                glow_pos = (text_rect.x + dx, text_rect.y + dy)
                screen.blit(glow_surface, glow_pos)
    
    # Dessiner texte principal
    screen.blit(text_surface, text_rect)
    
    return text_rect

# === Classe Star pour les étoiles animées ===
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

# === Fonctions utilitaires pour les assets ===
def load_star_frames(path):
    """Charge les frames d'étoiles animées (spritesheet 4x1)."""
    try:
        sheet = pygame.image.load(path).convert_alpha()
        frames = []
        for i in range(4):
            frame = sheet.subsurface(pygame.Rect(i * 32, 0, 32, 32))
            frames.append(frame)
        return frames
    except (pygame.error, FileNotFoundError):
        # Fallback: créer une étoile simple
        fallback_star = pygame.Surface((32, 32))
        fallback_star.fill((255, 255, 0))
        return [fallback_star]

def load_background_image(path, screen_size):
    """Charge et redimensionne une image de fond."""
    try:
        bg_image = pygame.image.load(path).convert()
        return pygame.transform.scale(bg_image, screen_size)
    except (pygame.error, FileNotFoundError):
        return None

def create_starry_background(star_frames, screen_width, screen_height, star_count=50):
    """Crée une liste d'étoiles pour l'arrière-plan."""
    return [Star(star_frames, screen_width, screen_height) for _ in range(star_count)]

def draw_starry_background(screen, stars, bg_image=None, base_color=(10, 10, 30)):
    """Affiche le fond étoilé animé avec le fond bleu aura si fourni."""
    screen.fill(base_color)
    
    if bg_image:
        screen.blit(bg_image, (0, 0))
    
    for star in stars:
        star.update()
        star.draw(screen)

def draw_stylish_button(screen, border_mgr, rect, text, font, tick, hovered=False, clicked=False, 
                       color_base=None, border_thickness=4):
    """Dessine un bouton stylé avec oscillation, ombre, glow et cadre uitools."""
    if color_base is None:
        color_base = oscillate_color(tick)
    
    color_shadow = (30, 30, 60)
    
    # Descendre le bouton si hovered
    button_rect = rect.copy()
    if hovered:
        button_rect.y += 3
    
    # Cadre avec BorderManager
    border_mgr.draw_border(screen, button_rect, border_thickness=border_thickness)
    
    # Couleur du texte
    r, g, b = color_base
    if hovered:
        r, g, b = int(r * 0.8), int(g * 0.8), int(b * 0.8)
    if clicked:
        r, g, b = int(r * 0.6), int(g * 0.6), int(b * 0.6)
    
    button_color = (r, g, b)
    
    # Textes
    text_surface = font.render(text, True, button_color)
    glow_surface = font.render(text, True, (r, g, b, 80 if hovered else 50))
    shadow_surface = font.render(text, True, color_shadow)
    text_rect = text_surface.get_rect(center=button_rect.center)
    
    # Ombre du texte (pas d'ombre si hovered)
    if not hovered:
        screen.blit(shadow_surface, (text_rect.x + 2, text_rect.y + 2))
    
    # Glow
    screen.blit(glow_surface, (text_rect.x - 1, text_rect.y - 1))
    screen.blit(glow_surface, (text_rect.x + 1, text_rect.y + 1))
    
    # Texte principal
    screen.blit(text_surface, text_rect)

# === Nouvelles classes pour l'interface ===
class PrevNextButton:
    """Boutons Previous/Next avec assets gauchedroiteui.png et gauchedroitehoverui.png"""
    
    def __init__(self, x, y, is_prev=True):
        self.rect = pygame.Rect(x, y, 11, 14)
        self.is_prev = is_prev  # True pour Previous/Gauche, False pour Next/Droite
        self.hovered = False
        self.clicked = False
        self.frames_normal = []
        self.frames_hover = []
        
        self.load_assets()
    
    def load_assets(self):
        """Charge les assets prev/next (11x14px, 2 frames) ou fallback simple."""
        def fallback():
            for i in range(2):
                surf = pygame.Surface((11, 14))
                surf.fill((150, 100, 100) if i == 0 else (100, 150, 100))
                self.frames_normal.append(surf)
                self.frames_hover.append(surf.copy())
        try:
            normal = pygame.image.load("assets/ui/gauchedroiteui.png").convert_alpha()
            hover = pygame.image.load("assets/ui/gauchedroitehoverui.png").convert_alpha()
            for i in range(2):
                rect = pygame.Rect(i*11, 0, 11, 14)
                self.frames_normal.append(normal.subsurface(rect))
                self.frames_hover.append(hover.subsurface(rect))
        except Exception:
            fallback()
        if len(self.frames_normal) < 2:
            fallback()
    
    def handle_event(self, event):
        """Gère les événements de la souris"""
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.clicked = True
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.clicked = False
        return False
    
    def draw(self, screen):
        """Dessine le bouton avec l'état approprié"""
        frame_index = 0 if self.is_prev else 1
        frames = self.frames_hover if self.hovered else self.frames_normal
        screen.blit(frames[frame_index], self.rect)

class UISlider:
    SLIDER_TYPES = ["normal", "quete", "vert", "rouge", "bleu"]

    def __init__(self, x, y, min_val, max_val, initial_val, slider_type="normal", orientation="horizontal"):
        self.x = x
        self.y = y
        self.min_val = min_val
        self.max_val = max_val
        self.val = initial_val
        self.slider_type = slider_type
        self.orientation = orientation
        self.rect = pygame.Rect(x, y, 120 if orientation=="horizontal" else 24, 24 if orientation=="horizontal" else 120)
        self.hovered = False
        self.dragging = False
        self.load_assets()

    def load_assets(self):
        sheet_path = "assets/ui/sliders1.png"
        hover_path = "assets/ui/sliders.png"
        self.sheet = pygame.image.load(sheet_path).convert_alpha()
        self.sheet_hover = pygame.image.load(hover_path).convert_alpha()
        frame_w = self.sheet.get_width() // 5
        frame_h = self.sheet.get_height()
        idx = self.SLIDER_TYPES.index(self.slider_type)
        self.knob_img = self.sheet.subsurface((idx * frame_w, 0, frame_w, frame_h))
        self.knob_img_hover = self.sheet_hover.subsurface((idx * frame_w, 0, frame_w, frame_h))

    def draw(self, screen):
        # Barre de fond
        if self.orientation == "vertical":
            # Centrer la ligne du slider sur le centre du knob
            line_x = self.x + self.rect.width // 2 - 2
            pygame.draw.rect(screen, (80, 80, 120), (line_x, self.y, 4, self.rect.height), border_radius=2)
            t = (self.val - self.min_val) / (self.max_val - self.min_val)
            knob_x = self.x + (self.rect.width - self.knob_img.get_width()) // 2  # Centrer le knob
            knob_y = self.y + int(t * (self.rect.height - self.knob_img.get_height()))
            img = self.knob_img_hover if self.hovered else self.knob_img
            screen.blit(img, (knob_x, knob_y))
            self.knob_rect = pygame.Rect(knob_x, knob_y, self.knob_img.get_width(), self.knob_img.get_height())
            
        else:  # horizontal
            pygame.draw.rect(screen, (80, 80, 120), (self.x, self.y + self.rect.height // 2 - 2, self.rect.width, 4), border_radius=2)
            t = (self.val - self.min_val) / (self.max_val - self.min_val)
            knob_x = self.x + int(t * (self.rect.width - self.knob_img.get_width()))
            knob_y = self.y
            # Rotation à 90° pour les sliders horizontaux
            img = self.knob_img_hover if self.hovered else self.knob_img
            rotated_img = pygame.transform.rotate(img, 90)
            screen.blit(rotated_img, (knob_x, knob_y))
            self.knob_rect = pygame.Rect(knob_x, knob_y, rotated_img.get_width(), rotated_img.get_height())

    def handle_event(self, event):
        mouse_pos = pygame.mouse.get_pos()
        # Initialiser knob_rect si pas encore défini
        if not hasattr(self, 'knob_rect'):
            self.knob_rect = pygame.Rect(self.x, self.y, 20, 20)
            
        self.hovered = self.knob_rect.collidepoint(mouse_pos)
        if event.type == pygame.MOUSEBUTTONDOWN and self.hovered:
            self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            if self.orientation == "vertical":
                rel_y = mouse_pos[1] - self.y
                t = min(max(rel_y / (self.rect.height - self.knob_img.get_height()), 0), 1)
            else:  # horizontal
                rel_x = mouse_pos[0] - self.x
                t = min(max(rel_x / (self.rect.width - self.knob_img.get_width()), 0), 1)
            new_val = int(self.min_val + t * (self.max_val - self.min_val))
            if new_val != self.val:
                self.val = new_val
                return True
        return False

class BorderManager:
    """Gestionnaire des bordures découpées depuis l'asset allborder.png avec support 9-slicing"""
    
    def __init__(self, border_asset_path="assets/ui/allborder.png", session=None):
        self.border_asset_path = border_asset_path
        self.borders = []
        self.current_border_index = 0
        self.border_width = 64  # 640 / 10
        self.border_height = 64  # 512 / 8
        self.session = session  # Référence à la session pour save/load
        
        # Configuration 9-slicing (taille des coins et bords)
        self.corner_size = 16  # Taille des coins (non étirés)
        self.border_thickness = 8  # Épaisseur des bords étirables
        
        self.load_borders()
        self.load_border_index_from_session()
        
    def load_borders(self):
        """Découpe l'asset en 80 bordures individuelles"""
        try:
            if os.path.exists(self.border_asset_path):
                border_sheet = pygame.image.load(self.border_asset_path).convert_alpha()
                print(f"[BORDER] Asset chargé: {self.border_asset_path}")
                
                # Découper en 10x8 = 80 bordures
                for row in range(8):
                    for col in range(10):
                        x = col * self.border_width
                        y = row * self.border_height
                        rect = pygame.Rect(x, y, self.border_width, self.border_height)
                        border_frame = border_sheet.subsurface(rect).copy()
                        
                        # Découper chaque bordure en 9 zones pour le 9-slicing
                        nine_slice_data = self._create_nine_slice(border_frame)
                        self.borders.append(nine_slice_data)
                        
                print(f"[BORDER] {len(self.borders)} bordures découpées avec 9-slicing")
            else:
                print(f"[BORDER] Asset non trouvé: {self.border_asset_path}")
                self.create_fallback_border()
                
        except pygame.error as e:
            print(f"[BORDER] Erreur chargement: {e}")
            self.create_fallback_border()
            
    def _create_nine_slice(self, border_surface):
        """
        Découpe une bordure 64x64 en 9 zones pour le 9-slicing
        
        Returns:
            dict: Dictionnaire contenant les 9 zones découpées
        """
        w, h = border_surface.get_size()
        corner = self.corner_size
        
        # Définir les zones de découpe
        zones = {
            # Coins (non étirés)
            'top_left':     (0, 0, corner, corner),
            'top_right':    (w - corner, 0, corner, corner),
            'bottom_left':  (0, h - corner, corner, corner),
            'bottom_right': (w - corner, h - corner, corner, corner),
            
            # Bords (étirés dans une direction)
            'top':          (corner, 0, w - 2*corner, corner),
            'bottom':       (corner, h - corner, w - 2*corner, corner),
            'left':         (0, corner, corner, h - 2*corner),
            'right':        (w - corner, corner, corner, h - 2*corner),
            
            # Centre (étiré dans les deux directions)
            'center':       (corner, corner, w - 2*corner, h - 2*corner)
        }
        
        # Découper les zones
        nine_slice = {}
        for zone_name, (x, y, width, height) in zones.items():
            if width > 0 and height > 0:
                zone_rect = pygame.Rect(x, y, width, height)
                nine_slice[zone_name] = border_surface.subsurface(zone_rect).copy()
            else:
                # Créer une surface vide si la zone est trop petite
                nine_slice[zone_name] = pygame.Surface((1, 1))
                
        return nine_slice
    
    def create_fallback_border(self):
        """Crée une bordure de substitution si l'asset n'est pas trouvé"""
        fallback = pygame.Surface((self.border_width, self.border_height))
        fallback.fill((100, 100, 150))
        pygame.draw.rect(fallback, (150, 150, 200), fallback.get_rect(), 3)
        self.borders = [self._create_nine_slice(fallback)]
        
    def get_current_border(self):
        """Retourne la bordure actuellement sélectionnée (données 9-slice)"""
        if not self.borders:
            return None
        return self.borders[self.current_border_index % len(self.borders)]
        
    def next_border(self):
        """Passe à la bordure suivante"""
        if not self.borders:
            return
        self.current_border_index = (self.current_border_index + 1) % len(self.borders)
        print(f"[BORDER] Bordure changée: {self.current_border_index + 1}/{len(self.borders)}")
        # Sauvegarde automatique de l'index
        self.save_border_index_to_session()
    
    def set_border_index(self, index):
        """Définit l'index de bordure directement"""
        if not self.borders:
            return
        self.current_border_index = max(0, min(index, len(self.borders) - 1))
        print(f"[BORDER] Index de bordure défini: {self.current_border_index + 1}/{len(self.borders)}")
        # Sauvegarde automatique de l'index
        self.save_border_index_to_session()
    
    def load_border_index_from_session(self):
        """Charge l'index de bordure depuis la session"""
        if not self.session:
            print("[BORDER] Aucune session disponible pour charger l'index de bordure")
            return
        
        try:
            # Récupère l'index depuis les données de session
            border_data = self.session.data.get("border", {})
            saved_index = border_data.get("current_index", 0)
            
            if self.borders and 0 <= saved_index < len(self.borders):
                self.current_border_index = saved_index
                print(f"[BORDER] Index de bordure chargé depuis session: {self.current_border_index + 1}/{len(self.borders)}")
            else:
                print(f"[BORDER] Index invalide dans session ({saved_index}), utilisation de l'index 0")
                self.current_border_index = 0
        except Exception as e:
            print(f"[BORDER] Erreur lors du chargement index: {e}")
            self.current_border_index = 0
    
    def save_border_index_to_session(self):
        """Sauvegarde l'index de bordure dans la session"""
        if not self.session:
            print("[BORDER] Aucune session disponible pour sauvegarder l'index de bordure")
            return
        
        try:
            # Assure que la section border existe
            if "border" not in self.session.data:
                self.session.data["border"] = {}
            
            # Sauvegarde l'index actuel
            self.session.data["border"]["current_index"] = self.current_border_index
            self.session.save_data()
            
            print(f"[BORDER] Index de bordure sauvegardé: {self.current_border_index}")
        except Exception as e:
            print(f"[BORDER] Erreur lors de la sauvegarde index: {e}")
            
    def draw_border(self, screen, rect, border_thickness=0):
        """
        Dessine une bordure 9-slice autour d'un rectangle, border_thickness agrandit la zone.
        """
        if border_thickness > 0:
            rect = pygame.Rect(
                rect.x - border_thickness,
                rect.y - border_thickness,
                rect.width + 2 * border_thickness,
                rect.height + 2 * border_thickness
            )
        border_data = self.get_current_border()
        if not border_data:
            return
        corner = self.corner_size
        center_width = max(1, rect.width - 2 * corner)
        center_height = max(1, rect.height - 2 * corner)
        screen.blit(border_data['top_left'], (rect.x, rect.y))
        screen.blit(border_data['top_right'], (rect.x + rect.width - corner, rect.y))
        screen.blit(border_data['bottom_left'], (rect.x, rect.y + rect.height - corner))
        screen.blit(border_data['bottom_right'], (rect.x + rect.width - corner, rect.y + rect.height - corner))
        if center_width > 0:
            screen.blit(pygame.transform.scale(border_data['top'], (center_width, corner)), (rect.x + corner, rect.y))
            screen.blit(pygame.transform.scale(border_data['bottom'], (center_width, corner)), (rect.x + corner, rect.y + rect.height - corner))
        if center_height > 0:
            screen.blit(pygame.transform.scale(border_data['left'], (corner, center_height)), (rect.x, rect.y + corner))
            screen.blit(pygame.transform.scale(border_data['right'], (corner, center_height)), (rect.x + rect.width - corner, rect.y + corner))
        if center_width > 0 and center_height > 0:
            screen.blit(pygame.transform.scale(border_data['center'], (center_width, center_height)), (rect.x + corner, rect.y + corner))