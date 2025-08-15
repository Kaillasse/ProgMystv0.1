import pygame
from core.quest import QUESTS, NEW_QUESTS, SECRET_QUESTS
from core.session import SessionManager
from core.quest_analyzer import QuestAnalyzer
from ui.uitools import QuestStar, BorderManager
from core.settings import FONTS


class QuestTable:
    """Interface de table des quêtes avec animations et descriptions détaillées"""
    
    def __init__(self, screen_width=800, screen_height=600, session=None):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.session = session
        self.is_active = False
        
        # Gestionnaire de bordures (utilise l'instance singleton)
        self.border_manager = BorderManager.get_instance(session)
        
        # Analyseur de quêtes
        self.quest_analyzer = QuestAnalyzer(session) if session else None
        
        # Interface
        self.scroll_offset = 0
        self.max_visible_quests = 12
        self.quest_height = 40
        self.expanded_quest = None  # Quête actuellement expanded
        
        # Police
        self.quest_font = pygame.font.Font(FONTS['default'], 20)
        self.desc_font = pygame.font.Font(FONTS['default'], 16)
        self.title_font = pygame.font.Font(FONTS['title'], 24)
        
        # Couleurs
        self.bg_color = (20, 20, 40)
        self.text_color = (255, 255, 255)
        self.completed_color = (100, 255, 100)
        self.given_color = (255, 255, 100)
        self.desc_bg_color = (40, 40, 80)
        
        # Animations d'étoiles pour chaque type de quête
        self.quest_stars = {}
        
        # Données des quêtes
        self.quest_data = []
        self.load_quest_data()
    
    def load_quest_data(self):
        """Charge les données des quêtes depuis l'analyseur"""
        if not self.quest_analyzer:
            return
        
        self.quest_data = self.quest_analyzer.get_given_quests()
        print(f"[QUEST_TABLE] Chargé {len(self.quest_data)} quêtes données")
    
    def show(self):
        """Affiche la table des quêtes"""
        self.is_active = True
        self.load_quest_data()
        
        # Analyse du grimoire à l'ouverture
        if self.quest_analyzer:
            newly_completed = self.quest_analyzer.analyze_grimoire()
            if newly_completed:
                print(f"[QUEST_TABLE] Nouvelles quêtes accomplies détectées: {newly_completed}")
                self.load_quest_data()  # Recharge après analyse
    
    def hide(self):
        """Cache la table des quêtes"""
        self.is_active = False
        self.expanded_quest = None
    
    def handle_event(self, event):
        """Gère les événements utilisateur"""
        if not self.is_active:
            return None
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.hide()
                return "close"
            elif event.key == pygame.K_UP:
                self.scroll_offset = max(0, self.scroll_offset - 1)
            elif event.key == pygame.K_DOWN:
                max_scroll = max(0, len(self.quest_data) - self.max_visible_quests)
                self.scroll_offset = min(max_scroll, self.scroll_offset + 1)
            elif event.key == pygame.K_b:
                # Changer de bordure avec B
                self.border_manager.next_border()
        
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Clic sur une quête pour l'expand/collapse
            mouse_x, mouse_y = event.pos
            quest_index = self._get_quest_at_position(mouse_x, mouse_y)
            
            if quest_index is not None and quest_index < len(self.quest_data):
                quest_code = self.quest_data[quest_index]['code']
                
                # Toggle l'expansion
                if self.expanded_quest == quest_code:
                    self.expanded_quest = None
                else:
                    self.expanded_quest = quest_code
                
                return "quest_clicked"
        
        elif event.type == pygame.MOUSEWHEEL:
            # Scroll avec la molette
            if event.y > 0:  # Scroll up
                self.scroll_offset = max(0, self.scroll_offset - 1)
            else:  # Scroll down
                max_scroll = max(0, len(self.quest_data) - self.max_visible_quests)
                self.scroll_offset = min(max_scroll, self.scroll_offset + 1)
        
        return None
    
    def _get_quest_at_position(self, mouse_x, mouse_y):
        """Retourne l'index de la quête à la position de la souris"""
        quest_area_rect = pygame.Rect(50, 100, self.screen_width - 100, 
                                    self.max_visible_quests * self.quest_height)
        
        if not quest_area_rect.collidepoint(mouse_x, mouse_y):
            return None
        
        # Calcule l'index relatif dans la zone visible
        relative_y = mouse_y - quest_area_rect.y
        quest_index = relative_y // self.quest_height + self.scroll_offset
        
        return quest_index if quest_index < len(self.quest_data) else None
    
    def _get_quest_star_type(self, quest_code, completed):
        """Retourne le type d'étoile pour une quête"""
        if completed:
            # Détermine le type selon le code de la quête
            if quest_code.startswith('#S'):
                return 'secretquest'
            elif quest_code.startswith('#Q') and int(quest_code[2:]) > 30:
                return 'newquest'
            else:
                return 'quest'
        else:
            return 'uncompleted'
    
    def render(self, screen, dt):
        """Affiche la table des quêtes"""
        if not self.is_active:
            return
        
        # Fond semi-transparent
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(180)
        overlay.fill(self.bg_color)
        screen.blit(overlay, (0, 0))
        
        # Fenêtre principale
        main_rect = pygame.Rect(40, 40, self.screen_width - 80, self.screen_height - 80)
        pygame.draw.rect(screen, (60, 60, 100), main_rect)
        self.border_manager.draw_border(screen, main_rect, border_thickness=10)
        
        # Titre
        title = "Table des Quêtes"
        title_surface = self.title_font.render(title, True, self.text_color)
        title_rect = title_surface.get_rect()
        title_rect.centerx = main_rect.centerx
        title_rect.y = main_rect.y + 15
        screen.blit(title_surface, title_rect)
        
        # Statistiques
        total_quests = len(self.quest_data)
        completed_count = sum(1 for q in self.quest_data if q['completed'])
        stats_text = f"Quêtes: {completed_count}/{total_quests} accomplies"
        stats_surface = self.desc_font.render(stats_text, True, self.text_color)
        stats_rect = stats_surface.get_rect()
        stats_rect.centerx = main_rect.centerx
        stats_rect.y = title_rect.bottom + 5
        screen.blit(stats_surface, stats_rect)
        
        # Zone de quêtes
        quest_area_rect = pygame.Rect(main_rect.x + 10, main_rect.y + 80, 
                                    main_rect.width - 20, main_rect.height - 120)
        
        # Scrollbar si nécessaire
        if len(self.quest_data) > self.max_visible_quests:
            self._draw_scrollbar(screen, quest_area_rect)
        
        # Affiche les quêtes visibles
        self._render_quest_list(screen, quest_area_rect, dt)
        
        # Instructions
        instructions = "↑↓: Naviguer | Clic: Détails | B: Bordure | Échap: Fermer"
        inst_surface = self.desc_font.render(instructions, True, (200, 200, 200))
        inst_rect = inst_surface.get_rect()
        inst_rect.centerx = main_rect.centerx
        inst_rect.bottom = main_rect.bottom - 10
        screen.blit(inst_surface, inst_rect)
    
    def _render_quest_list(self, screen, quest_area_rect, dt):
        """Affiche la liste des quêtes avec animations"""
        visible_quests = self.quest_data[self.scroll_offset:self.scroll_offset + self.max_visible_quests]
        
        current_y = quest_area_rect.y
        
        for i, quest in enumerate(visible_quests):
            quest_code = quest['code']
            quest_name = quest['name']
            quest_desc = quest['description']
            completed = quest['completed']
            
            # Rectangle de la quête
            quest_rect = pygame.Rect(quest_area_rect.x, current_y, 
                                   quest_area_rect.width, self.quest_height)
            
            # Couleur de fond selon le statut
            bg_color = self.completed_color if completed else self.given_color
            bg_color = (bg_color[0] // 4, bg_color[1] // 4, bg_color[2] // 4)  # Plus sombre
            
            pygame.draw.rect(screen, bg_color, quest_rect)
            self.border_manager.draw_border(screen, quest_rect, border_thickness=2)
            
            # Animation d'étoile
            star_type = self._get_quest_star_type(quest_code, completed)
            
            if quest_code not in self.quest_stars:
                self.quest_stars[quest_code] = QuestStar(quest_rect.x + 5, quest_rect.y + 4, star_type)
            
            star = self.quest_stars[quest_code]
            star.set_position(quest_rect.x + 5, quest_rect.y + 4)
            star.update(dt)
            star.draw(screen)
            
            # Texte de la quête
            text_x = quest_rect.x + 45  # Après l'étoile
            text_y = quest_rect.y + (quest_rect.height - self.quest_font.get_height()) // 2
            
            text_color = self.completed_color if completed else self.given_color
            
            # Code de la quête
            code_surface = self.quest_font.render(quest_code, True, text_color)
            screen.blit(code_surface, (text_x, text_y))
            
            # Nom de la quête
            name_surface = self.quest_font.render(quest_name, True, self.text_color)
            screen.blit(name_surface, (text_x + 70, text_y))
            
            # Statut
            status_text = "✓" if completed else "○"
            status_surface = self.quest_font.render(status_text, True, text_color)
            status_rect = status_surface.get_rect()
            status_rect.right = quest_rect.right - 10
            status_rect.centery = quest_rect.centery
            screen.blit(status_surface, status_rect)
            
            current_y += self.quest_height
            
            # Description expandée si cette quête est sélectionnée
            if self.expanded_quest == quest_code:
                desc_height = self._render_expanded_description(screen, quest_area_rect, 
                                                              current_y, quest_desc)
                current_y += desc_height
    
    def _render_expanded_description(self, screen, area_rect, y_pos, description):
        """Affiche la description expandée d'une quête"""
        desc_rect = pygame.Rect(area_rect.x + 20, y_pos, 
                              area_rect.width - 40, 60)
        
        # Fond de la description
        pygame.draw.rect(screen, self.desc_bg_color, desc_rect)
        self.border_manager.draw_border(screen, desc_rect, border_thickness=3)
        
        # Texte de description avec retour à la ligne
        words = description.split(' ')
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + word + " "
            if self.desc_font.size(test_line)[0] <= desc_rect.width - 20:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line.strip())
                current_line = word + " "
        
        if current_line:
            lines.append(current_line.strip())
        
        # Affiche les lignes
        line_height = self.desc_font.get_height() + 2
        text_y = desc_rect.y + 10
        
        for line in lines[:3]:  # Maximum 3 lignes
            line_surface = self.desc_font.render(line, True, self.text_color)
            screen.blit(line_surface, (desc_rect.x + 10, text_y))
            text_y += line_height
        
        return desc_rect.height
    
    def _draw_scrollbar(self, screen, quest_area_rect):
        """Dessine une scrollbar simple"""
        scrollbar_rect = pygame.Rect(quest_area_rect.right + 5, quest_area_rect.y, 
                                   10, quest_area_rect.height)
        
        # Fond de la scrollbar
        pygame.draw.rect(screen, (100, 100, 100), scrollbar_rect)
        
        # Position du thumb
        if len(self.quest_data) > 0:
            thumb_height = max(20, scrollbar_rect.height * self.max_visible_quests // len(self.quest_data))
            thumb_y = scrollbar_rect.y + (scrollbar_rect.height - thumb_height) * self.scroll_offset // max(1, len(self.quest_data) - self.max_visible_quests)
            
            thumb_rect = pygame.Rect(scrollbar_rect.x, thumb_y, scrollbar_rect.width, thumb_height)
            pygame.draw.rect(screen, (200, 200, 200), thumb_rect)


# Fonctions de compatibilité avec l'ancien système
def get_player_quests(player):
    """Fonction de compatibilité - retourne les quêtes du joueur"""
    session = SessionManager.get_current_session()
    if not session:
        return {"active": [], "completed": []}
    
    analyzer = QuestAnalyzer(session)
    given_quests = analyzer.get_given_quests()
    
    return {
        "active": [q for q in given_quests if not q['completed']],
        "completed": [q for q in given_quests if q['completed']]
    }