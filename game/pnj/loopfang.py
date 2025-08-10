import pygame
import os
from core.settings import get_grimoire_path
from core.analyze import analyser_script

class Loopfang:
    def __init__(self, name="Loopfang", sprite_path="assets/pnj/loopfang/loopfang_sprite.png", bust_path="assets/pnj/loopfang/loopfang_bust.png",
                 start_tile=(1, 8), combat_start_tile=(4, 2)):
        self.name = name
        self.sprite_path = sprite_path
        self.bust_path = bust_path
        self.map_name = "clairiere"
        self.start_tile = start_tile
        self.combat_start_tile = combat_start_tile  # Position pour le mode combat
        self.tile_pos = list(self.start_tile)
        self.quest_progress_key = "loopfang_progress"
        self.dialog_state = 0
        self.has_given_quests = False
        self.sprite = self._load_image(self.sprite_path)
        self.bust = self._load_image(self.bust_path)
        
        # Configuration du spritesheet Loopfang
        self.frame_width = 64
        self.frame_height = 64
        self.columns = 15
        self.rows = 16
        self.total_frames = self.columns * self.rows  # 240
        self.frames = self.load_frames()
        self.animations = self.load_animations()
        
        # État d'animation
        self.current_animation = "idle"
        self.frame_index = 0
        self.frame_timer = 0
        self.frame_delay = 200  # ms

    def _load_image(self, path):
        if path:
            try:
                return pygame.image.load(path).convert_alpha()
            except FileNotFoundError:
                print(f"[PNJ] ATTENTION: Impossible de charger l'image {path}")
        return None
        
    def load_frames(self):
        """Découpe le spritesheet en 240 frames individuelles (64x64 px chacune) et double la taille"""
        if not self.sprite:
            placeholder = pygame.Surface((self.frame_width * 2, self.frame_height * 2))
            placeholder.fill((255, 255, 0))  # Jaune pour Loopfang
            return [placeholder]
            
        frames = []
        for row in range(self.rows):
            for col in range(self.columns):
                rect = pygame.Rect(col * self.frame_width, row * self.frame_height,
                                 self.frame_width, self.frame_height)
                frame = self.sprite.subsurface(rect)
                # Doubler la taille
                frame = pygame.transform.scale(frame, (self.frame_width * 2, self.frame_height * 2))
                frames.append(frame)
        return frames
    
    def load_animations(self):
        """Définit l'animation idle avec les 4 frames spécifiques"""
        # Idle = frames 191, 192, 193, 194
        return {
            "idle": [191, 192, 193, 194]
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
            '#Q16': "Excellent ! Tu maîtrises les boucles while ! Attention à ne pas créer de boucles infinies !",
            '#Q17': "Bravo ! Tu as découvert les fonctions ! C'est la clé pour organiser ton code !",
            '#Q18': "Parfait ! Tu sais maintenant faire retourner des valeurs avec return !",
            '#Q19': "Impressionnant ! Tu comprends comment passer des paramètres aux fonctions !",
            '#Q20': "Magnifique ! Tu as accompli toutes les quêtes de base ! Tu es maintenant un vrai programmeur Python !"
        }
        return messages.get(quest_code, "")
        
    def speak(self):
        if not self.has_given_quests:
            messages = [
                "Salut, apprenti avancé !",
                "Je suis Loopfang, gardien des boucles et des fonctions.",
                "Tu as bien progressé jusqu'ici ! Il est temps de finaliser tes connaissances.",
                "Voici tes dernières quêtes fondamentales :\n" + \
                "16. Utilise une boucle while avec une condition\n" + \
                "17. Définis une fonction avec def nom_fonction():\n" + \
                "18. Utilise return dans une fonction pour retourner une valeur\n" + \
                "19. Appelle une fonction avec des paramètres\n" + \
                "20. Crée une fonction qui utilise plusieurs concepts appris"
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
                "Salut, apprenti avancé !",
                "Je suis Loopfang, gardien des boucles et des fonctions.",
                "Tu as bien progressé jusqu'ici ! Il est temps de finaliser tes connaissances.",
                "Voici tes dernières quêtes fondamentales :\n" + \
                "16. Utilise une boucle while avec une condition\n" + \
                "17. Définis une fonction avec def nom_fonction():\n" + \
                "18. Utilise return dans une fonction pour retourner une valeur\n" + \
                "19. Appelle une fonction avec des paramètres\n" + \
                "20. Crée une fonction qui utilise plusieurs concepts appris"
            ]
            print(f"[DIALOG] {self.name} dit: {messages[self.dialog_state]}")
            self.dialog_state = (self.dialog_state + 1) % len(messages)
            if self.dialog_state == 0:
                self.has_given_quests = True
                session.set_progress("pnj_loopfang_quests_given", True)
                session.save_data()
        else:
            completed = self.check_quests(session.name)
            
            if completed is None:
                print(f"[DIALOG] {self.name} dit: Je ne trouve pas ton grimoire...")
                return
                
            quest_codes = ['#Q16', '#Q17', '#Q18', '#Q19', '#Q20']
            completed_now = [q for q in quest_codes if q in completed]
            
            previously_completed = session.get_progress("loopfang_completed_quests", [])
            new_completions = [q for q in completed_now if q not in previously_completed]
            
            if new_completions:
                for quest in new_completions:
                    print(f"[DIALOG] {self.name} dit: {self.get_completion_message(quest)}")
                session.set_progress("loopfang_completed_quests", completed_now)
                session.save_data()
                
                # Vérifier si toutes les quêtes sont complétées
                if len(completed_now) == 5:
                    print(f"[DIALOG] {self.name} dit: FÉLICITATIONS ! Tu as terminé toutes les quêtes de base !")
                    print(f"[DIALOG] {self.name} dit: Tu es maintenant prêt pour des défis plus avancés !")
            elif completed_now:
                print(f"[DIALOG] {self.name} dit: Tu as déjà accompli {len(completed_now)} de mes quêtes. Excellent travail !")
            else:
                print(f"[DIALOG] {self.name} dit: Continue à explorer les boucles et les fonctions ! C'est la dernière étape !")

