import os
import pygame

class BorderManager:
    """Gestionnaire des bordures découpées depuis l'asset allborder.png avec support 9-slicing"""
    
    def __init__(self, border_asset_path="assets/ui/allborder.png"):
        self.border_asset_path = border_asset_path
        self.borders = []
        self.current_border_index = 0
        self.border_width = 64  # 640 / 10
        self.border_height = 64  # 512 / 8
        
        # Configuration 9-slicing (taille des coins et bords)
        self.corner_size = 16  # Taille des coins (non étirés)
        self.border_thickness = 8  # Épaisseur des bords étirables
        
        self.load_borders()
        
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