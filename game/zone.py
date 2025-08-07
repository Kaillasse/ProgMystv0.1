import pygame
import json
import os
from core.settings import TILE_WIDTH, TILE_HEIGHT, LAYER_HEIGHT

class Zone:
    def __init__(self, map_name):
        self.map_name = map_name
        self.map_path = f"data/map/{map_name}.json"
        self.tile_folder = os.path.join("assets", "tiles")
        self.grid_layers, self.tile_images = [], []
        self.spawn_point, self.spawn_layer = (0, 0), 0
        self.grid_width, self.grid_height = 0, 0
        self._tiles_cache = None
        self.transition_points, self.npc_spawns = [], []

    def load(self):
        """Charge la carte et les tuiles"""
        self._load_map_and_build_grid()  # Fonction unifiée de chargement et génération de grille
        self._load_tiles()
        self._load_transition_points()
        self._load_npc_spawns()
    
    def _load_map_and_build_grid(self):
        """Charge la carte et génère immédiatement la grille de tuiles avec positions monde"""
        try:
            with open(self.map_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # 1. Extraire les dimensions et layers brutes
            raw_layers = []
            for layer in data["layers"]:
                if layer.get("type") != "tilelayer":
                    continue
                width, height = layer["width"], layer["height"]
                layer_data = [
                    [layer["data"][y * width + x] if y * width + x < len(layer["data"]) else 0
                     for x in range(width)]
                    for y in range(height)
                ]
                raw_layers.append(layer_data)
            
            # Calculer les dimensions de la grille
            self.grid_width = width if 'width' in locals() else 33
            self.grid_height = height if 'height' in locals() else 33
            self.grid_layers = raw_layers
            
            # 2. Calculer le spawn dès maintenant
            self._calc_spawn()
            
            # 3. Construire immédiatement la grille avec positions monde
            self._build_world_grid()
            
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            print(f"[ZONE] Erreur chargement map {self.map_name}: {e}")
            self.grid_layers = []
            self.grid_width, self.grid_height = 33, 33
            self._tiles_cache = []
            self._calc_spawn()
    def _build_world_grid(self):
        """Construit la grille SANS centrage, coordonnées de grille brute (0,0 en haut à gauche)"""
        tiles = []
        for z, layer in enumerate(self.grid_layers):
            for grid_y, row in enumerate(layer):
                for grid_x, tile_id in enumerate(row):
                    tile_info = {
                        "x": grid_x,  # plus de centrage
                        "y": grid_y,
                        "z": z,
                        "tile_id": tile_id,
                        "is_walkable": self._is_walkable_tile(tile_id),
                        "grid_x": grid_x,
                        "grid_y": grid_y
                    }
                    tiles.append(tile_info)
        self._tiles_cache = tiles# Calculer un spawn par défaut
    
    def get_all_tiles_with_pos(self):
        """Retourne la liste des tuiles avec positions monde (déjà calculée au chargement)"""
        if self._tiles_cache is None:
            # Si par extraordinaire le cache est None, le reconstruire
            self._build_world_grid()
        return self._tiles_cache

    def _load_tiles(self):
        self.tile_images = []
        try:
            if not os.path.isdir(self.tile_folder):
                return
            for filename in sorted(os.listdir(self.tile_folder)):
                if filename.endswith(".png") and filename.startswith("tile_"):
                    path = os.path.join(self.tile_folder, filename)
                    img = pygame.image.load(path).convert_alpha()
                    img = pygame.transform.scale(img, (TILE_WIDTH, TILE_HEIGHT))
                    self.tile_images.append(img)
            self._apply_tile_opacity()
        except (FileNotFoundError, OSError):
            for i in range(10):
                surf = pygame.Surface((TILE_WIDTH, TILE_HEIGHT))
                surf.fill((50 + i*20, 100, 50))
                self.tile_images.append(surf)

    def _apply_tile_opacity(self, opacity=217, index_range=(91, 95)):
        if not self.tile_images:
            return
        for idx in range(index_range[0], index_range[1] + 1):
            img_idx = idx - 1
            if 0 <= img_idx < len(self.tile_images):
                self.tile_images[img_idx].set_alpha(opacity)

    def _calc_spawn(self):
        spawn_points = {
            "clairiere": (-1, 7, 2),
            "loopfanglerecursif": (-3, 9, 2),
            "roi": (20, 10, 2),
            "neuill": (16, 14, 2),
            "JSON.": (20, 14, 2),
            "tyran": (1, 1, 2)
        }
        
        spawn_data = spawn_points.get(self.map_name, (0, 0, 0))
        self.spawn_point = (spawn_data[0], spawn_data[1])
        self.spawn_layer = spawn_data[2]

    def _load_transition_points(self):
        """Transitions en coordonnées monde"""
        transition_map = {
            "clairiere": [
                {"x": 5, "y": 5, "target_map": "JSON.", "target_spawn": "default"},
                {"x": 7, "y": 10, "target_map": "roi", "target_spawn": "default"},
                {"x": -5, "y": 5, "target_map": "loopfanglerecursif", "target_spawn": "default"}
            ],
            "neuill": [
                {"x": 0, "y": 0, "target_map": "clairiere", "target_spawn": "default"}
            ]
        }
        self.transition_points = transition_map.get(self.map_name, [])

    def _load_npc_spawns(self):
        self.npc_spawns = []
        try:
            with open(self.map_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for layer in data.get("layers", []):
                if layer.get("type") == "objectgroup" and layer.get("name") == "npcs":
                    for obj in layer.get("objects", []):
                        self.npc_spawns.append({
                            "x": obj.get("x", 0) // TILE_WIDTH,
                            "y": obj.get("y", 0) // TILE_HEIGHT,
                            "npc_type": obj.get("properties", {}).get("npc_type", "default"),
                            "npc_id": obj.get("properties", {}).get("npc_id", f"npc_{len(self.npc_spawns)}")
                        })
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            pass

    def get_transition_at(self, x, y):
        """Trouve une transition à la position donnée"""
        for tp in self.transition_points:
            if tp["x"] == x and tp["y"] == y:
                return tp
        return None

    def _is_walkable_tile(self, tile_id):
        """Détermine si une tuile est walkable"""
        if tile_id <= 0:
            return False
        # Ici on peut ajouter d'autres tuiles non-walkable
        non_walkable_tiles = set()
        return tile_id not in non_walkable_tiles

    def get_spawn(self):
        return self.spawn_point
    def get_spawn_layer(self):
        return self.spawn_layer

    def get_tile_images(self):
        return self.tile_images
