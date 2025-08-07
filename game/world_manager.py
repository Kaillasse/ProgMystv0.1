import pygame
from core.settings import TILE_WIDTH, TILE_HEIGHT, LAYER_HEIGHT, grid_to_iso, iso_to_grid
from game.zone import Zone


class WorldManager:
    """
    Gestionnaire du monde isométrique simplifié.
    Logique uniquement basée sur les coordonnées de tuiles.
    """
    def __init__(self, map_name="clairiere", screen=None):
        self.zone = Zone(map_name)
        self.zone.load()
        self.current_zone = self.zone
        self.screen = screen
        # Paramètres de centrage du rendu
        self.screen_center_x = 400
        self.screen_center_y = 200
        self._init_background()

    def _init_background(self):
        if not self.screen:
            self.screen = pygame.display.get_surface()
        self.bg_img = pygame.image.load("assets/cloud/1.png").convert()
        screen_size = self.screen.get_size()
        self.bg_img = pygame.transform.scale(self.bg_img, screen_size)
        self.cloud_imgs = [pygame.image.load(f"assets/cloud/{i}.png").convert_alpha() for i in (2, 3)]
        self.cloud_pos = [
            [-self.cloud_imgs[0].get_width(), screen_size[1] - self.cloud_imgs[0].get_height() - 50],
            [screen_size[0], screen_size[1] - self.cloud_imgs[1].get_height() - 120]
        ]
        self.cloud_speed = [0.3, -0.2]

    def change_zone(self, new_map_name):
        self.zone = Zone(new_map_name)
        self.zone.load()
        self.current_zone = self.zone

    def check_transition(self, x, y):
        """Vérifie les transitions (coordonnées entières uniquement)"""
        return self.zone.get_transition_at(x, y)

    def update_background(self, screen):
        screen_width = screen.get_width()
        screen.blit(self.bg_img, (0, 0))
        for i, cloud in enumerate(self.cloud_imgs):
            self.cloud_pos[i][0] += self.cloud_speed[i]
            if self.cloud_speed[i] > 0:
                if self.cloud_pos[i][0] > screen_width:
                    self.cloud_pos[i][0] = -cloud.get_width()
            else:
                if self.cloud_pos[i][0] < -cloud.get_width():
                    self.cloud_pos[i][0] = screen_width
            screen.blit(cloud, (int(self.cloud_pos[i][0]), int(self.cloud_pos[i][1])))

    # === CONVERSION TUILE→PIXEL (rendu uniquement) ===
    
    def tile_to_pixel(self, tile_x, tile_y):
        """Convertit coordonnées tuile vers pixel pour le RENDU uniquement"""
        iso_x, iso_y = grid_to_iso(tile_x, tile_y, TILE_WIDTH, TILE_HEIGHT)
        screen_x = iso_x + self.screen_center_x
        screen_y = iso_y + self.screen_center_y
        return screen_x, screen_y
    
    def pixel_to_tile(self, pixel_x, pixel_y):
        """Conversion pixel→tuile (debug/souris uniquement, JAMAIS pour la logique)"""
        iso_x = pixel_x - self.screen_center_x
        iso_y = pixel_y - self.screen_center_y
        return iso_to_grid(iso_x, iso_y, TILE_WIDTH, TILE_HEIGHT)

    # === RENDU ===
    
    def draw(self, screen, camera_offset=(0, 0)):
        self.update_background(screen)
        all_tiles = self.zone.get_all_tiles_with_pos()
        if not all_tiles:
            return
        tile_images = self.zone.get_tile_images()
        if not tile_images:
            return
        
        # Calculer la tuile sous la souris (debug uniquement)
        mouse_x, mouse_y = pygame.mouse.get_pos()
        world_mouse_x = mouse_x - camera_offset[0]
        world_mouse_y = mouse_y - camera_offset[1]
        hovered_tile_x, hovered_tile_y = self.pixel_to_tile(world_mouse_x, world_mouse_y)
        
        # Filtrer et trier les tuiles visibles
        visible_tiles = [tile for tile in all_tiles if tile["tile_id"] > 0]
        visible_tiles.sort(key=lambda tile: (tile["y"], tile["x"], tile["z"]))
        
        # Rendu des tuiles
        for tile in visible_tiles:
            tile_id = tile["tile_id"]
            x, y, layer_index = tile["x"], tile["y"], tile["z"]
            
            # Image de la tuile
            tile_img_idx = tile_id - 1
            if 0 <= tile_img_idx < len(tile_images):
                tile_img = tile_images[tile_img_idx]
            else:
                tile_img = pygame.Surface((TILE_WIDTH, TILE_HEIGHT))
                tile_img.fill((255, 0, 255))
            
            # Position d'affichage (conversion tuile→pixel)
            screen_x, screen_y = self.tile_to_pixel(x, y)
            screen_x += camera_offset[0]
            screen_y += camera_offset[1] - (LAYER_HEIGHT * layer_index)
            
            # Highlight de la tuile sous la souris
            if x == hovered_tile_x and y == hovered_tile_y:
                screen_y -= 8
                highlight_surface = pygame.Surface((TILE_WIDTH, TILE_HEIGHT))
                highlight_surface.set_alpha(100)
                highlight_surface.fill((255, 255, 0))
                screen.blit(highlight_surface, (screen_x, screen_y))
            
            screen.blit(tile_img, (screen_x, screen_y))
        
        # Debug
        self._draw_debug(screen, hovered_tile_x, hovered_tile_y)

    def _draw_debug(self, screen, tile_x, tile_y):
        """Debug simple pour vérifier la logique"""
        font = pygame.font.SysFont("Arial", 12, bold=True)
        
        # Position souris
        mouse_text = f"Souris -> Tuile({tile_x}, {tile_y})"
        screen.blit(font.render(mouse_text, True, (0, 255, 255)), (10, 70))
        
        # Tuiles à cette position
        tiles_here = [t for t in self.zone.get_all_tiles_with_pos() 
                     if t["x"] == tile_x and t["y"] == tile_y]
        
        walkable_tiles = [t for t in tiles_here if t["is_walkable"]]
        
        if walkable_tiles:
            # Afficher le layer le plus haut disponible
            highest_layer = max(t["z"] for t in walkable_tiles)
            layers_text = f"Layers walkable: {sorted([t['z'] for t in walkable_tiles])} -> Plus haut: L{highest_layer}"
            screen.blit(font.render(layers_text, True, (0, 255, 0)), (10, 85))

    # === COLLISION INTELLIGENTE (layer le plus haut) ===
    
    def can_move(self, from_x, from_y, to_x, to_y, current_layer=None):
        # Recherche toutes les tuiles à la position cible
        target_tiles = [t for t in self.zone.get_all_tiles_with_pos()
                        if t["x"] == to_x and t["y"] == to_y]
        if not target_tiles:
            # Permissif : autorise le mouvement si la distance flottante < 0.2 tuile
            if abs(to_x - from_x) < 0.2 and abs(to_y - from_y) < 0.2:
                return {"can_move": True, "target_layer": current_layer, "reason": "permissive_edge"}
            return {"can_move": False, "target_layer": None, "reason": "no_tile"}
        # Sinon, logique normale
        highest_layer = max(t["z"] for t in target_tiles)
        return {"can_move": True, "target_layer": highest_layer, "reason": "normal"}

    # === ACCESSEURS ===
    
    def get_spawn_position(self):
        return self.zone.get_spawn()

    def get_spawn_layer(self):
        return self.zone.get_spawn_layer()

    def get_fall_destination(self):
        return "clairiere"