# Arbre de dialogue pour Loopfang
loopfang_dialogue_tree = {
    "start": {
        "text": "while apprentissage == True: print('Salut !') Que veux-tu maîtriser aujourd'hui ?",
        "responses": [
            {"label": "Les boucles", "next": "about_loops"},
            {"label": "Les fonctions", "next": "about_functions"},
            {"label": "Au revoir", "action": "end"}
        ]
    },
    "about_loops": {
        "text": "Les boucles for et while sont tes amies ! Elles répètent du code automatiquement.",
        "responses": [
            {"label": "Comment utiliser for ?", "next": "for_loop"},
            {"label": "Et while ?", "next": "while_loop"},
            {"label": "Retour", "next": "start"}
        ]
    },
    "for_loop": {
        "text": "for i in range(5): print(i) - Cette boucle affiche 0, 1, 2, 3, 4. Parfait pour répéter !",
        "responses": [
            {"label": "Très utile !", "next": "start"},
            {"label": "Et while ?", "next": "while_loop"},
            {"label": "Des exemples ?", "next": "loop_examples"}
        ]
    },
    "while_loop": {
        "text": "while condition: - Cette boucle continue tant que la condition est vraie. Attention aux boucles infinies !",
        "responses": [
            {"label": "Comment éviter l'infini ?", "next": "avoid_infinite"},
            {"label": "Et for ?", "next": "for_loop"},
            {"label": "Retour", "next": "start"}
        ]
    },
    "avoid_infinite": {
        "text": "Assure-toi que la condition devient False ! Incrémente un compteur ou modifie la variable de contrôle.",
        "responses": [
            {"label": "Bon conseil !", "next": "start"},
            {"label": "Des exemples ?", "next": "loop_examples"},
            {"label": "Merci Loopfang", "action": "end"}
        ]
    },
    "loop_examples": {
        "text": "for mot in ['Python', 'est', 'génial']: print(mot) - Parfait pour parcourir des listes !",
        "responses": [
            {"label": "Excellent !", "next": "start"},
            {"label": "Et les fonctions ?", "next": "about_functions"},
            {"label": "Merci", "action": "end"}
        ]
    },
    "about_functions": {
        "text": "def ma_fonction(): - Les fonctions organisent ton code en blocs réutilisables !",
        "responses": [
            {"label": "Comment créer une ?", "next": "create_function"},
            {"label": "Pourquoi les utiliser ?", "next": "why_functions"},
            {"label": "Retour", "next": "start"}
        ]
    },
    "create_function": {
        "text": "def saluer(nom): return f'Salut {nom}!' puis saluer('Alice') pour l'appeler !",
        "responses": [
            {"label": "Simple et efficace !", "next": "start"},
            {"label": "Pourquoi les fonctions ?", "next": "why_functions"},
            {"label": "Merci Loopfang", "action": "end"}
        ]
    },
    "why_functions": {
        "text": "for conseil in mes_conseils: print(conseil) - Évite la répétition, organise ton code, facilite les tests !",
        "responses": [
            {"label": "Logique !", "next": "start"},
            {"label": "Comment créer ?", "next": "create_function"},
            {"label": "À bientôt !", "action": "end"}
        ]
    }
}
