#INITIALISATION DES PNJ : Une seule classe par PNJ
import pygame
from core.settings import get_grimoire_path
from core.analyze import analyser_script
from game.world_manager import WorldManager



class NPC:
    def __init__(self, name, sprite_path, bust_path=None,
                 start_map=None, start_tile=None,
                 animations=None, dialogues=None, quest_progress_key=None, map_name=None):
        self.name = name
        self.sprite_path = sprite_path
        self.bust_path = bust_path
        self.map_name = start_map or map_name
        self.start_tile = start_tile or (0, 0)
        self.tile_pos = list(self.start_tile)
        self.dialogues = dialogues or []
        self.dialogue_index = 0
        self.quest_progress_key = quest_progress_key or f"{self.name.lower()}_progress"
        self.dialog_state = 0
        self.has_given_quests = False
        self.sprite = self._load_image(self.sprite_path)
        self.bust = self._load_image(self.bust_path)
        self.animations = animations or {}

    def _load_image(self, path):
        if path:
            try:
                return pygame.image.load(path).convert_alpha()
            except (pygame.error, FileNotFoundError):
                print(f"[NPC] ATTENTION: Impossible de charger l'image {path}")
        return None

    def load_progress_from_session(self, session):
        if session:
            self.has_given_quests = session.get_progress(f"npc_{self.name.lower()}_quests_given", False)
            if self.has_given_quests:
                self.dialog_state = 0
            print(f"[DEBUG] Progression chargée pour {self.name}: quêtes données = {self.has_given_quests}")

    def load_progress(self, session):
        if session:
            progress = session.data.get(self.quest_progress_key, {})
            self.dialog_state = progress.get("dialog_state", 0)
            self.has_given_quests = progress.get("has_given_quests", False)

    def save_progress(self, session):
        if session:
            session.data[self.quest_progress_key] = {
                "dialog_state": self.dialog_state,
                "has_given_quests": self.has_given_quests
            }
            session.save_data()

    def speak(self):
        if self.dialogues:
            print(f"{self.name} dit : {self.dialogues[self.dialogue_index]}")
            self.dialogue_index = (self.dialogue_index + 1) % len(self.dialogues)
        else:
            print(f"{self.name} reste silencieux...")

    def distance_to_player(self, player):
        return abs(self.tile_pos[0] - player.tile_pos[0]) + abs(self.tile_pos[1] - player.tile_pos[1])

