import os
import pygame
from ui.uitools import BorderManager

class DialogueButton:
    """Classe pour les boutons de réponse dans les dialogues"""
    
    def __init__(self, text, action, rect):
        self.text = text
        self.action = action
        self.rect = rect
        self.hovered = False
        self.font = pygame.font.Font(None, 28)
        
    def update(self, mouse_pos):
        """Met à jour l'état hover du bouton"""
        self.hovered = self.rect.collidepoint(mouse_pos)
        
    def draw(self, screen):
        """Dessine le bouton"""
        # Couleur selon l'état
        bg_color = (100, 100, 150) if self.hovered else (60, 60, 100)
        border_color = (150, 150, 200) if self.hovered else (100, 100, 150)
        
        # Fond du bouton
        pygame.draw.rect(screen, bg_color, self.rect)
        pygame.draw.rect(screen, border_color, self.rect, 2)
        
        # Texte du bouton
        text_color = (255, 255, 255)
        text_surface = self.font.render(self.text, True, text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
        
    def is_clicked(self, mouse_pos):
        """Vérifie si le bouton est cliqué"""
        return self.rect.collidepoint(mouse_pos)

class InteractionUI:
    """Interface utilisateur pour les dialogues entre le joueur et les PNJ"""
    
    def __init__(self, screen_width=800, screen_height=600):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.is_active = False
        
        # Gestionnaire de bordures
        self.border_manager = BorderManager()
        
        # Images de bustes
        self.character_bust = None
        self.npc_bust = None
        
        # Dialogue
        self.current_dialogue = ""
        
        # Boutons de réponse
        self.response_buttons = []
        
        # Polices
        self.dialogue_font = pygame.font.Font(None, 32)
        self.name_font = pygame.font.Font(None, 36)
        
        # Couleurs
        self.bg_color = (0, 0, 0, 180)  # Semi-transparent
        self.dialogue_bg = (40, 40, 60)
        self.text_color = (255, 255, 255)
        
        # Current NPC and character references
        self.current_npc = None
        self.current_character = None

        
    def start_interaction(self, character, npc, session=None):
        """
        Démarre une interaction avec un PNJ
        
        Args:
            character: Instance du personnage joueur
            npc: Instance du PNJ
            session: Session du joueur (optionnelle)
        """
        self.current_character = character
        self.current_npc = npc
        self.is_active = True
        
        # Charger les bustes
        self._load_character_busts(character, npc)
        
        # Obtenir le dialogue du PNJ
        self._get_npc_dialogue(npc, session)
        
        # Créer les boutons de réponse
        self._create_response_buttons()
        
        print(f"[INTERACTION] Dialogue démarré avec {npc.name}")
        
    def _load_character_busts(self, character, npc):
        """Charge les images de bustes des personnages, retourne une surface de secours si besoin"""
        def load_bust(path, fallback_color):
            if path and os.path.exists(path):
                try:
                    return pygame.image.load(path).convert_alpha()
                except pygame.error:
                    pass
            surf = pygame.Surface((150, 200))
            surf.fill(fallback_color)
            return surf
        self.character_bust = load_bust("data/thib_bust.png", (255, 100, 100))
        bust_path = getattr(npc, 'bust_path', None)
        self.npc_bust = load_bust(bust_path, (100, 100, 255))
        
    def _get_npc_dialogue(self, npc, session):
        """Récupère le dialogue du PNJ"""
        if hasattr(npc, 'interact') and session:
            if npc.name == "Dame Indenta":
                self._get_dame_indenta_dialogue(npc, session)
            elif npc.name == "Neuill":
                self._get_neuill_dialogue(npc, session)
            elif npc.name == "JSON":
                self._get_json_dialogue(npc, session)
            elif npc.name == "Loopfang":
                self._get_loopfang_dialogue(npc, session)
            else:
                self.current_dialogue = f"{npc.name} vous salue."
        elif hasattr(npc, 'dialogues') and npc.dialogues:
            self.current_dialogue = npc.dialogues[0]
        else:
            self.current_dialogue = f"{npc.name} vous salue." if hasattr(npc, 'name') else "Ce PNJ reste silencieux..."
                
    def _get_dame_indenta_dialogue(self, dame_indenta, session):
        """Gère le dialogue spécifique de Dame Indenta"""
        # Charger la progression
        dame_indenta.load_progress_from_session(session)
        
        if not dame_indenta.has_given_quests:
            # Première interaction - donner les quêtes
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
            self.current_dialogue = messages[dame_indenta.dialog_state]
        else:
            # Vérifier les quêtes complétées
            completed = dame_indenta.check_quests(session.name)
            
            if completed is None:
                self.current_dialogue = "Je ne trouve pas ton grimoire dans le dossier des étudiants..."
            else:
                quest_codes = ['#Q1', '#Q2', '#Q3', '#Q4', '#Q5']
                completed_now = [q for q in quest_codes if q in completed]
                
                if completed_now:
                    completion_count = len(completed_now)
                    self.current_dialogue = f"Excellent ! Tu as accompli {completion_count} de mes quêtes. Continue ainsi !"
                else:
                    self.current_dialogue = "Continue à travailler sur ton grimoire. Je sens que tu es sur la bonne voie !"
                    
    def _get_neuill_dialogue(self, neuill, session):
        """Gère le dialogue spécifique de Neuill"""
        neuill.load_progress_from_session(session)
        
        messages = [
            "Bienvenue dans ma clairière, jeune codeur !",
            "Je vois que tu explores le monde de Progmyst.",
            "As-tu déjà rencontré Dame Indenta ? Elle donne d'excellentes quêtes !",
            "Continue à explorer, chaque zone a ses secrets.",
            "Reviens me voir quand tu auras progressé !"
        ]
        
        if not hasattr(neuill, 'dialog_state'):
            neuill.dialog_state = 0
            
        self.current_dialogue = messages[neuill.dialog_state % len(messages)]
        
    def _get_json_dialogue(self, json_npc, session):
        """Gère le dialogue spécifique de JSON"""
        json_npc.load_progress_from_session(session)
        
        messages = [
            "{ \"greeting\": \"Salut, codeur !\" }",
            "Je vois que tu explores le monde des données.",
            "Bientôt tu apprendras les dictionnaires et les listes !",
            "Mes clés et valeurs t'aideront à organiser tes informations.",
            "{ \"motivation\": \"Continue à coder !\" }"
        ]
        
        if not hasattr(json_npc, 'dialog_state'):
            json_npc.dialog_state = 0
            
        self.current_dialogue = messages[json_npc.dialog_state % len(messages)]
        
    def _get_loopfang_dialogue(self, loopfang, session):
        """Gère le dialogue spécifique de Loopfang"""
        loopfang.load_progress_from_session(session)
        
        messages = [
            "while apprentissage == True:",
            "    print('Bienvenue dans ma boucle récursive !')",
            "Les boucles for et while sont tes amies !",
            "Répéter du code, c'est mon domaine d'expertise.",
            "for conseil in mes_conseils: print(conseil)"
        ]
        
        if not hasattr(loopfang, 'dialog_state'):
            loopfang.dialog_state = 0
            
        self.current_dialogue = messages[loopfang.dialog_state % len(messages)]
                    
    def _create_response_buttons(self):
        """Crée les boutons de réponse centrés dans la boîte de dialogue"""
        self.response_buttons = []

        # Dimensions de la boîte de dialogue
        dialogue_rect = pygame.Rect(40, self.screen_height - 250, self.screen_width - 80, 200)
        button_width = 200
        button_height = 30
        button_spacing = 20
        responses = [
            ("Continuer", "next"),
            ("En savoir plus", "more"),
            ("Terminer", "end")
        ]
        num_buttons = len(responses)
        total_width = num_buttons * button_width + (num_buttons - 1) * button_spacing
        start_x = dialogue_rect.left + (dialogue_rect.width - total_width) // 2
        button_y = self.screen_height - 53

        for i, (text, action) in enumerate(responses):
            button_x = start_x + i * (button_width + button_spacing)
            button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
            button = DialogueButton(text, action, button_rect)
            self.response_buttons.append(button)
            
    def update(self, mouse_pos):
        """Met à jour l'interface"""
        if not self.is_active:
            return
            
        # Mettre à jour les boutons
        for button in self.response_buttons:
            button.update(mouse_pos)
            
    def handle_event(self, event):
        """
        Gère les événements utilisateur
        
        Args:
            event: Événement pygame
            
        Returns:
            str: Action à effectuer ("continue", "end", etc.) ou None
        """
        if not self.is_active:
            return None
            
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Clic gauche
            for button in self.response_buttons:
                if button.is_clicked(event.pos):
                    return self._handle_button_action(button.action)
                    
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "end"
            elif event.key == pygame.K_b:
                # Changer de bordure avec la touche B
                self.border_manager.next_border()
                return None
                
        return None
        
    def _handle_button_action(self, action):
        """Gère l'action d'un bouton"""
        if action == "next":
            # Avancer dans le dialogue si applicable
            if hasattr(self.current_npc, 'dialog_state'):
                self.current_npc.dialog_state += 1
            return "continue"
        elif action == "more":
            # Demander plus d'informations
            return "more"
        elif action == "end":
            # Terminer le dialogue
            self.end_interaction()
            return "end"
        return None
        
    def render(self, screen):
        """
        Affiche l'interface de dialogue avec bordures texturées
        
        Args:
            screen: Surface pygame où dessiner
        """
        if not self.is_active:
            return
            
        # Fond semi-transparent
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        # Fenêtre de dialogue principale
        dialogue_rect = pygame.Rect(50, self.screen_height - 200, self.screen_width - 100, 150)
        
        # Fond de la fenêtre de dialogue
        pygame.draw.rect(screen, self.dialogue_bg, dialogue_rect)
        
        # Bordure texturée autour de la fenêtre de dialogue
        self.border_manager.draw_border(screen, dialogue_rect, border_thickness=15)
        
        # Bustes des personnages
        if self.character_bust:
            # Buste joueur à gauche
            bust_rect = self.character_bust.get_rect()
            bust_rect.bottomleft = (-100, self.screen_height - 220)
            flipped_bust = pygame.transform.flip(self.character_bust, True, False)
            screen.blit(flipped_bust, bust_rect)

        if self.npc_bust:
            # Buste PNJ à droite
            bust_rect = self.npc_bust.get_rect()
            bust_rect.bottomright = (self.screen_width + 100, self.screen_height - 220)
            screen.blit(self.npc_bust, bust_rect)
            
        # Nom du PNJ
        if self.current_npc:
            name_surface = self.name_font.render(self.current_npc.name, True, (255, 255, 100))
            name_rect = name_surface.get_rect()
            name_rect.topleft = (dialogue_rect.left + 10, dialogue_rect.top + 5)
            screen.blit(name_surface, name_rect)
            
        # Texte du dialogue
        self._render_dialogue_text(screen, dialogue_rect)
        
        # Boutons de réponse avec bordures texturées
        for button in self.response_buttons:
            # Dessiner la bordure texturée autour du bouton
            self.border_manager.draw_border(screen, button.rect, border_thickness=5)
            button.draw(screen)
            
        # Afficher l'indicateur de bordure actuelle
        border_info = f"Bordure: {self.border_manager.current_border_index + 1}/80 (Appuyez sur B pour changer)"
        info_surface = pygame.font.Font(None, 24).render(border_info, True, (200, 200, 200))
        screen.blit(info_surface, (10, 10))
            
    def _render_dialogue_text(self, screen, dialogue_rect):
        """Affiche le texte du dialogue avec retour à la ligne"""
        if not self.current_dialogue:
            return
        text_rect = pygame.Rect(
            dialogue_rect.left + 10,
            dialogue_rect.top + 40,
            dialogue_rect.width - 20,
            dialogue_rect.height - 50
        )
        words = self.current_dialogue.split(' ')
        lines, current_line = [], ""
        font = self.dialogue_font
        for word in words:
            test_line = current_line + word + " "
            if font.render(test_line, True, self.text_color).get_width() <= text_rect.width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line.rstrip())
                current_line = word + " "
        if current_line:
            lines.append(current_line.rstrip())
        line_height = font.get_height() + 2
        for i, line in enumerate(lines):
            if (i + 1) * line_height > text_rect.height:
                break
            line_surface = font.render(line, True, self.text_color)
            screen.blit(line_surface, (text_rect.left, text_rect.top + i * line_height))
            
    def end_interaction(self):
        """Termine l'interaction"""
        self.is_active = False
        self.current_npc = None
        self.current_character = None
        self.current_dialogue = ""
        self.response_buttons = []
        print("[INTERACTION] Dialogue terminé")