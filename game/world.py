import pygame
import json
import os
from core.settings import TILE_WIDTH, TILE_HEIGHT, grid_to_iso, iso_to_grid

class World:

    LAYER_Z_OFFSET = 16
    def __init__(self, screen=None):
        self.tile_folder = os.path.join("assets", "tiles")
        self.screen = screen or pygame.display.get_surface()
        self.tile_images = []
        # Nouvelle structure centralisée : liste de tuples (entité ou classe, (x, y))
        self.spawn_point = {
            "joueur": (0, 0),
            "DameIndenta": (4, 8),
            "Neuill": (1, 6),
            "JSON": (3, 6),
            "Loopfang": (1, 8),
        }
        self._tiles_cache = None
        self.screen_center_x = 400
        self.screen_center_y = 200
        self.bg_img = None
        self.cloud_imgs = []
        self.cloud_pos = []
        self.cloud_speed = [0.3, -0.2]
        self.load()
        self._init_background()

    def load(self):
        """Charge la map et les tuiles"""
        self._load_tiles()
        self._load_map_from_json()

    def _load_map_from_json(self):
        """Charge la map depuis data/map/clairiere.json ou crée une grille par défaut"""
        map_path = "data/map/clairiere.json"
        try:
            if not os.path.exists(map_path):
                print(f"[WORLD] Fichier map '{map_path}' introuvable, création d'une grille par défaut")
                self._create_default_grid()
                return
            with open(map_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            print(f"[WORLD] Chargement de la map depuis {map_path}")
            tiles = []
            for layer_count, layer in enumerate([l for l in data.get("layers", []) if l.get("type") == "tilelayer"]):
                width, height = layer.get("width", 0), layer.get("height", 0)
                layer_data = layer.get("data", [])
                print(f"[WORLD] Layer {layer_count}: {width}x{height}, {len(layer_data)} tuiles")
                for y in range(height):
                    for x in range(width):
                        idx = y * width + x
                        if idx < len(layer_data):
                            tile_id = layer_data[idx]
                            if tile_id > 0:
                                world_x = x - (width // 2) + self.spawn_point["joueur"][0]
                                world_y = y - (height // 2) + self.spawn_point["joueur"][1]
                                tiles.append({
                                    "x": world_x,
                                    "y": world_y,
                                    "z": layer_count,
                                    "tile_id": tile_id,
                                    "is_walkable": self._is_walkable_tile(tile_id)
                                })
            self._tiles_cache = tiles
            print(f"[WORLD] Map 'clairiere' chargée: {len(tiles)} tuiles, {layer_count+1} layers")
        except Exception as e:
            print(f"[WORLD] Erreur chargement map clairiere: {e}")
            self._create_default_grid()

    def _load_tiles(self):
        """Charge les images de tuiles depuis assets/tiles/"""
        self.tile_images = []
        try:
            if not os.path.isdir(self.tile_folder):
                print(f"[WORLD] Dossier tuiles '{self.tile_folder}' introuvable")
                self._create_default_tiles()
                return
            tile_files = [f for f in sorted(os.listdir(self.tile_folder)) if f.endswith(".png") and f.startswith("tile_")]
            if not tile_files:
                print("[WORLD] Aucune tuile trouvée dans assets/tiles/")
                self._create_default_tiles()
                return
            for filename in tile_files:
                path = os.path.join(self.tile_folder, filename)
                img = pygame.image.load(path).convert_alpha()
                img = pygame.transform.scale(img, (TILE_WIDTH, TILE_HEIGHT))
                self.tile_images.append(img)
            print(f"[WORLD] {len(self.tile_images)} tuiles chargées depuis {self.tile_folder}")
        except Exception as e:
            print(f"[WORLD] Erreur chargement tuiles: {e}")
            self._create_default_tiles()

    def _is_walkable_tile(self, tile_id):
        """Détermine si une tuile est walkable"""
        return tile_id > 0 and tile_id not in {91, 92, 93, 94, 95, 101, 102, 103, 104}

    def _init_background(self):
        """Initialise l'arrière-plan avec nuages"""
        try:
            self.bg_img = pygame.image.load("assets/cloud/1.png").convert()
            screen_size = self.screen.get_size()
            self.bg_img = pygame.transform.scale(self.bg_img, screen_size)
            self.cloud_imgs = [pygame.image.load(f"assets/cloud/{i}.png").convert_alpha() for i in (2, 3)]
            self.cloud_pos = [
                [-self.cloud_imgs[0].get_width(), screen_size[1] - self.cloud_imgs[0].get_height() - 50],
                [screen_size[0], screen_size[1] - self.cloud_imgs[1].get_height() - 120]
            ]
        except Exception:
            print("[WORLD] Impossible de charger les images de nuages")
            screen_size = self.screen.get_size() if self.screen else (800, 600)
            self.bg_img = pygame.Surface(screen_size)
            self.bg_img.fill((135, 206, 235))
            self.cloud_imgs = []
            self.cloud_pos = []

    def update_background(self, screen):
        """Met à jour l'arrière-plan animé"""
        if self.bg_img:
            screen.blit(self.bg_img, (0, 0))
        
        if self.cloud_imgs:
            screen_width = screen.get_width()
            for i, cloud in enumerate(self.cloud_imgs):
                self.cloud_pos[i][0] += self.cloud_speed[i]
                if self.cloud_speed[i] > 0:
                    if self.cloud_pos[i][0] > screen_width:
                        self.cloud_pos[i][0] = -cloud.get_width()
                else:
                    if self.cloud_pos[i][0] < -cloud.get_width():
                        self.cloud_pos[i][0] = screen_width
                screen.blit(cloud, (int(self.cloud_pos[i][0]), int(self.cloud_pos[i][1])))

    def get_grid_position(self, entity):
        """MÉTHODE UNIFIÉE : Position entière standardisée pour toutes les entités"""
        if hasattr(entity, 'tile_pos'):
            return (int(round(entity.tile_pos[0])), int(round(entity.tile_pos[1])))
        return (0, 0)
    
    def tile_to_pixel(self, tile_x, tile_y):
        """Convertit coordonnées tuile vers pixel isométrique"""
        iso_x, iso_y = grid_to_iso(tile_x, tile_y, TILE_WIDTH, TILE_HEIGHT)
        return iso_x + self.screen_center_x, iso_y + self.screen_center_y
    
    def pixel_to_tile(self, pixel_x, pixel_y):
        """Convertit pixel vers coordonnées tuile"""
        iso_x = pixel_x - self.screen_center_x
        iso_y = pixel_y - self.screen_center_y
        return iso_to_grid(iso_x, iso_y, TILE_WIDTH, TILE_HEIGHT)

    def draw(self, screen, camera_offset=(0, 0)):
        """Dessine le monde complet"""
        self.update_background(screen)
        
        all_tiles = self.get_all_tiles_with_pos()
        if not all_tiles:
            return
            
        if not self.tile_images:
            return
        
        # Calculer la tuile sous la souris
        mouse_x, mouse_y = pygame.mouse.get_pos()
        world_mouse_x = mouse_x - camera_offset[0]
        world_mouse_y = mouse_y - camera_offset[1]
        hovered_tile_x, hovered_tile_y = self.pixel_to_tile(world_mouse_x, world_mouse_y)
        
        # Trier les tuiles pour un rendu correct (layer par layer)
        sorted_tiles = sorted(all_tiles, key=lambda t: (t["z"], t["y"], t["x"]))

        # Rendu des tuiles avec offset z
        for tile in sorted_tiles:
            tile_id = tile["tile_id"]
            x, y, z = tile["x"], tile["y"], tile["z"]

            # Image de la tuile
            tile_img_idx = tile_id - 1
            if 0 <= tile_img_idx < len(self.tile_images):
                tile_img = self.tile_images[tile_img_idx]
            else:
                tile_img = pygame.Surface((TILE_WIDTH, TILE_HEIGHT))
                tile_img.fill((100, 200, 100))

            # Position d'affichage avec offset z
            screen_x, screen_y = self.tile_to_pixel(x, y)
            screen_x += camera_offset[0]
            screen_y += camera_offset[1] - z * self.LAYER_Z_OFFSET

            # Highlight de la tuile sous la souris
            if x == hovered_tile_x and y == hovered_tile_y:
                screen_y -= 8
                highlight_surface = pygame.Surface((TILE_WIDTH, TILE_HEIGHT))
                highlight_surface.set_alpha(100)
                highlight_surface.fill((255, 255, 0))
                screen.blit(highlight_surface, (screen_x, screen_y))

            screen.blit(tile_img, (screen_x, screen_y))

    def get_all_tiles_with_pos(self):
        """Retourne toutes les tuiles avec leurs positions"""
        if self._tiles_cache is None:
            self._load_map_from_json()
        return self._tiles_cache

    def get_tiles_at_position(self, x, y):
        """Retourne les tuiles à la position donnée"""
        grid_x, grid_y = round(x), round(y)
        return [t for t in self.get_all_tiles_with_pos() 
                if t["x"] == grid_x and t["y"] == grid_y]

    def get_spawn_position(self, entity_name="joueur"):
        pos = self.spawn_point.get(entity_name)
        if pos and self.is_valid_tile_position(pos[0], pos[1]):
            return pos
        raise ValueError(f"Spawn point not found for entity: {entity_name}")

    def get_spawn_layer(self):
        """Retourne le layer de spawn (toujours 0 maintenant)"""
        return 2

    def get_tile_images(self):
        """Retourne les images de tuiles"""
        return self.tile_images
    
    def is_valid_tile_position(self, x, y):
        """Vérifie qu'une position correspond à une tuile valide dans le cache"""
        return any(t["x"] == x and t["y"] == y for t in self.get_all_tiles_with_pos())
    
    # === MÉTHODES UNIFIÉES POUR LES ENTITÉS ===
    
    def get_entity_pixel_pos(self, tile_x, tile_y, camera_offset=(0, 0)):
        """UNIQUE MÉTHODE de conversion tuile→pixel pour TOUTES les entités"""
        pixel_x, pixel_y = self.tile_to_pixel(tile_x, tile_y)
        return pixel_x + camera_offset[0], pixel_y + camera_offset[1]
    
    def sync_combat_positions(self, entities):
        """Synchronise les positions de combat avec les positions monde pour toutes les entités"""
        for entity in entities:
            if hasattr(entity, 'tile_pos') and hasattr(entity, 'combat_tile_x'):
                grid_x, grid_y = self.get_grid_position(entity)
                entity.combat_tile_x = grid_x
                entity.combat_tile_y = grid_y
                print(f"[WORLD] Sync combat: {getattr(entity, 'name', 'Entity')} -> combat({entity.combat_tile_x}, {entity.combat_tile_y})")
    
    def validate_entity_positions(self, entities):
        """DEBUG : Valide et affiche les positions de toutes les entités"""
        print("[WORLD] === VALIDATION DES POSITIONS ===")
        for entity in entities:
            name = getattr(entity, 'name', 'Unknown')
            
            if hasattr(entity, 'tile_pos'):
                # Position grille standardisée
                grid_x, grid_y = self.get_grid_position(entity)
                # Position pixel calculée
                pixel_x, pixel_y = self.get_entity_pixel_pos(entity.tile_pos[0], entity.tile_pos[1])
                # Position combat
                combat_pos = f"combat({getattr(entity, 'combat_tile_x', '?')}, {getattr(entity, 'combat_tile_y', '?')})"
                
                print(f"[WORLD] {name}: tile_pos({entity.tile_pos[0]:.2f}, {entity.tile_pos[1]:.2f}) | grid({grid_x}, {grid_y}) | {combat_pos} | pixel({pixel_x:.1f}, {pixel_y:.1f})")
            else:
                print(f"[WORLD] {name}: NO tile_pos!")
        print("[WORLD] === FIN VALIDATION ===")
        
    # === MÉTHODES MANQUANTES (fallback) ===
    
    def _create_default_grid(self):
        """Crée une grille par défaut si aucune map n'est trouvée"""
        print("[WORLD] Création d'une grille par défaut 10x10")
        tiles = []
        for y in range(-5, 5):
            for x in range(-5, 5):
                tiles.append({
                    "x": x, "y": y, "z": 0,
                    "tile_id": 1, "is_walkable": True
                })
        self._tiles_cache = tiles
    
    def _create_default_tiles(self):
        """Crée des tuiles par défaut si aucune image n'est trouvée"""
        print("[WORLD] Création de tuiles par défaut")
        default_tile = pygame.Surface((TILE_WIDTH, TILE_HEIGHT))
        default_tile.fill((100, 200, 100))  # Vert
        self.tile_images = [default_tile]
