import pygame
from core.settings import TILE_WIDTH, TILE_HEIGHT, LAYER_HEIGHT, grid_to_iso, iso_to_grid
from game.zone import Zone


class WorldManager:
    """
    Orchestration du monde et gestion d'input specifique a la zone.
    Responsabilite : Rendu, interactions, logique de jeu.
    """

    def __init__(self, map_name="clairiere", screen=None):
        # Délégation du chargement de carte à Zone
        self.zone = Zone(map_name)
        self.zone.load()
        self.current_zone = self.zone  # Référence pour l'affichage
        
        self.screen = screen
        
        # Initialisation du fond et des nuages
        self._init_background()

    def _init_background(self):
        """Initialise le fond et les nuages animés"""
        if not self.screen:
            # Si pas d'écran fourni, utiliser l'écran par défaut
            self.screen = pygame.display.get_surface()
        
        # Charger et redimensionner le fond à la taille de l'écran
        self.bg_img = pygame.image.load("assets/cloud/1.png").convert()
        screen_size = self.screen.get_size()
        self.bg_img = pygame.transform.scale(self.bg_img, screen_size)
        
        # Charger les nuages avec transparence
        self.cloud_imgs = []
        for i in (2, 3):
            cloud = pygame.image.load(f"assets/cloud/{i}.png").convert_alpha()
            self.cloud_imgs.append(cloud)
        
        # Positions initiales sur les bords (gauche et droite)
        self.cloud_pos = [
            [-self.cloud_imgs[0].get_width(), screen_size[1] - self.cloud_imgs[0].get_height() - 50],
            [screen_size[0], screen_size[1] - self.cloud_imgs[1].get_height() - 120]
        ]
        
        # Vitesses différentes pour chaque nuage
        self.cloud_speed = [0.3, -0.2]  # px/frame

    def change_zone(self, new_map_name):
        """Change vers une nouvelle zone."""
        self._tiles_cache = None 
        self.zone = Zone(new_map_name)
        self.zone.load()
        # Mise à jour de la référence dans current_zone pour l'affichage
        self.current_zone = self.zone

    def check_transition(self, x, y):
        """Vérifie s'il y a une transition à la position donnée, peu importe le layer z."""
        transition = self.zone.get_transition_at(x, y)
        if transition:
            print(f"[WORLD_MGR] Transition trouvée à ({x}, {y}) vers {transition['target_map']}")
        return transition

    def update_background(self, screen):
        """Dessine le fond et anime les nuages sur la scène"""
        screen_width = screen.get_width()
        
        # 1. Dessiner le fond
        screen.blit(self.bg_img, (0, 0))
        
        # 2. Animer et dessiner les nuages
        for i, cloud in enumerate(self.cloud_imgs):
            # Mise à jour position
            self.cloud_pos[i][0] += self.cloud_speed[i]
            
            # Faire boucler les nuages quand ils sortent de l'écran
            if self.cloud_speed[i] > 0:  # Déplacement vers la droite
                if self.cloud_pos[i][0] > screen_width:
                    self.cloud_pos[i][0] = -cloud.get_width()
            else:  # Déplacement vers la gauche
                if self.cloud_pos[i][0] < -cloud.get_width():
                    self.cloud_pos[i][0] = screen_width
            
            # Dessiner le nuage (conversion en int pour éviter les avertissements)
            screen.blit(cloud, (int(self.cloud_pos[i][0]), int(self.cloud_pos[i][1])))

    def draw(self, screen, camera_offset=(0, 0)):
        """
        Dessine le monde complet avec toutes les couches
        CORRIGÉ : Rendu simplifié et efficace sans cases vides
        """
        # Dessiner d'abord le fond et les nuages
        self.update_background(screen)
        
        # Utiliser la nouvelle méthode optimisée pour récupérer SEULEMENT les tuiles valides
        all_tiles = self.zone.get_all_tiles_with_pos()
        if not all_tiles:
            print("[WORLD_MGR] Aucune tuile valide à dessiner!")
            return
        
        tile_images = self.zone.get_tile_images()
        if not tile_images:
            print("[WORLD_MGR] Aucune image de tuile chargée!")
            return
        
        # Calculer l'offset de centrage corrigé
        grid_width = self.zone.grid_width
        center_offset_x = (grid_width * TILE_WIDTH) // 4
        
        # Trier les tuiles par couche pour un rendu correct (couches inférieures en premier)
        all_tiles.sort(key=lambda tile: tile["z"])
        
        # Dessiner toutes les tuiles valides (plus de filtre ici car zone.py ne retourne que les valides)
        tiles_drawn = 0
        for tile in all_tiles:
            tile_id = tile["tile_id"]
            x, y, layer_index = tile["x"], tile["y"], tile["z"]
            
            # Récupérer l'image de la tuile (gestion sécurisée d'index)
            tile_img_idx = tile_id - 1  # Correction d'index (Tiled commence à 1)
            if 0 <= tile_img_idx < len(tile_images):
                tile_img = tile_images[tile_img_idx]
            else:
                # Tuile de debug pour indices invalides
                tile_img = pygame.Surface((TILE_WIDTH, TILE_HEIGHT))
                tile_img.fill((255, 0, 255))  # Magenta pour debug
                print(f"[WORLD_MGR] Tuile ID {tile_id} invalide (index {tile_img_idx})")
            
            # Calculer la position à l'écran avec centrage corrigé
            iso_x, iso_y = grid_to_iso(x, y, TILE_WIDTH, TILE_HEIGHT)
            screen_x = iso_x + center_offset_x + camera_offset[0]
            screen_y = iso_y + camera_offset[1] - (LAYER_HEIGHT * layer_index)
            
            # Dessiner la tuile
            screen.blit(tile_img, (screen_x, screen_y))
            tiles_drawn += 1
        
        # Debug occasionnel pour vérifier le rendu
        if hasattr(self, '_render_debug_counter'):
            self._render_debug_counter += 1
        else:
            self._render_debug_counter = 1
            print(f"[WORLD_MGR] Premier rendu: {tiles_drawn} tuiles dessinées")

    # === Méthodes de collision et navigation ===

    def can_move(self, from_x, from_y, to_x, to_y, current_layer=None):
        """Validation de mouvement unifiée et permissive"""
        # Debug stratégique : limiter les logs pour éviter le spam
        if not hasattr(self, '_debug_movement_counter'):
            self._debug_movement_counter = 0
        self._debug_movement_counter += 1
        
        # Trouver toutes les tuiles walkable à destination
        walkable_tiles = [t for t in self.zone.get_all_tiles_with_pos() 
                         if t["x"] == to_x and t["y"] == to_y and t["is_walkable"]]
        
        # Debug occasionnel pour comprendre le blocage
        if self._debug_movement_counter % 20 == 0:  # Log tous les 20 appels
            all_tiles_at_pos = [t for t in self.zone.get_all_tiles_with_pos() if t["x"] == to_x and t["y"] == to_y]
            print(f"[DEBUG] Mouvement vers ({to_x}, {to_y}):")
            print(f"  - Tuiles présentes: {len(all_tiles_at_pos)}")
            for t in all_tiles_at_pos:
                print(f"    * Z{t['z']} ID:{t['tile_id']} Walkable:{t['is_walkable']}")
            print(f"  - Tuiles walkable: {len(walkable_tiles)}")
        
        # Aucune tuile walkable = mouvement impossible
        if not walkable_tiles:
            return {"can_move": False, "target_layer": None, "reason": "aucune_tuile_walkable"}
        
        # Trouver le layer walkable optimal
        if current_layer is not None:
            # Préférer rester au même layer ou descendre/monter légèrement
            same_layer_tiles = [t for t in walkable_tiles if t["z"] == current_layer]
            if same_layer_tiles:
                return {"can_move": True, "target_layer": current_layer, "reason": "same_layer"}
            
            # Descendre est toujours possible
            lower_layer_tiles = [t for t in walkable_tiles if t["z"] < current_layer]
            if lower_layer_tiles:
                target_layer = max(t["z"] for t in lower_layer_tiles)
                return {"can_move": True, "target_layer": target_layer, "reason": "descend"}
            
            # Monter est limité à +1 layer
            higher_layer_tiles = [t for t in walkable_tiles if t["z"] > current_layer]
            if higher_layer_tiles and min(t["z"] for t in higher_layer_tiles) - current_layer <= 1:
                target_layer = min(t["z"] for t in higher_layer_tiles)
                return {"can_move": True, "target_layer": target_layer, "reason": "ascend"}
                
            return {"can_move": False, "target_layer": None, "reason": "hauteur_invalide"}
        
        # Sans layer courant, utiliser le plus haut walkable
        target_layer = max(t["z"] for t in walkable_tiles)
        return {"can_move": True, "target_layer": target_layer, "reason": "ok"}
    
    def tile_to_pixel(self, tile_x, tile_y):
        """Conversion tuile vers pixel centralisee, utilise settings.py"""
        # Utiliser la fonction de reference de settings.py
        iso_x, iso_y = grid_to_iso(tile_x, tile_y, TILE_WIDTH, TILE_HEIGHT)
        
        # Appliquer le MEME centrage que dans draw()
        center_offset_x = (self.zone.grid_width * TILE_WIDTH) // 4
        
        return iso_x + center_offset_x, iso_y
    
    def pixel_to_tile(self, pixel_x, pixel_y):
        """Conversion pixel vers tuile centralisee, utilise settings.py"""
        # Soustraire le centrage avant conversion
        center_offset_x = (self.zone.grid_width * TILE_WIDTH) // 4
        
        # Utiliser la fonction de reference de settings.py
        return iso_to_grid(pixel_x - center_offset_x, pixel_y, TILE_WIDTH, TILE_HEIGHT)

    # ...existing code...
    
    def get_spawn_position(self):
        """Retourne la position de spawn."""
        return self.zone.get_spawn()
    
    def get_spawn_layer(self):
        """Retourne le layer de spawn."""
        return self.zone.get_spawn_layer()
    
    def get_fall_destination(self):
        """Retourne une destination après chute (pour compatibility)."""
        return "clairiere"  # Fallback vers la clairière
    
    # === Méthode d'analyse de zone (pour IA et navigation) ===
    def debug_tile_at(self, x, y):
        """Affiche les infos détaillées sur la tuile à la position donnée"""
        all_tiles = [t for t in self.zone.get_all_tiles_with_pos() if t["x"] == x and t["y"] == y]
        print(f"[DEBUG] Tuiles à ({x},{y}):")
        if all_tiles:
            for t in all_tiles:
                print(f"  - Z{t['z']} ID:{t['tile_id']} Walkable:{t['is_walkable']}")
        else:
            print("  - Aucune tuile trouvée")
        return all_tiles