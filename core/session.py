# === core/session.py ===
import json
import os
from game.zone import Zone
from core.settings import grid_to_iso, iso_to_grid, get_player_data_path, get_player_sprite_path

class GameSession:
    def update_tile_pos(self, x, y, z=0, map_name=None):
        """
        Met à jour la position du joueur à partir des coordonnées de tuile (grille).
        Si map_name n'est pas fourni, conserve la map actuelle.
        """
        if map_name is None:
            map_name = self.data.get("current_map", "clairiere")
        self.set_player_position(x, y, z, map_name)
    def get_player_position(self):
        """
        Retourne la position du joueur en grille (x, y, z) et en isométrique (iso_x, iso_y), ainsi que le nom de la map.
        """
        pos = self.data.get("position", [0, 0, 0])
        x, y, z = pos if len(pos) == 3 else (pos[0], pos[1], 0)
        map_name = self.data.get("current_map", "clairiere")
        # Conversion grille → iso
        iso_x, iso_y = grid_to_iso(x, y)
        return {
            "grid": (x, y, z),
            "iso": (iso_x, iso_y),
            "map": map_name
        }

    def get_player_position_full(self):
        """
        Retourne toutes les infos de position utiles (grille, iso, map, raw).
        """
        pos = self.data.get("position", [0, 0, 0])
        x, y, z = pos if len(pos) == 3 else (pos[0], pos[1], 0)
        map_name = self.data.get("current_map", "clairiere")
        iso_x, iso_y = grid_to_iso(x, y)
        grid_from_iso = iso_to_grid(iso_x, iso_y)
        return {
            "grid": (x, y, z),
            "iso": (iso_x, iso_y),
            "map": map_name,
            "raw": pos,
            "grid_from_iso": grid_from_iso
        }

    def set_player_position(self, x, y, z=0, map_name="clairiere"):
        """
        Met à jour la position complète du joueur et sauvegarde.
        """
        self.data["position"] = [x, y, z]
        self.data["current_map"] = map_name
        self.save_data()
        
    def get_progress(self, key, default=None):
        """
        Récupère une valeur de progression pour une clé donnée.
        """
        if "progress" not in self.data:
            self.data["progress"] = {}
        return self.data["progress"].get(key, default)
    
    def set_progress(self, key, value):
        """
        Définit une valeur de progression pour une clé donnée.
        """
        if "progress" not in self.data:
            self.data["progress"] = {}
        self.data["progress"][key] = value
        print(f"[SESSION] Progression sauvegardée: {key} = {value}")
    
    def has_progress(self, key):
        """
        Vérifie si une clé de progression existe et n'est pas None/False.
        """
        if "progress" not in self.data:
            return False
        value = self.data["progress"].get(key)
        return value is not None and value is not False

    def __init__(self, player_name):
        self.name = player_name
        # Correction : charge la map via Zone
        zone = Zone("clairiere")
        zone._load_map_and_build_grid()
        self.map = zone.grid_layers
        if self.map and len(self.map) > 0:
            self.grid = self.map[0]  # Layer sol
        else:
            print(f"[SESSION] Aucune grille de map chargée depuis clairiere")
            self.grid = []
        self.data_path = get_player_data_path(player_name)
        self.sprite_path = get_player_sprite_path(player_name)

        print(f"[SESSION] Initialisation de la session pour {self.name}")

        self.data = {}
        self.load_data()

        # Position initiale sur la tuile id 4 entourée de 15 ou 16
        if "position" not in self.data:
            print("[SESSION] Aucune position dans data, recherche spawn initial")
            self.data["position"] = self.find_special_start_pos()
            print(f"[SESSION] Position spawn définie: {self.data['position']}")
        elif not self.is_valid_position(self.data["position"]):
            print(f"[SESSION] Position invalide {self.data['position']}, recherche nouveau spawn")
            self.data["position"] = self.find_special_start_pos()
            print(f"[SESSION] Nouvelle position spawn: {self.data['position']}")
        else:
            print(f"[SESSION] Position existante valide: {self.data['position']}")
        
        # Assure qu'on a une position Z par défaut
        if len(self.data["position"]) == 2:
            self.data["position"].append(0)
            print(f"[SESSION] Ajout Z=0, position finale: {self.data['position']}")

    def is_valid_position(self, pos):
        if not self.grid or not pos:
            return False
        # Accepte positions 2D [x, y] et 3D [x, y, z]
        if len(pos) >= 2:
            x, y = pos[0], pos[1]
            if 0 <= y < len(self.grid) and 0 <= x < len(self.grid[0]):
                return self.grid[y][x] > 0  # Tuile valide (pas -1 ou 0)
        return False

    def find_special_start_pos(self):
        """
        Trouve une position de spawn valide (première tuile praticable).
        Retourne [x, y].
        """
        if not self.grid:
            print("[SESSION] Aucune grille disponible pour trouver spawn")
            return [15, 15]
            
        print(f"[SESSION] Recherche spawn dans grille {len(self.grid[0])}x{len(self.grid)}")
        
        # Utilise le spawn par défaut
        spawn_x, spawn_y = 9, 10  # Position de spawn par défaut
        
        print(f"[SESSION] Spawn défini en ({spawn_x}, {spawn_y})")
        return [spawn_x, spawn_y]

    def load_data(self):
        try:
            with open(self.data_path, "r", encoding="utf-8") as f:
                print(f"[SESSION] Chargement des données de {self.name} depuis {self.data_path}")
                self.data = json.load(f)
                print(f"[SESSION] Données chargées avec succès : {list(self.data.keys())}")

                # 🔧 Correction proactive des couleurs manquantes dans le buste
                bust = self.data.get("bust", {})
                for key, layer in bust.items():
                    if layer.get("color") is None:
                        print(f"[SESSION] Couleur manquante pour '{key}' corrigée.")
                        layer["color"] = (255, 255, 255)

        except FileNotFoundError:
            print(f"[ERREUR SESSION] Fichier introuvable : {self.data_path}")

        # 🔁 Ajoute sprite_path si absent (utile pour explorateur)
        if "sprite_path" not in self.data:
            self.data["sprite_path"] = self.sprite_path

        # Position initiale par défaut
        if "position" not in self.data:
            self.data["position"] = [10, 3]

    def save_data(self):
        # Mise à jour sécurisée des champs critiques
        self.data["sprite_path"] = self.sprite_path

        # Assure qu'une position est toujours présente
        if "position" not in self.data:
            self.data["position"] = [5, 5]

        with open(self.data_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4)

    def has_custom_avatar(self):
        return os.path.exists(f"data/{self.name.lower()}_bust.png")

    def has_iso_sprite(self):
        return os.path.exists(f"data/{self.name.lower()}_iso.png")