#DameIndenta
class DameIndenta(NPC):
    def __init__(self, name="Dame Indenta", sprite_path="assets/pnj/di/di_sprite.png", bust_path="assets/pnj/di/di_bust.png",
                 start_tile=(15, 10)):
        super().__init__(name, sprite_path, bust_path, start_map="clairiere", start_tile=start_tile, quest_progress_key="dame_indenta_progress")
        self.frame_width = 48
        self.frame_height = 96
        self.columns = 12
        self.rows = 8
        self.frames = self.load_frames()
        self.animations = self.load_animations()
        # État d'animation
        self.current_animation = "idle_front"
        self.frame_index = 0
        self.frame_timer = 0
        self.frame_delay = 500  # ms entre les frames
        
    def load_frames(self):
        """Découpe le spritesheet en frames individuelles"""
        if not self.sprite:
            # Créer une frame de substitution si pas de sprite
            placeholder = pygame.Surface((self.frame_width, self.frame_height))
            placeholder.fill((255, 0, 255))  # Magenta pour debug
            return [placeholder]
            
        frames = []
        for row in range(self.rows):
            for col in range(self.columns):
                rect = pygame.Rect(col * self.frame_width, row * self.frame_height,
                                 self.frame_width, self.frame_height)
                frames.append(self.sprite.subsurface(rect))
        return frames
    
    def load_animations(self):
        """Définit les animations disponibles"""
        return {
            "idle_front": [1], 
            "idle_left": [13], 
            "idle_right": [25], 
            "idle_back": [37]
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
    
    def check_quests(self, player_name):
        """Vérifie l'état des quêtes du joueur"""
        import os
        
        # 1. Vérifier si le nom du joueur est valide
        if not player_name:
            print(f"[DEBUG] Nom du joueur invalide: {player_name}")
            return None
            
        # 2. Obtenir le chemin du grimoire
        grimoire_path = get_grimoire_path(player_name)
        
        # 3. Vérifier si le fichier existe
        if not os.path.exists(grimoire_path):
            print(f"[DEBUG] Grimoire introuvable: {grimoire_path}")
            return None
            
        # 4. Vérifier si le fichier est lisible
        if not os.access(grimoire_path, os.R_OK):
            print(f"[DEBUG] Grimoire non lisible: {grimoire_path}")
            return None
            
        # 5. Vérifier si le fichier n'est pas vide
        if os.path.getsize(grimoire_path) == 0:
            print(f"[DEBUG] Grimoire vide: {grimoire_path}")
            return None
        
        # Si toutes les vérifications sont passées, analyser le code
        completed_quests = analyser_script(grimoire_path)
        return completed_quests
        
    def get_completion_message(self, quest_code):
        """Retourne le message de félicitations pour une quête complétée"""
        messages = {
            '#Q1': "Félicitations ! Tu as bien compris l'utilisation des variables. C'est la base de la programmation !",
            '#Q2': "Excellent ! Tu maîtrises l'affectation des variables. C'est crucial pour manipuler les données !",
            '#Q3': "Bravo ! Tu sais maintenant afficher des messages avec print(). La communication est importante !",
            '#Q4': "Parfait ! Tu as réussi à utiliser input() pour interagir avec l'utilisateur !",
            '#Q5': "Impressionnant ! Tu maîtrises les conditions if. Tu peux maintenant créer des programmes qui prennent des décisions !"
        }
        return messages.get(quest_code, "")
        
    def speak(self):
        if not self.has_given_quests:
            messages = [
                "Bienvenue, jeune apprenti programmeur !",
                "Je suis Dame Indenta, la gardienne des quêtes de programmation.",
                "Je vais te confier tes premières quêtes pour apprendre Python.",
                "Ouvre ton grimoire (fichier Python) et montre-moi tes compétences !",
                "Voici tes 5 premières quêtes :\n" + \
                "1. Utilise au moins 2 variables (entier, réel ou chaîne)\n" + \
                "2. Affecte une valeur à une variable avec =\n" + \
                "3. Utilise print() pour afficher un message\n" + \
                "4. Utilise input() pour lire une entrée utilisateur\n" + \
                "5. Utilise une instruction if pour une condition"
            ]
            print(f"[DIALOG] {self.name} dit: {messages[self.dialog_state]}")
            self.dialog_state = (self.dialog_state + 1) % len(messages)
            if self.dialog_state == 0:
                self.has_given_quests = True
        else:
            # Vérifier les quêtes complétées sans session
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
        # Charger la progression depuis la session
        self.load_progress_from_session(session)
        
        if not self.has_given_quests:
            messages = [
                "Bienvenue, jeune apprenti programmeur !",
                "Je suis Dame Indenta, la gardienne des quêtes de programmation.",
                "Je vais te confier tes premières quêtes pour apprendre Python.",
                "Ouvre ton grimoire (fichier Python) et montre-moi tes compétences !",
                "Voici tes 5 premières quêtes :\n" + \
                "1. Utilise au moins 2 variables (entier, réel ou chaîne)\n" + \
                "2. Affecte une valeur à une variable avec =\n" + \
                "3. Utilise print() pour afficher un message\n" + \
                "4. Utilise input() pour lire une entrée utilisateur\n" + \
                "5. Utilise une instruction if pour une condition"
            ]
            print(f"[DIALOG] {self.name} dit: {messages[self.dialog_state]}")
            self.dialog_state = (self.dialog_state + 1) % len(messages)
            if self.dialog_state == 0:
                self.has_given_quests = True
                # Sauvegarder la progression du dialogue
                session.set_progress("npc_dame_indenta_quests_given", True)
                session.save_data()
        else:
            # Vérifier les quêtes complétées
            completed = self.check_quests(session.name)
            
            if completed is None:
                print(f"[DIALOG] {self.name} dit: Je ne trouve pas ton grimoire dans le dossier des étudiants...")
                return
                
            quest_codes = ['#Q1', '#Q2', '#Q3', '#Q4', '#Q5']
            completed_now = [q for q in quest_codes if q in completed]
            
            # Vérifier quelles quêtes sont nouvellement complétées
            previously_completed = session.get_progress("completed_quests", [])
            new_completions = [q for q in completed_now if q not in previously_completed]
            
            if new_completions:
                # Afficher les messages pour les nouvelles quêtes complétées
                for quest in new_completions:
                    print(f"[DIALOG] {self.name} dit: {self.get_completion_message(quest)}")
                # Sauvegarder les nouvelles completions
                session.set_progress("completed_quests", completed_now)
                session.save_data()
            elif completed_now:
                print(f"[DIALOG] {self.name} dit: Tu as déjà accompli {len(completed_now)} de mes quêtes. Continue ainsi !")
            else:
                print(f"[DIALOG] {self.name} dit: Continue à travailler sur ton grimoire. Je sens que tu es sur la bonne voie !")


#Neuill
class Neuill(NPC):
    def __init__(self, name="Neuill", sprite_path="assets/pnj/neuil/critter_badger_SW_idle.png", 
                 bust_path="assets/pnj/neuil/neuil_bust.png", start_tile=(13, 10)):
        super().__init__(name, sprite_path, bust_path, start_map="clairiere", start_tile=start_tile, quest_progress_key="neuill_progress")
        
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

    def speak(self):
        """Dialogue de base de Neuill"""
        messages = [
            "Salut, jeune apprenti !",
            "Je suis Neuill, le gardien de cette petite clairière.",
            "Tu sembles nouveau dans le monde de la programmation ?",
            "N'hésite pas à explorer et à parler aux autres PNJ !",
            "Chacun d'entre nous a des conseils à te donner."
        ]
        
        if not hasattr(self, 'dialog_state'):
            self.dialog_state = 0
            
        print(f"[DIALOG] {self.name} dit: {messages[self.dialog_state]}")
        self.dialog_state = (self.dialog_state + 1) % len(messages)
        
    def interact(self, session=None):
        """Interaction avec Neuill"""
        if session:
            self.interact_with_session(session)
        else:
            self.speak()
            
    def interact_with_session(self, session):
        """Interaction avec accès à la session du joueur"""
        # Charger la progression depuis la session
        self.load_progress_from_session(session)
        
        messages = [
            "Bienvenue dans ma clairière, jeune codeur !",
            "Je vois que tu explores le monde de Progmyst.",
            "As-tu déjà rencontré Dame Indenta ? Elle donne d'excellentes quêtes !",
            "Continue à explorer, chaque zone a ses secrets.",
            "Reviens me voir quand tu auras progressé !"
        ]
        
        if not hasattr(self, 'dialog_state'):
            self.dialog_state = 0
            
        print(f"[DIALOG] {self.name} dit: {messages[self.dialog_state]}")
        self.dialog_state = (self.dialog_state + 1) % len(messages)
        
        # Sauvegarder la progression
        if session:
            session.set_progress(f"npc_{self.name.lower()}_talked", True)
            session.save_data()

#JSON
class JSON(NPC):
    def __init__(self, name="JSON", sprite_path="assets/pnj/JSON/json_sprite.png", 
                 bust_path="assets/pnj/JSON/json_bust.png", start_tile=(17, 10)):
        super().__init__(name, sprite_path, bust_path, start_map="clairiere", start_tile=start_tile, quest_progress_key="json_progress")
        
        # Configuration sprite standard
        self.total_frames = 7  # Mets ici le nombre réel de frames dans ton PNG
        self.frame_width = 41  # Mets ici la largeur réelle d'une frame
        self.frame_height = 25 # Mets ici la hauteur réelle d'une frame
        self.target_width = 82 # Double la taille (par exemple)
        self.target_height = 50 # Double la taille (par exemple)
        self.frames = self.load_frames()
        self.animations = self.load_animations()
        
        # État d'animation
        self.current_animation = "idle"
        self.frame_index = 0
        self.frame_timer = 0
        self.frame_delay = 200  # Animation rapide pour test
        
    def load_frames(self):
        """Découpe le spritesheet en frames individuelles et double la taille"""
        if not self.sprite:
            placeholder = pygame.Surface((self.target_width * 1.5, self.target_height * 1.5))
            placeholder.fill((100, 150, 255))
            return [placeholder]
        frames = []
        sprite_width = self.sprite.get_width()
        sprite_height = self.sprite.get_height()
        actual_frame_width = sprite_width // self.total_frames
        for i in range(self.total_frames):
            rect = pygame.Rect(i * actual_frame_width, 0, actual_frame_width, sprite_height)
            frame = self.sprite.subsurface(rect)
            frame = pygame.transform.scale(frame, (self.target_width * 1.5, self.target_height * 1.5))
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

    def speak(self):
        """Dialogue de base de JSON"""
        messages = [
            "{ \"message\": \"Bonjour, développeur !\" }",
            "Je suis JSON, un format de données très utilisé.",
            "Tu apprendras bientôt à me manipuler en Python !",
            "Les dictionnaires Python sont mes cousins proches.",
            "{ \"conseil\": \"Structure tes données comme moi !\" }"
        ]
        
        if not hasattr(self, 'dialog_state'):
            self.dialog_state = 0
            
        print(f"[DIALOG] {self.name} dit: {messages[self.dialog_state]}")
        self.dialog_state = (self.dialog_state + 1) % len(messages)
        
    def interact(self, session=None):
        """Interaction avec JSON"""
        if session:
            self.interact_with_session(session)
        else:
            self.speak()
            
    def interact_with_session(self, session):
        """Interaction avec accès à la session du joueur"""
        self.load_progress_from_session(session)
        
        messages = [
            "{ \"greeting\": \"Salut, codeur !\" }",
            "Je vois que tu explores le monde des données.",
            "Bientôt tu apprendras les dictionnaires et les listes !",
            "Mes clés et valeurs t'aideront à organiser tes informations.",
            "{ \"motivation\": \"Continue à coder !\" }"
        ]
        
        if not hasattr(self, 'dialog_state'):
            self.dialog_state = 0
            
        print(f"[DIALOG] {self.name} dit: {messages[self.dialog_state]}")
        self.dialog_state = (self.dialog_state + 1) % len(messages)
        
        if session:
            session.set_progress(f"npc_{self.name.lower()}_talked", True)
            session.save_data()

#Loopfang
class Loopfang(NPC):
    def __init__(self, name="Loopfang", sprite_path="assets/pnj/loopfang/loopfang_sprite.png", 
                 bust_path="assets/pnj/loopfang/loopfang_bust.png", start_tile=(15, 12)):
        super().__init__(name, sprite_path, bust_path, start_map="clairiere", start_tile=start_tile, quest_progress_key="loopfang_progress")
        
        # Configuration du spritesheet
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
        
    def load_frames(self):
        """Découpe le spritesheet en 240 frames individuelles (64x64 px chacune) et double la taille"""
        if not self.sprite:
            placeholder = pygame.Surface((self.frame_width * 2.5, self.frame_height * 2.5))
            placeholder.fill((255, 100, 255))
            return [placeholder]
        frames = []
        for row in range(self.rows):
            for col in range(self.columns):
                rect = pygame.Rect(col * self.frame_width, row * self.frame_height,
                                   self.frame_width, self.frame_height)
                frame = self.sprite.subsurface(rect)
                frame = pygame.transform.scale(frame, (self.frame_width * 2.5, self.frame_height * 2.5))
                frames.append(frame)
        return frames

    def load_animations(self):
        """Définit l'animation idle avec les 4 frames spécifiques"""
        # Idle = frames 191, 192, 193, 194
        return {
            "idle": [191, 192, 193, 194]
        }
    
    def update_animation(self, dt):
        self.frame_timer += dt
        if self.frame_timer >= self.frame_delay:
            self.frame_timer = 0
            animation_frames = self.animations.get(self.current_animation, [0])
            self.frame_index = (self.frame_index + 1) % len(animation_frames)
    
    def get_current_frame(self):
        if not self.frames:
            return None
        animation_frames = self.animations.get(self.current_animation, [0])
        if animation_frames:
            frame_id = animation_frames[self.frame_index]
            if 0 <= frame_id < len(self.frames):
                return self.frames[frame_id]
        return self.frames[0] if self.frames else None

    def speak(self):
        """Dialogue de base de Loopfang"""
        messages = [
            "Boucle ! Boucle ! Je suis Loopfang !",
            "for i in range(infini): print('Salut!')",
            "Tu veux apprendre les boucles ? C'est ma spécialité !",
            "while True: continue_to_learn()",
            "Attention aux boucles infinies, jeune codeur !"
        ]
        
        if not hasattr(self, 'dialog_state'):
            self.dialog_state = 0
            
        print(f"[DIALOG] {self.name} dit: {messages[self.dialog_state]}")
        self.dialog_state = (self.dialog_state + 1) % len(messages)
        
    def interact(self, session=None):
        """Interaction avec Loopfang"""
        if session:
            self.interact_with_session(session)
        else:
            self.speak()
            
    def interact_with_session(self, session):
        """Interaction avec accès à la session du joueur"""
        self.load_progress_from_session(session)
        
        messages = [
            "while apprentissage == True:",
            "    print('Bienvenue dans ma boucle récursive !')",
            "Les boucles for et while sont tes amies !",
            "Répéter du code, c'est mon domaine d'expertise.",
            "for conseil in mes_conseils: print(conseil)"
        ]
        
        if not hasattr(self, 'dialog_state'):
            self.dialog_state = 0
            
        print(f"[DIALOG] {self.name} dit: {messages[self.dialog_state]}")
        self.dialog_state = (self.dialog_state + 1) % len(messages)
        
        if session:
            session.set_progress(f"npc_{self.name.lower()}_talked", True)
            session.save_data()