import pygame
import os
from core.settings import get_grimoire_path
from core.analyze import analyser_script
from game.entity import Entity

class Neuill(Entity):
    def __init__(self, tile_pos, name="Neuill", sprite_path="assets/pnj/neuil/critter_badger_SW_idle.png", 
                 bust_path="assets/pnj/neuil/neuil_bust.png"):
        
        # Initialisation de la classe Entity
        super().__init__(tile_pos, name)
        
        # Attributs spécifiques à Neuill
        self.sprite_path = sprite_path
        self.bust_path = bust_path
        self.quest_progress_key = "neuill_progress"
        self.dialog_state = 0
        self.has_given_quests = False
        
        # Chargement des ressources
        self.sprite = self._load_image(self.sprite_path)
        self.bust = self._load_image(self.bust_path)
        
        # Spécifique à Neuill - sprite en bande de 21 frames
        self.frame_width = 42  # À ajuster selon la taille réelle
        self.frame_height = 32  # À ajuster selon la taille réelle
        self.total_frames = 22
        self.frames = self.load_frames()
        self.animations = self.load_animations()
        
        # État d'animation
        self.current_animation = "idle"
        self.frame_index = 0
        self.frame_timer = 0
        self.frame_delay = 150  # Animation plus rapide pour créature

    def _load_image(self, path):
        if path:
            try:
                return pygame.image.load(path).convert_alpha()
            except FileNotFoundError:
                print(f"[PNJ] ATTENTION: Impossible de charger l'image {path}")
        return None
        
    def load_frames(self):
        """Découpe le sprite en bande horizontale de 21 frames et double la taille"""
        if not self.sprite:
            placeholder = pygame.Surface((self.frame_width * 1.5, self.frame_height * 1.5))
            placeholder.fill((139, 69, 19))
            return [placeholder]
        frames = []
        sprite_width = self.sprite.get_width()
        sprite_height = self.sprite.get_height()
        actual_frame_width = sprite_width // self.total_frames
        self.frame_width = actual_frame_width
        self.frame_height = sprite_height
        for i in range(self.total_frames):
            rect = pygame.Rect(i * actual_frame_width, 0, actual_frame_width, sprite_height)
            frame = self.sprite.subsurface(rect)
            frame = pygame.transform.scale(frame, (actual_frame_width * 1.5, sprite_height * 1.5))
            frames.append(frame)
        return frames
    
    def load_animations(self):
        """Définit les animations disponibles pour Neuill"""
        return {
            "idle": list(range(self.total_frames))  # Utilise toutes les frames pour l'animation idle
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
            '#Q6': "Excellent ! Tu as bien compris comment utiliser len() pour connaître la longueur d'une chaîne !",
            '#Q7': "Bravo ! Tu maîtrises l'indexation des chaînes. Tu peux maintenant accéder aux caractères individuels !",
            '#Q8': "Parfait ! Tu as découvert le slicing. C'est un outil puissant pour extraire des parties de chaînes !",
            '#Q9': "Impressionnant ! Tu utilises les méthodes de chaînes comme un vrai programmeur !",
            '#Q10': "Magnifique ! Tu maîtrises maintenant les boucles for avec range(). C'est la clé de l'automatisation !"
        }
        return messages.get(quest_code, "")
        
    def speak(self):
        if not self.has_given_quests:
            messages = [
                "Salutations, apprenti !",
                "Je suis Neuill, spécialiste des chaînes de caractères et des boucles.",
                "Tu as déjà parlé à Dame Indenta ? Parfait !",
                "Voici tes prochaines quêtes pour progresser :\n" + \
                "6. Utilise len() pour connaître la longueur d'une chaîne\n" + \
                "7. Accède au premier caractère d'une chaîne avec [0]\n" + \
                "8. Utilise le slicing [début:fin] pour extraire une portion\n" + \
                "9. Utilise une méthode de chaîne (.upper(), .lower(), .replace(), etc.)\n" + \
                "10. Utilise une boucle for avec range() pour répéter des actions"
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
                "Salutations, apprenti !",
                "Je suis Neuill, spécialiste des chaînes de caractères et des boucles.",
                "Tu as déjà parlé à Dame Indenta ? Parfait !",
                "Voici tes prochaines quêtes pour progresser :\n" + \
                "6. Utilise len() pour connaître la longueur d'une chaîne\n" + \
                "7. Accède au premier caractère d'une chaîne avec [0]\n" + \
                "8. Utilise le slicing [début:fin] pour extraire une portion\n" + \
                "9. Utilise une méthode de chaîne (.upper(), .lower(), .replace(), etc.)\n" + \
                "10. Utilise une boucle for avec range() pour répéter des actions"
            ]
            print(f"[DIALOG] {self.name} dit: {messages[self.dialog_state]}")
            self.dialog_state = (self.dialog_state + 1) % len(messages)
            if self.dialog_state == 0:
                self.has_given_quests = True
                session.set_progress("pnj_neuill_quests_given", True)
                session.save_data()
        else:
            completed = self.check_quests(session.name)
            
            if completed is None:
                print(f"[DIALOG] {self.name} dit: Je ne trouve pas ton grimoire...")
                return
                
            quest_codes = ['#Q6', '#Q7', '#Q8', '#Q9', '#Q10']
            completed_now = [q for q in quest_codes if q in completed]
            
            previously_completed = session.get_progress("neuill_completed_quests", [])
            new_completions = [q for q in completed_now if q not in previously_completed]
            
            if new_completions:
                for quest in new_completions:
                    print(f"[DIALOG] {self.name} dit: {self.get_completion_message(quest)}")
                session.set_progress("neuill_completed_quests", completed_now)
                session.save_data()
            elif completed_now:
                print(f"[DIALOG] {self.name} dit: Tu as déjà accompli {len(completed_now)} de mes quêtes. Bravo !")
            else:
                print(f"[DIALOG] {self.name} dit: Continue tes expérimentations ! Les chaînes et les boucles n'ont plus de secrets pour toi bientôt !")

