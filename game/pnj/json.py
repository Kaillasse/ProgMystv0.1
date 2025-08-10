import pygame
import os
from core.settings import get_grimoire_path
from core.analyze import analyser_script

class JSON:
    def __init__(self, name="JSON", sprite_path="assets/pnj/JSON/json_sprite.png", bust_path="assets/pnj/JSON/json_bust.png",
                 start_tile=(3, 6)):
        self.name = name
        self.sprite_path = sprite_path
        self.bust_path = bust_path
        self.map_name = "clairiere"
        self.start_tile = start_tile
        self.tile_pos = list(self.start_tile)
        self.quest_progress_key = "json_progress"
        self.dialog_state = 0
        self.has_given_quests = False
        self.sprite = self._load_image(self.sprite_path)
        self.bust = self._load_image(self.bust_path)
        
        # Configuration sprite JSON - sprite en bande horizontale
        self.total_frames = 7  # Nombre réel de frames dans le PNG
        self.frame_width = 41  # Largeur réelle d'une frame
        self.frame_height = 25 # Hauteur réelle d'une frame
        self.target_width = 82 # Double la taille
        self.target_height = 50 # Double la taille
        self.frames = self.load_frames()
        self.animations = self.load_animations()
        
        # État d'animation
        self.current_animation = "idle"
        self.frame_index = 0
        self.frame_timer = 0
        self.frame_delay = 200  # Animation rapide

    def _load_image(self, path):
        if path:
            try:
                return pygame.image.load(path).convert_alpha()
            except FileNotFoundError:
                print(f"[PNJ] ATTENTION: Impossible de charger l'image {path}")
        return None
        
    def load_frames(self):
        """Découpe le spritesheet en frames individuelles et double la taille"""
        if not self.sprite:
            placeholder = pygame.Surface((self.target_width, self.target_height))
            placeholder.fill((0, 0, 255))  # Bleu pour JSON
            return [placeholder]
            
        frames = []
        sprite_width = self.sprite.get_width()
        sprite_height = self.sprite.get_height()
        actual_frame_width = sprite_width // self.total_frames
        
        for i in range(self.total_frames):
            rect = pygame.Rect(i * actual_frame_width, 0, actual_frame_width, sprite_height)
            frame = self.sprite.subsurface(rect)
            # Doubler la taille
            frame = pygame.transform.scale(frame, (self.target_width, self.target_height))
            frames.append(frame)
        return frames
    
    def load_animations(self):
        """Définit les animations disponibles pour JSON"""
        return {
            "idle": list(range(self.total_frames))
        }
    
    def update_animation(self, dt):
        """Met à jour l'animation du PNJ"""
        self.frame_timer += dt
        if self.frame_timer >= self.frame_delay:
            self.frame_timer = 0
            animation_frames = self.animations.get(self.current_animation, [0])
            self.frame_index = (self.frame_index + 1) % len(animation_frames)
    
    def get_current_frame(self):
        """Retourne la frame actuelle à afficher"""
        if not self.frames:
            return None
        animation_frames = self.animations.get(self.current_animation, [0])
        if animation_frames:
            frame_id = animation_frames[self.frame_index]
            if 0 <= frame_id < len(self.frames):
                return self.frames[frame_id]
        return self.frames[0] if self.frames else None

    def load_progress_from_session(self, session):
        if session:
            self.has_given_quests = session.get_progress(f"pnj_{self.name.lower()}_quests_given", False)
            if self.has_given_quests:
                self.dialog_state = 0
            print(f"[DEBUG] Progression chargée pour {self.name}: quêtes données = {self.has_given_quests}")
    
    def check_quests(self, player_name):
        """Vérifie l'état des quêtes du joueur"""
        if not player_name:
            print(f"[DEBUG] Nom du joueur invalide: {player_name}")
            return None
            
        grimoire_path = get_grimoire_path(player_name)
        
        if not os.path.exists(grimoire_path):
            print(f"[DEBUG] Grimoire introuvable: {grimoire_path}")
            return None
            
        if not os.access(grimoire_path, os.R_OK):
            print(f"[DEBUG] Grimoire non lisible: {grimoire_path}")
            return None
            
        if os.path.getsize(grimoire_path) == 0:
            print(f"[DEBUG] Grimoire vide: {grimoire_path}")
            return None
        
        completed_quests = analyser_script(grimoire_path)
        return completed_quests
        
    def get_completion_message(self, quest_code):
        """Retourne le message de félicitations pour une quête complétée"""
        messages = {
            '#Q11': "Excellent ! Tu as compris comment créer et utiliser des listes !",
            '#Q12': "Bravo ! Tu sais maintenant ajouter des éléments à une liste avec append() !",
            '#Q13': "Parfait ! Tu maîtrises l'accès aux éléments par index !",
            '#Q14': "Impressionnant ! Tu utilises les boucles for pour parcourir les listes !",
            '#Q15': "Magnifique ! Tu as découvert les dictionnaires, une structure très puissante !"
        }
        return messages.get(quest_code, "")
        
    def speak(self):
        if not self.has_given_quests:
            messages = [
                "Bienvenue, jeune codeur !",
                "Je suis JSON, maître des structures de données.",
                "Tu as progressé avec Dame Indenta et Neuill ? Formidable !",
                "Il est temps d'apprendre les listes et dictionnaires :\n" + \
                "11. Crée une liste avec [] et au moins 3 éléments\n" + \
                "12. Utilise .append() pour ajouter un élément à une liste\n" + \
                "13. Accède à un élément de liste avec son index [n]\n" + \
                "14. Utilise une boucle for pour parcourir une liste\n" + \
                "15. Crée un dictionnaire avec {} et au moins 2 paires clé:valeur"
            ]
            print(f"[DIALOG] {self.name} dit: {messages[self.dialog_state]}")
            self.dialog_state = (self.dialog_state + 1) % len(messages)
            if self.dialog_state == 0:
                self.has_given_quests = True
        else:
            print(f"[DIALOG] {self.name} dit: Je ne peux pas vérifier tes quêtes sans accéder à ta session...")
            print(f"[DIALOG] {self.name} dit: Assure-toi d'être connecté correctement !")
        
    def interact(self, session=None):
        """Interaction quand le joueur clique sur le PNJ"""
        if session:
            self.interact_with_session(session)
        else:
            self.speak()
            
    def interact_with_session(self, session):
        """Interaction avec accès à la session du joueur"""
        self.load_progress_from_session(session)
        
        if not self.has_given_quests:
            messages = [
                "Bienvenue, jeune codeur !",
                "Je suis JSON, maître des structures de données.",
                "Tu as progressé avec Dame Indenta et Neuill ? Formidable !",
                "Il est temps d'apprendre les listes et dictionnaires :\n" + \
                "11. Crée une liste avec [] et au moins 3 éléments\n" + \
                "12. Utilise .append() pour ajouter un élément à une liste\n" + \
                "13. Accède à un élément de liste avec son index [n]\n" + \
                "14. Utilise une boucle for pour parcourir une liste\n" + \
                "15. Crée un dictionnaire avec {} et au moins 2 paires clé:valeur"
            ]
            print(f"[DIALOG] {self.name} dit: {messages[self.dialog_state]}")
            self.dialog_state = (self.dialog_state + 1) % len(messages)
            if self.dialog_state == 0:
                self.has_given_quests = True
                session.set_progress("pnj_json_quests_given", True)
                session.save_data()
        else:
            completed = self.check_quests(session.name)
            
            if completed is None:
                print(f"[DIALOG] {self.name} dit: Je ne trouve pas ton grimoire...")
                return
                
            quest_codes = ['#Q11', '#Q12', '#Q13', '#Q14', '#Q15']
            completed_now = [q for q in quest_codes if q in completed]
            
            previously_completed = session.get_progress("json_completed_quests", [])
            new_completions = [q for q in completed_now if q not in previously_completed]
            
            if new_completions:
                for quest in new_completions:
                    print(f"[DIALOG] {self.name} dit: {self.get_completion_message(quest)}")
                session.set_progress("json_completed_quests", completed_now)
                session.save_data()
            elif completed_now:
                print(f"[DIALOG] {self.name} dit: Tu as déjà accompli {len(completed_now)} de mes quêtes. Continue ainsi !")
            else:
                print(f"[DIALOG] {self.name} dit: Expérimente avec les listes et dictionnaires ! Ils sont la base de nombreux programmes !")

