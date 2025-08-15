import os
import pygame
from ui.uitools import BorderManager
from core.settings import FONTS

# Import du dispatcher de dialogue
from core.dialogue_dispatcher import DialogueDispatcher

class DialogueButton:
    """Classe pour les boutons de réponse dans les dialogues"""
    
    def __init__(self, text, action, rect):
        self.text = text
        self.action = action
        self.rect = rect
        self.hovered = False
        self.font = pygame.font.Font(FONTS["default"], 28)

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
    
    def __init__(self, screen_width=800, screen_height=600, session=None):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.is_active = False
        
        # Gestionnaire de bordures (utilise l'instance singleton)
        self.border_manager = BorderManager.get_instance(session)
        
        # Images de bustes
        self.character_bust = None
        self.npc_bust = None
        
        # Dialogue
        self.current_dialogue = ""
        
        # Boutons de réponse
        self.response_buttons = []
        
        # Polices
        self.dialogue_font = pygame.font.Font(FONTS['default'], 32)
        self.name_font = pygame.font.Font(FONTS['title'], 36)
        
        # Couleurs
        self.bg_color = (0, 0, 0, 180)  # Semi-transparent
        self.dialogue_bg = (40, 40, 60)
        self.text_color = (255, 255, 255)
        
        # Current NPC and character references
        self.current_npc = None
        self.current_character = None
        
        # Système d'arbre de dialogue
        self.dialogue_tree = None
        self.current_node = "start"
        
        # Dispatcher de dialogue depuis .twee
        self.dialogue_dispatcher = DialogueDispatcher()
        
        # Callback pour déclencher des actions spéciales (comme le combat)
        self.action_callback = None

        
    def start_interaction(self, character, npc, session=None):
        """
        Démarre une interaction avec un PNJ (nouvelle logique arbre de dialogue)
        """
        self.current_character = character
        self.current_npc = npc
        self.is_active = True
        
        # Charger les bustes
        self._load_character_busts(character, npc)
        
        # Construire l'arbre de dialogue pour ce PNJ
        self.dialogue_tree = self._build_dialogue_tree(npc, session)
        self.current_node = "start"
        
        # Afficher le dialogue initial
        self._set_dialogue_from_node()
        
        print(f"[INTERACTION] Dialogue démarré avec {npc.name}")

    def _build_dialogue_tree(self, npc, session):
        """Construit l'arbre de dialogue pour le PNJ donné en utilisant le dispatcher"""
        return self.dialogue_dispatcher.get_dialogue_tree_for_npc(npc.name, session)

    def _set_dialogue_from_node(self):
        """Met à jour le texte et les boutons selon le nœud courant de l'arbre de dialogue"""
        if not self.dialogue_tree or self.current_node not in self.dialogue_tree:
            self.current_dialogue = "..."
            self.response_buttons = []
            return
            
        node = self.dialogue_tree[self.current_node]
        self.current_dialogue = node["text"]
        
        # Créer les boutons de réponse
        self.response_buttons = []
        dialogue_rect = pygame.Rect(40, self.screen_height - 250, self.screen_width - 80, 200)
        button_width = 200
        button_height = 30
        button_spacing = 20
        
        responses = node["responses"]
        num_buttons = len(responses)
        total_width = num_buttons * button_width + (num_buttons - 1) * button_spacing
        start_x = dialogue_rect.left + (dialogue_rect.width - total_width) // 2
        button_y = self.screen_height - 53
        
        for i, resp in enumerate(responses):
            button_x = start_x + i * (button_width + button_spacing)
            button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
            button = DialogueButton(resp["label"], resp, button_rect)
            self.response_buttons.append(button)
        
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
        bust_path = f"data/{character.name.lower()}_bust.png"
        self.character_bust = load_bust(bust_path, (255, 100, 100))
        bust_path = getattr(npc, 'bust_path', None)
        self.npc_bust = load_bust(bust_path, (100, 100, 255))
            
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
        
    def _handle_button_action(self, resp):
        """Gère l'action d'un bouton de réponse (arbre de dialogue)"""
        if "action" in resp:
            if resp["action"] == "end":
                self.end_interaction()
                return "end"
            elif resp["action"] == "start_combat":
                print("[INTERACTION] Déclenchement du combat générique!")
                if self.action_callback:
                    self.action_callback("start_combat")
                self.end_interaction()
                return "start_combat"
            elif resp["action"] == "start_combat_with_dame_indenta":
                print("[INTERACTION] Déclenchement du combat contre Dame Indenta!")
                if self.action_callback:
                    self.action_callback("start_combat_dame_indenta")
                self.end_interaction()
                return "start_combat"
            elif resp["action"] == "quest_info":
                # Affiche les informations d'une quête
                quest_code = resp.get("quest_info")
                if quest_code:
                    self._show_quest_info(quest_code)
                return "continue"
            elif resp["action"] == "back_to_dialogue":
                # Retour au dialogue principal depuis l'info quête
                self._set_dialogue_from_node()
                return "continue"
            # Ajouter d'autres actions ici si besoin
        elif "next" in resp:
            # Naviguer vers un autre nœud de l'arbre
            self.current_node = resp["next"]
            self._set_dialogue_from_node()
            return "continue"
        return None
    
    def _show_quest_info(self, quest_code):
        """Affiche les informations détaillées d'une quête"""
        from core.quest import QUESTS, NEW_QUESTS, SECRET_QUESTS
        
        # Trouve la quête correspondante
        quest_obj = None
        for quest in QUESTS + NEW_QUESTS + SECRET_QUESTS:
            if quest.code == quest_code:
                quest_obj = quest
                break
        
        if quest_obj:
            # Crée un dialogue temporaire avec les informations de la quête
            info_text = f"Quête: {quest_obj.nom}\n\nDescription: {quest_obj.description}"
            self.current_dialogue = info_text
            
            # Bouton de retour
            self.response_buttons = []
            dialogue_rect = pygame.Rect(40, self.screen_height - 250, self.screen_width - 80, 200)
            button_rect = pygame.Rect(dialogue_rect.centerx - 50, self.screen_height - 53, 100, 30)
            
            back_response = {"label": "Retour", "action": "back_to_dialogue"}
            button = DialogueButton("Retour", back_response, button_rect)
            self.response_buttons.append(button)
            
            print(f"[INTERACTION] Affichage info quête: {quest_code} - {quest_obj.nom}")
        else:
            print(f"[INTERACTION] Quête introuvable: {quest_code}")
        
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