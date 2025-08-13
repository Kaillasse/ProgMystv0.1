# === core/session.py ===
import json
import os
from game.world import World
from core.settings import grid_to_iso, iso_to_grid, get_player_data_path, get_player_sprite_path, get_grimoire_path


class SessionManager:
    """
    Gestionnaire singleton pour éviter les multiples instances de GameSession
    """
    _instance = None
    _session = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_session(cls, name=None):
        """
        Récupère ou crée une session unique
        """
        if cls._session is None and name:
            print(f"[SESSION_MGR] Création unique session pour: {name}")
            cls._session = GameSession(name)
        elif cls._session and name and cls._session.name != name:
            print(f"[SESSION_MGR] Changement de session: {cls._session.name} → {name}")
            cls._session = GameSession(name)
        elif cls._session:
            print(f"[SESSION_MGR] Réutilisation session existante: {cls._session.name}")
        
        return cls._session
    
    @classmethod
    def has_session(cls):
        """Vérifie si une session existe"""
        return cls._session is not None
    
    @classmethod
    def get_current_session(cls):
        """Récupère la session actuelle sans en créer une nouvelle"""
        return cls._session
    
    @classmethod
    def reset(cls):
        """Remet à zéro la session (pour debug/tests)"""
        print("[SESSION_MGR] Reset session")
        cls._session = None
    @classmethod
    def check_existing_saves(cls):
        return [f[:-5] for f in os.listdir("data") if f.endswith(".json")]

    @classmethod
    def create_player_files(cls, name):
        with open(get_grimoire_path(name), "w") as f:
            f.write(f"# Grimoire de {name}\n\n")
        player_data = {"name": name, "progress": {}, "bust": {}, "sprite": {}, "border": {}}
        with open(get_player_data_path(name), "w", encoding="utf-8") as f:
            json.dump(player_data, f, indent=4)

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
        world = World()  # Uses "clairiere" as default map
        # World loads automatically, no need to call load()
        # Simplification : plus de map complexe, juste une grille basique
        self.map = [[1 for _ in range(20)] for _ in range(20)]  # Grille 20x20 simple
        self.grid = self.map
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

        # 🔧 Assure que le champ border existe (rétrocompatibilité)
        if "border" not in self.data:
            self.data["border"] = {"current_index": 0}
            print("[SESSION] Champ 'border' ajouté avec index par défaut 0")

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
