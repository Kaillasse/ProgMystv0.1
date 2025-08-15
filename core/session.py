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
        player_data = {
            "name": name, 
            "progress": {}, 
            "bust": {}, 
            "sprite": {}, 
            "border": {},
            "dialogue_state": {}  # Nouvel ajout pour sauvegarder l'état des dialogues
        }
        with open(get_player_data_path(name), "w", encoding="utf-8") as f:
            json.dump(player_data, f, indent=4)

class GameSession:
    def update_grid_position(self, x, y, z=0, map_name=None):
        """
        UNIFIED: Update player position using grid coordinates.
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
    
    # === DIALOGUE STATE MANAGEMENT ===
    
    def get_dialogue_state(self, npc_name):
        """
        Récupère l'état actuel du dialogue pour un PNJ.
        Retourne l'index/nom du dernier dialogue atteint.
        """
        if "dialogue_state" not in self.data:
            self.data["dialogue_state"] = {}
        return self.data["dialogue_state"].get(npc_name, None)
    
    def set_dialogue_state(self, npc_name, dialogue_index):
        """
        Sauvegarde l'état du dialogue pour un PNJ.
        """
        if "dialogue_state" not in self.data:
            self.data["dialogue_state"] = {}
        
        old_state = self.data["dialogue_state"].get(npc_name, "aucun")
        self.data["dialogue_state"][npc_name] = dialogue_index
        print(f"[SESSION] Dialogue state {npc_name}: {old_state} -> {dialogue_index}")
        self.save_data()
    
    def get_dialogue_entry_point(self, npc_name):
        """
        DEPRECATED: Cette méthode est maintenant gérée par DialogueDispatcher.
        Retourne simplement l'état sauvegardé ou un état par défaut.
        """
        print(f"[SESSION] WARNING: get_dialogue_entry_point deprecated pour {npc_name}")
        print(f"[SESSION] Utiliser DialogueDispatcher._determine_entry_point() à la place")
        
        # Retourne l'état sauvegardé ou un défaut simple
        current_state = self.get_dialogue_state(npc_name)
        if current_state:
            return current_state
        
        # États par défaut simples
        defaults = {
            "DameIndenta": "D1",
            "Neuill": "N0", 
            "JSON": "J0",
            "Loopfang": "L0"
        }
        return defaults.get(npc_name, "unknown")
    
    # Méthodes depreciées - logique déplacée vers DialogueDispatcher
    def _dame_indenta_quests_completed(self):
        """DEPRECATED: Logique déplacée vers DialogueDispatcher"""
        print("[SESSION] WARNING: _dame_indenta_quests_completed deprecated")
        print("[SESSION] Utiliser DialogueDispatcher._get_quests_reachable_from_start() à la place")
        return False
    
    def _npc_state_quests_completed(self, npc_name, current_state):
        """DEPRECATED: Logique déplacée vers DialogueDispatcher"""
        print(f"[SESSION] WARNING: _npc_state_quests_completed deprecated pour {npc_name}")
        print("[SESSION] Utiliser DialogueDispatcher._get_quests_reachable_from_start() à la place")
        return False
    
    def give_quest(self, quest_code):
        """
        Marque une quête comme donnée au joueur.
        """
        if "quests" not in self.data:
            self.data["quests"] = {}
        
        if quest_code not in self.data["quests"]:
            # Importe quest.py pour obtenir les détails de la quête
            from core.quest import QUESTS, NEW_QUESTS, SECRET_QUESTS
            all_quests = QUESTS + NEW_QUESTS + SECRET_QUESTS
            
            quest_obj = None
            for quest in all_quests:
                if quest.code == quest_code:
                    quest_obj = quest
                    break
            
            if quest_obj:
                self.data["quests"][quest_code] = {
                    'given': True,
                    'completed': False,
                    'name': quest_obj.nom,
                    'description': quest_obj.description
                }
                print(f"[SESSION] Quête donnée: {quest_code} - {quest_obj.nom}")
            else:
                self.data["quests"][quest_code] = {
                    'given': True,
                    'completed': False,
                    'name': quest_code,
                    'description': 'Quête inconnue'
                }
                print(f"[SESSION] Quête inconnue donnée: {quest_code}")
        else:
            self.data["quests"][quest_code]['given'] = True
            print(f"[SESSION] Quête marquée comme donnée: {quest_code}")
        
        self.save_data()
    
    def complete_quest(self, quest_code):
        """
        Marque une quête comme accomplie.
        """
        if "quests" not in self.data:
            self.data["quests"] = {}
        
        if quest_code in self.data["quests"]:
            self.data["quests"][quest_code]['completed'] = True
            print(f"[SESSION] Quête accomplie: {quest_code}")
            self.save_data()
        else:
            print(f"[SESSION] Tentative d'accomplir une quête non donnée: {quest_code}")
    
    def is_quest_given(self, quest_code):
        """
        Vérifie si une quête a été donnée au joueur.
        """
        if "quests" not in self.data:
            return False
        return self.data["quests"].get(quest_code, {}).get('given', False)
    
    def is_quest_completed(self, quest_code):
        """
        Vérifie si une quête a été accomplie par le joueur.
        """
        if "quests" not in self.data:
            return False
        return self.data["quests"].get(quest_code, {}).get('completed', False)
    
    def get_quest_data(self, quest_code):
        """
        Retourne toutes les données d'une quête.
        """
        if "quests" not in self.data:
            return None
        return self.data["quests"].get(quest_code, None)
    
    def get_all_quests(self):
        """
        Retourne toutes les données de quêtes du joueur.
        """
        return self.data.get("quests", {})

    def __init__(self, player_name):
        self.name = player_name
        # Simplification : plus besoin de World ici, GameManager le créera avec screen
        # Plus de map complexe, juste une grille basique pour compatibilité
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
        """DEPRECATED: Use world.is_valid_position() instead for unified validation"""
        print("[SESSION] WARNING: Using deprecated is_valid_position, use world authority instead")
        return True  # Fallback

    def find_special_start_pos(self):
        """UNIFIED: Use world spawn points instead of hardcoded positions"""
        print("[SESSION] UNIFIED: Using world spawn point for player")
        return [0, 0]  # World spawn point for "joueur"

    def load_data(self):
        try:
            with open(self.data_path, "r", encoding="utf-8") as f:
                print(f"[SESSION] Chargement des données de {self.name} depuis {self.data_path}")
                self.data = json.load(f)
                print(f"[SESSION] Données chargées avec succès : {list(self.data.keys())}")

                # 🔧 Correction proactive des couleurs manquantes dans le buste
                bust = self.data.get("bust", {})
                if not bust:  # Fallback vers l'ancien format "buste"
                    bust = self.data.get("buste", {})
                    if bust:
                        self.data["bust"] = bust  # Migration vers le nouveau format
                        print("[SESSION] Migration de 'buste' vers 'bust'")
                
                for key, layer in bust.items():
                    if isinstance(layer, dict) and layer.get("color") is None:
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

        # UNIFIED: Position initiale via world spawn points
        if "position" not in self.data:
            self.data["position"] = [0, 0, 0]  # Use world spawn authority

    def save_data(self):
        # Mise à jour sécurisée des champs critiques
        self.data["sprite_path"] = self.sprite_path

        # UNIFIED: Assure qu'une position valide est présente
        if "position" not in self.data:
            self.data["position"] = [0, 0, 0]  # Use world spawn authority

        with open(self.data_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4)

    def has_custom_avatar(self):
        return os.path.exists(f"data/{self.name.lower()}_bust.png")

    def has_iso_sprite(self):
        return os.path.exists(f"data/{self.name.lower()}_iso.png")