# Arbre de dialogue pour JSON
json_dialogue_tree = {
    "start": {
        "text": "{ \"greeting\": \"Salut, codeur !\" } Que veux-tu apprendre sur les données ?",
        "responses": [
            {"label": "Les listes", "next": "about_lists"},
            {"label": "Les dictionnaires", "next": "about_dicts"},
            {"label": "Au revoir", "action": "end"}
        ]
    },
    "about_lists": {
        "text": "Les listes sont comme des boîtes numérotées ! [1, 2, 'Python'] - tu peux y mettre tout ce que tu veux !",
        "responses": [
            {"label": "Comment les utiliser ?", "next": "list_usage"},
            {"label": "Et les dictionnaires ?", "next": "about_dicts"},
            {"label": "Retour", "next": "start"}
        ]
    },
    "list_usage": {
        "text": "Utilise [] pour créer, ma_liste[0] pour accéder au premier élément, et for item in ma_liste: pour parcourir !",
        "responses": [
            {"label": "Très utile !", "next": "start"},
            {"label": "Des exemples ?", "next": "list_examples"},
            {"label": "Merci JSON", "action": "end"}
        ]
    },
    "list_examples": {
        "text": "fruits = ['pomme', 'banane'] puis fruits.append('orange') pour ajouter ! Simple et efficace !",
        "responses": [
            {"label": "Génial !", "next": "start"},
            {"label": "Et les dictionnaires ?", "next": "about_dicts"},
            {"label": "Merci", "action": "end"}
        ]
    },
    "about_dicts": {
        "text": "{ \"clé\": \"valeur\" } - Les dictionnaires associent des clés à des valeurs ! Parfait pour organiser !",
        "responses": [
            {"label": "Comment ça marche ?", "next": "dict_usage"},
            {"label": "Et les listes ?", "next": "about_lists"},
            {"label": "Retour", "next": "start"}
        ]
    },
    "dict_usage": {
        "text": "personne = {'nom': 'Alice', 'age': 25} puis personne['nom'] pour récupérer 'Alice' !",
        "responses": [
            {"label": "C'est logique !", "next": "start"},
            {"label": "Plus d'exemples ?", "next": "dict_examples"},
            {"label": "Merci JSON", "action": "end"}
        ]
    },
    "dict_examples": {
        "text": "{ \"motivation\": \"Continue à coder !\", \"conseil\": \"Pratique avec des données réelles !\" }",
        "responses": [
            {"label": "Inspirant !", "next": "start"},
            {"label": "Merci pour tout", "action": "end"},
            {"label": "Autres conseils ?", "next": "final_advice"}
        ]
    },
    "final_advice": {
        "text": "Mes clés et valeurs t'aideront à organiser tes informations. Les données bien structurées = code plus propre !",
        "responses": [
            {"label": "Sage conseil", "next": "start"},
            {"label": "Merci JSON", "action": "end"},
            {"label": "À bientôt !", "action": "end"}
        ]
    }
}
