import pygame
import json
import os
from core.settings import TILE_WIDTH, TILE_HEIGHT, LAYER_HEIGHT

class Zone:

    def __init__(self, map_name):
        self.map_name = map_name
        # Gestion spéciale pour le fichier JSON.. qui a deux points
        self.map_path = f"data/map/{map_name}.json"
        self.tile_folder = os.path.join("assets", "tiles")

        # Données de la carte
        self.grid_layers = []    # List[list[list[int]]] - Toutes les couches
        self.z_offsets = []      # List[int] - Offsets Z pour chaque couche
        self.tile_images = []    # List[Surface] - Images des tuiles
        self.spawn_point = (0, 0)
        self.spawn_layer = 0     # Layer de spawn pour éviter les spawn hors grille
        self.grid_width = 0
        self.grid_height = 0
        self._debug_shown = False  # Flag pour limiter les logs de debug
        self._tiles_cache = None  # Cache pour les tuiles valides

        # Points de liaison entre les maps
        self.transition_points = []  # Liste des points de transition vers d'autres maps
        self.npc_spawns = []        # Emplacements des PNJ

    def load(self):
        """Charge la carte et les tuiles, puis calcule un spawn valide."""
        self._load_map()
        self._load_tiles()
        self._calc_spawn()
        self._load_transition_points()
        self._load_npc_spawns()
        self._tiles_cache = None  # Invalide le cache à chaque chargement

    def _load_map(self):
        """Lecture du JSON et découpe en grid_layers + z_offsets."""
        print(f"[ZONE] Tentative de chargement de la map: {self.map_path}")
        try:
            with open(self.map_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.grid_layers = []
            for layer in data["layers"]:
                flat_data = layer["data"]
                width = layer["width"]
                height = layer["height"]

                # Conversion en grille 2D
                grid = []
                for y in range(height):
                    row = []
                    for x in range(width):
                        index = y * width + x
                        tile_id = flat_data[index] if index < len(flat_data) else 0
                        row.append(tile_id)
                    grid.append(row)

                self.grid_layers.append(grid)

            # Taille de la grille
            if self.grid_layers:
                self.grid_width = len(self.grid_layers[0][0])
                self.grid_height = len(self.grid_layers[0])
                print(f"[ZONE] Map chargée avec succès: {self.grid_width}x{self.grid_height}, {len(self.grid_layers)} couches")
            else:
                self.grid_width = 32
                self.grid_height = 32
                print("[ZONE] Aucune couche trouvée, utilisation des dimensions par défaut")

            # Z offsets par couche
            self.z_offsets = [i * -LAYER_HEIGHT for i in range(len(self.grid_layers))]

        except FileNotFoundError:
            print(f"[ZONE] ERREUR: Fichier de map non trouvé: {self.map_path}")
            # Fallback en cas d'erreur
            self.grid_layers = []
            self.z_offsets = []
            self.grid_width = 32
            self.grid_height = 32
        except (json.JSONDecodeError, KeyError) as e:
            print(f"[ZONE] ERREUR lors du chargement: {e}")
            # Fallback en cas d'erreur
            self.grid_layers = []
            self.z_offsets = []
            self.grid_width = 32
            self.grid_height = 32

    def _load_tiles(self):
        """Charge les images de chaque tile et les met à l'échelle."""
        self.tile_images = []
        try:
            if not os.path.isdir(self.tile_folder):
                return
                
            files = sorted(os.listdir(self.tile_folder))
            for filename in files:
                if filename.endswith(".png") and filename.startswith("tile_"):
                    path = os.path.join(self.tile_folder, filename)
                    img = pygame.image.load(path).convert_alpha()
                    img = pygame.transform.scale(img, (TILE_WIDTH, TILE_HEIGHT))
                    self.tile_images.append(img)
            
            # Appliquer l'opacité aux tuiles spécifiées
            self._apply_tile_opacity()
            
        except (FileNotFoundError, OSError) as e:
            print(f"[ZONE] ERREUR lors du chargement des tiles: {e}")
            # Créer des tuiles de debug en cas d'erreur
            for i in range(10):
                surf = pygame.Surface((TILE_WIDTH, TILE_HEIGHT))
                surf.fill((50 + i*20, 100, 50))
                self.tile_images.append(surf)

    def _apply_tile_opacity(self, opacity=217, index_range=(91, 95)):
        """Applique une opacité à certaines tuiles."""
        if not self.tile_images:
            return

        for idx in range(index_range[0], index_range[1] + 1):
            img_idx = idx - 1  # Correction car Tiled commence à 1
            if 0 <= img_idx < len(self.tile_images):
                self.tile_images[img_idx].set_alpha(opacity)

    def _calc_spawn(self):
        """Définit le spawn point dans le système de coordonnées centrées et le valide."""
        spawn_points = {
            "clairiere": (16, 16, 2),      # CORRIGÉ: Retour au layer 2 (layer réel du spawn)
            "loopfanglerecursif": (0, 0, 0),
            "roi": (2, 2, 0),
            "neuill": (-2, -2, 0),
            "JSON.": (0, 0, 0),
            "tyran": (1, 1, 0)
        }

        spawn_data = spawn_points.get(self.map_name, (0, 0, 0))
        if len(spawn_data) == 3:
            self.spawn_point = (spawn_data[0], spawn_data[1])
            self.spawn_layer = spawn_data[2]
        else:
            self.spawn_point = spawn_data
            self.spawn_layer = 0
            
        print(f"[ZONE] Map '{self.map_name}' - Spawn défini: {self.spawn_point}, Layer: {self.spawn_layer}")

    def _has_tile_at(self, x, y):
        """Vérifie si au moins une couche a une tuile à cette position."""
        return any(tile["x"] == x and tile["y"] == y for tile in self.get_all_tiles_with_pos())

    def _load_transition_points(self):
        """Charge les points de transition définis manuellement pour chaque map."""
        # Points de transition ajustés selon la taille réelle de chaque map
        transition_map = {
            "clairiere": [
                {"x": 15, "y": 15, "target_map": "JSON.", "target_spawn": "default"},
                {"x": 17, "y": 25, "target_map": "roi", "target_spawn": "default"},
                {"x": 5, "y": 20, "target_map": "loopfanglerecursif", "target_spawn": "default"}
            ],
            "neuill": [
                {"x": 11, "y": 8, "target_map": "clairiere", "target_spawn": "default"}
            ]
        }

        # Récupérer les transitions pour cette map
        self.transition_points = transition_map.get(self.map_name, [])
        print(f"[ZONE] Map '{self.map_name}' - {len(self.transition_points)} transitions définies")

        

    def _load_npc_spawns(self):
        """Charge les emplacements des PNJ depuis le JSON."""
        self.npc_spawns = []
        try:
            with open(self.map_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if "layers" in data:
                for layer in data["layers"]:
                    if layer.get("type") == "objectgroup" and layer.get("name") == "npcs":
                        for obj in layer.get("objects", []):
                            self.npc_spawns.append({
                                "x": obj.get("x", 0) // TILE_WIDTH,
                                "y": obj.get("y", 0) // TILE_HEIGHT,
                                "npc_type": obj.get("properties", {}).get("npc_type", "default"),
                                "npc_id": obj.get("properties", {}).get("npc_id", f"npc_{len(self.npc_spawns)}")
                            })
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            # En cas d'erreur, pas de PNJ
            pass

    def get_tile_at_layer(self, x, y, layer_idx):
        """Retourne le tile_id à la position sur une couche spécifique."""
        tiles = [t for t in self.get_all_tiles_with_pos() 
                if t["x"] == x and t["y"] == y and t["z"] == layer_idx]
        return tiles[0]["tile_id"] if tiles else 0

    def get_transition_at(self, x, y):
        """Retourne le point de transition à la position donnée, peu importe le layer z."""
        # Vérifier directement dans la liste des points de transition
        for tp in self.transition_points:
            if tp["x"] == x and tp["y"] == y:
                return tp
        return None

    def get_npc_at(self, x, y):
        """Retourne le PNJ à la position donnée."""
        tiles = [t for t in self.get_all_tiles_with_pos() 
                if t["x"] == x and t["y"] == y and "npc" in t]
        return tiles[0]["npc"] if tiles else None

    def get_all_tiles_with_pos(self):
        """Optimisé avec correction du centrage"""
        if self._tiles_cache is not None:
            return self._tiles_cache

        tiles = []
        highest_z = {}

        # Debug pour comprendre le centrage
        print(f"[ZONE.DEBUG] Taille grille: {self.grid_width}x{self.grid_height}")

        # Pour chaque layer, parcourir la grille
        for z, layer in enumerate(self.grid_layers):
            for grid_y, row in enumerate(layer):
                for grid_x, tile_id in enumerate(row):
                    if tile_id > 0:
                        # CORRECTION : Utiliser les coordonnées brutes sans centrage
                        wx = grid_x
                        wy = grid_y
                        
                        key = (wx, wy)
                        if key not in highest_z or z > highest_z[key]:
                            highest_z[key] = z
                        
                        # Ajouter la tuile avec nouvelles coordonnées
                        is_walkable = self._is_walkable_tile(tile_id)
                        tile_info = {
                            "x": wx, "y": wy, "z": z,
                            "tile_id": tile_id,
                            "is_walkable": is_walkable,
                        }
                        tiles.append(tile_info)
        
        self._tiles_cache = tiles
        return tiles
    
    def _is_walkable_tile(self, tile_id):
        """
        Logique permissive : toutes les tuiles sont walkable sauf les obstacles.
        Plus facile à maintenir et permet l'exploration libre.
        """
        # Liste des tuiles NON-walkable (obstacles, eau profonde, murs, etc.)
        non_walkable_tiles = {
            # Ajoutez ici les IDs des tuiles qui bloquent le mouvement
            # Par exemple : 55, 56, 57, 58, 59, 60  # Eau profonde
            # 80, 81, 82, 83, 84, 85  # Murs/rochers
        }
        
        # Toute tuile qui existe (tile_id > 0) et qui n'est pas dans la liste des obstacles
        return tile_id > 0 and tile_id not in non_walkable_tiles

    # === Méthodes d'accès publiques simplifiées ===
    def get_spawn(self):
        """Retourne la position de spawn avec le layer."""
        return self.spawn_point
    
    def get_spawn_layer(self):
        """Retourne le layer de spawn."""
        return self.spawn_layer
    
    def get_tile_images(self):
        """Retourne les images des tuiles."""
        return self.tile_images