# Arbre de dialogue pour Neuill
neuill_dialogue_tree = {
    "start": {
        "text": "Bienvenue dans ma clairière, jeune codeur ! Que puis-je faire pour toi ?",
        "responses": [
            {"label": "Parler de la clairière", "next": "talk_forest"},
            {"label": "Demander un conseil", "next": "advice"},
            {"label": "Au revoir", "action": "end"}
        ]
    },
    "talk_forest": {
        "text": "Cette clairière est un lieu paisible pour apprendre. Les arbres murmurent des secrets de programmation !",
        "responses": [
            {"label": "C'est poétique !", "next": "poetry"},
            {"label": "Dame Indenta ?", "next": "about_dame"},
            {"label": "Retour", "next": "start"}
        ]
    },
    "poetry": {
        "text": "La nature et le code ne font qu'un. Chaque fonction est comme une graine qui grandit !",
        "responses": [
            {"label": "Merci Neuill", "next": "start"},
            {"label": "Très sage", "action": "end"},
            {"label": "Un autre conseil", "next": "advice"}
        ]
    },
    "about_dame": {
        "text": "Dame Indenta ? Une excellente enseignante ! Elle donne les meilleures quêtes pour débuter.",
        "responses": [
            {"label": "Je l'ai rencontrée", "next": "met_dame"},
            {"label": "Où la trouver ?", "next": "find_dame"},
            {"label": "Retour", "next": "start"}
        ]
    },
    "met_dame": {
        "text": "Parfait ! Ses quêtes t'aideront à maîtriser les bases de Python. Continue sur cette voie !",
        "responses": [
            {"label": "Merci du conseil", "next": "start"},
            {"label": "D'autres conseils ?", "next": "advice"},
            {"label": "À bientôt", "action": "end"}
        ]
    },
    "find_dame": {
        "text": "Dame Indenta se trouve généralement près du centre de la clairière. Tu ne peux pas la rater !",
        "responses": [
            {"label": "Je vais la chercher", "action": "end"},
            {"label": "Merci", "next": "start"},
            {"label": "Autre chose ?", "next": "advice"}
        ]
    },
    "advice": {
        "text": "Mon conseil : explore chaque zone avec curiosité. Chaque endroit a ses secrets à révéler !",
        "responses": [
            {"label": "Sage conseil", "next": "start"},
            {"label": "Merci Neuill", "action": "end"},
            {"label": "Encore un conseil", "next": "advice2"}
        ]
    },
    "advice2": {
        "text": "Pratique régulièrement ! Même 15 minutes par jour valent mieux qu'une session de 3 heures une fois par semaine.",
        "responses": [
            {"label": "C'est noté !", "next": "start"},
            {"label": "Merci beaucoup", "action": "end"},
            {"label": "Retour", "next": "start"}
        ]
    }
}
