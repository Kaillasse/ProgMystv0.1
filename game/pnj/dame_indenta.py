import pygame


class DameIndenta:
    def __init__(self, name="Dame Indenta", sprite_path="assets/pnj/di/di_sprite.png", bust_path="assets/pnj/di/di_bust.png",
                 start_tile=(4, 8), combat_start_tile=(2, 2)):
        self.name = name
        self.sprite_path = sprite_path
        self.bust_path = bust_path
        self.map_name = "clairiere"
        self.start_tile = start_tile
        self.combat_tile_x = combat_start_tile[0]  # Position pour le mode combat
        self.combat_tile_y = combat_start_tile[1]  # Position pour le mode combat
        self.tile_pos = list(self.start_tile)
        self.quest_progress_key = "dame_indenta_progress"
        self.dialog_state = 0
        self.has_given_quests = False
        self.sprite = self._load_image(self.sprite_path)
        self.bust = self._load_image(self.bust_path)
        
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
        self.current_hp = 2
        self.max_hp = 2
        self.current_frame = 0

    @property
    def is_alive(self):
        return self.current_hp > 0

    def _load_image(self, path):
        if path:
            try:
                return pygame.image.load(path).convert_alpha()
            except FileNotFoundError:
                print(f"[PNJ] ATTENTION: Impossible de charger l'image {path}")
        return None
           
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
        return {
            "idle_front": [1], "idle_left": [13], "idle_right": [25], "idle_back": [37],
            "idle_frontright": [16], "idle_frontleft": [4], "idle_backleft": [28], "idle_backright": [40],
            "walk_front": [0, 2], "walk_left": [12, 14], "walk_right": [24, 26], "walk_back": [36, 38],
            "walk_frontright": [15, 17], "walk_frontleft": [3, 5], "walk_backright": [39, 41], "walk_backleft": [27, 29]
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

    def move(self, dx, dy):
        """Déplace Dame Indenta sur la grille de combat"""
        self.combat_start_tile = (self.combat_start_tile[0] + dx, self.combat_start_tile[1] + dy)
        return True
    
    def attack(self, target):
        """Dame Indenta attaque une cible"""
        if hasattr(target, "current_hp"):
            damage = 3  # Dame Indenta inflige 3 dégâts
            target.current_hp = max(0, target.current_hp - damage)
            print(f"[COMBAT] Dame Indenta attaque {target.name if hasattr(target, 'name') else 'cible'} pour {damage} dégâts!")
            return True
        return False
    
# Exemple d'arbre de dialogue pour Dame Indenta (à placer à la fin de la classe DameIndenta)
# Chaque clé est un noeud, chaque valeur contient le texte et 3 réponses possibles
dame_indenta_dialogue_tree = {
    "start": {
        "text": "Hmm alors c'est toi le nouvel apprenti ! Que veux-tu faire ?",
        "responses": [
            {"label": "Où suis-je ?", "next": "talk1"},
            {"label": "Battons-nous !", "action": "start_combat_with_dame_indenta"},
            {"label": "Quitter", "action": "end"}
        ]
    },
    "quest1": {
        "text": "Voici ta première quête : Utilise deux variables et affiche-les avec print().",
        "responses": [
            {"label": "Merci !", "next": "start"},
            {"label": "Une autre quête", "next": "quest2"},
            {"label": "Fermer", "action": "end"}
        ]
    },
    "quest2": {
        "text": "Deuxième quête : Utilise input() pour demander le nom de l'utilisateur.",
        "responses": [
            {"label": "Merci Dame Indenta", "next": "start"},
            {"label": "Encore une !", "next": "quest3"},
            {"label": "C'est tout", "action": "end"}
        ]
    },
    "quest3": {
        "text": "Troisième quête : Utilise une condition if pour afficher un message spécial.",
        "responses": [
            {"label": "Retour", "next": "start"},
            {"label": "Merci", "action": "end"},
            {"label": "Plus tard", "action": "end"}
        ]
    },
    "talk1": {
        "text": "La programmation est une aventure ! As-tu des questions ?",
        "responses": [
            {"label": "Comment progresser ?", "next": "tip1"},
            {"label": "Pourquoi Python ?", "next": "tip2"},
            {"label": "Au revoir", "action": "end"}
        ]
    },
    "tip1": {
        "text": "Pratique chaque jour et relève les défis !",
        "responses": [
            {"label": "Merci", "next": "start"},
            {"label": "Un autre conseil", "next": "tip2"},
            {"label": "Fermer", "action": "end"}
        ]
    },
    "tip2": {
        "text": "Python est simple et puissant, parfait pour débuter !",
        "responses": [
            {"label": "Retour", "next": "start"},
            {"label": "Merci", "action": "end"},
            {"label": "Plus tard", "action": "end"}
        ]
    },
}
