# === game/combat_manager.py ===
import pygame
from game.character import Character
from enum import Enum
from core.ia import DameIndentaAI
from game.pnj.dame_indenta import DameIndenta
from game.world import World
from ui.uitools import BorderManager

class CombatState(Enum):
    PLAYER_TURN = "player_turn"
    ENEMY_TURN = "enemy_turn"
    VICTORY = "victory"
    DEFEAT = "defeat"

class CombatAction:
    """Action de combat avec bouton cliquable"""
    def __init__(self, name, description, action_func):
        self.name = name
        self.description = description
        self.action_func = action_func

class SimpleCombatManager:
    """Gestionnaire de combat simplifié pour les duels entres les differents pions"""
    
    def __init__(self, world_manager, screen):
        self.world_manager = world_manager
        self.screen = screen
        self.state = CombatState.PLAYER_TURN
        
        # Pions de combat (instances de Pion)
        self.player_pion = None
        self.enemy_pion = None
        
        # IA
        self.ai = DameIndentaAI("Dame Indenta", world_manager=self.world_manager)

        # Interface comme interaction.py
        self.is_active = False
        self.border_manager = BorderManager()
        self.font = pygame.font.Font(None, 32)
        self.action_buttons = []
        
        # Actions disponibles pour le joueur
        self.player_actions = [
            CombatAction("Move", "Se déplacer", self._handle_move_action),
            CombatAction("Attack", "Attaquer (buff)", self._handle_attack_action),
            CombatAction("Abandonner", "Quitter le combat", self._abandon_combat)
        ]
        
        print("[COMBAT] SimpleCombatManager initialisé")
    
    def start_combat(self, session):
        """Démarre le combat simplifié contre Dame Indenta"""
        print("[COMBAT] === DÉBUT DU COMBAT SIMPLIFIÉ ===")
        
        # Créer le pion du joueur
        grimoire = session.data.get('grimoire', {}) if session else {}
        self.player_pion = Character(session, self.world_manager)

        # Créer le pion de Dame Indenta
        self.enemy_pion = DameIndenta(self)

        # État initial
        self.state = CombatState.PLAYER_TURN
        self.is_active = True
        
        # Créer les boutons d'action
        self._create_action_buttons()
        
        print(f"[COMBAT] Combat démarré - {self.player_pion.name} vs {self.enemy_pion.name}")
        print(f"[COMBAT] Positions: Joueur({self.player_pion.combat_tile_x}, {self.player_pion.combat_tile_y}) vs Dame({self.enemy_pion.combat_tile_x}, {self.enemy_pion.combat_tile_y})")

    def _handle_move_action(self):
        """Gère l'action de mouvement du joueur"""
        if self.player_pion and self.player_pion.energie > 0:
            # TODO: Implémenter la sélection de tuile pour le mouvement
            print("[COMBAT] Mode sélection de mouvement activé")
            return None
        else:
            print("[COMBAT] Plus d'énergie pour se déplacer")
            self._end_player_turn()
            return None


    def _handle_attack_action(self):
        """Gère l'action d'attaque du joueur (buff sur soi-même)"""
        if self.player_pion and self.player_pion.can_attack(self.player_pion):
            success = self.player_pion.attack(self.player_pion)
            if success:
                print("[COMBAT] Joueur se donne un buff!")
                self._end_player_turn()
        return None
    
    def _end_player_turn(self):
        """Termine le tour du joueur"""
        if self.player_pion and self.player_pion.energie <= 0:
            print("[COMBAT] Plus d'énergie - Fin du tour joueur")
            self.state = CombatState.ENEMY_TURN
    
    def _create_action_buttons(self):
        """Crée les boutons d'action comme dans interaction.py"""
        self.action_buttons = []
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        
        button_width = 120
        button_height = 35
        button_spacing = 10
        
        # Calculer la position des boutons (en bas de l'écran)
        total_width = len(self.player_actions) * button_width + (len(self.player_actions) - 1) * button_spacing
        start_x = (screen_width - total_width) // 2
        button_y = screen_height - 60
        
        for i, action in enumerate(self.player_actions):
            button_x = start_x + i * (button_width + button_spacing)
            button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
            
            button_data = {
                'rect': button_rect,
                'action': action,
                'hovered': False
            }
            self.action_buttons.append(button_data)
    
    def update(self):
        """Met à jour la logique du combat"""
        if not self.is_active:
            return
            
        if self.state == CombatState.ENEMY_TURN:
            self._update_enemy_turn()
        
        # Vérifier les conditions de fin
        self._check_victory_conditions()
    
    def _update_enemy_turn(self):
        """Tour de Dame Indenta (IA surcheatée)"""
        print("[COMBAT] Tour de Dame Indenta")
        
        # L'IA utilise maintenant les pions
        action_type, target = self.ai.choose_action(self.enemy_pion, [self.player_pion])
        self.ai.execute_action(self.enemy_pion, action_type, target)
        
        # Retour au tour du joueur
        self.state = CombatState.PLAYER_TURN
        print("[COMBAT] Retour au tour du joueur")

    def _abandon_combat(self):
        """Abandonne le combat"""
        print("[COMBAT] Combat abandonné par le joueur")
        self.is_active = False
        return "end_combat"
    
    def _check_victory_conditions(self):
        """Vérifie les conditions de fin de combat"""
        if self.player_pion and not self.player_pion.is_alive:
            self.state = CombatState.DEFEAT
            print("[COMBAT] DÉFAITE!")
        elif self.enemy_pion and not self.enemy_pion.is_alive:
            self.state = CombatState.VICTORY
            print("[COMBAT] VICTOIRE!")
    
    def handle_event(self, event):
        """Gère les événements (comme interaction.py)"""
        if not self.is_active:
            return None
            
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            for button_data in self.action_buttons:
                if button_data['rect'].collidepoint(mouse_pos):
                    result = button_data['action'].action_func()
                    if result == "end_combat":
                        return "end_combat"
                    break
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return self._abandon_combat()
        
        return None
    
    def update_buttons(self, mouse_pos):
        """Met à jour l'état hover des boutons"""
        for button_data in self.action_buttons:
            button_data['hovered'] = button_data['rect'].collidepoint(mouse_pos)
    
    def draw(self, screen):
        """Affiche le combat avec interface comme interaction.py"""
        if not self.is_active:
            return
            
        # Fond semi-transparent
        overlay = pygame.Surface(screen.get_size())
        overlay.set_alpha(150)
        overlay.fill((20, 20, 40))
        screen.blit(overlay, (0, 0))
        
        # Dessiner les unités (pions)
        if self.player_pion:
            self._draw_pion(screen, self.player_pion)
        if self.enemy_pion:
            self._draw_pion(screen, self.enemy_pion)

        # Interface de combat
        self._draw_combat_ui(screen)
        
        # Boutons d'action avec bordures
        for button_data in self.action_buttons:
            self._draw_action_button(screen, button_data)
    
    def _draw_pion(self, surface, pion):
        # 1. Récupérer le sprite/image à dessiner
        sprite = pion.get_current_frame()  # ou pion.sprite_sheet/frame selon l’animation

        # 2. Convertir la position tuile en position pixel
        pixel_x, pixel_y = self.world_manager.tile_to_pixel(pion.combat_tile_x, pion.combat_tile_y)

        # 3. Dessiner le sprite sur la surface
        surface.blit(sprite, (pixel_x, pixel_y))
        # Nom des pions
        name_surf = self.font.render(str(pion.name), True, (255, 255, 255))
        name_rect = name_surf.get_rect(center=(pixel_x + 24, pixel_y - 15))
        surface.blit(name_surf, name_rect)

        # Barre de HP
        hp_ratio = pion.current_hp / pion.max_hp
        hp_width = int(48 * hp_ratio)
        hp_bg = pygame.Rect(pixel_x, pixel_y - 8, 48, 4)
        hp_fg = pygame.Rect(pixel_x, pixel_y - 8, hp_width, 4)
        pygame.draw.rect(surface, (100, 0, 0), hp_bg)
        pygame.draw.rect(surface, (0, 255, 0), hp_fg)

        # Affichage de l'énergie pour le joueur
        if hasattr(pion, 'energie'):
            energie_text = f"Énergie: {pion.energie}"
            energie_surf = pygame.font.Font(None, 20).render(energie_text, True, (255, 255, 0))
            surface.blit(energie_surf, (pixel_x, pixel_y + 70))
    
    def _draw_combat_ui(self, screen):
        """Dessine l'interface du combat"""
        # Titre du combat
        title = "Combat contre Dame Indenta"
        title_surf = self.font.render(title, True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(screen.get_width() // 2, 30))
        screen.blit(title_surf, title_rect)
        
        # État du combat
        state_text = f"Phase: {self.state.value}"
        if self.state == CombatState.DEFEAT:
            state_text = "DÉFAITE! Dame Indenta est trop puissante..."
        elif self.state == CombatState.VICTORY:
            state_text = "VICTOIRE! Impossible... vous avez vaincu Dame Indenta!"
            
        state_surf = self.font.render(state_text, True, (255, 255, 0))
        state_rect = state_surf.get_rect(center=(screen.get_width() // 2, 60))
        screen.blit(state_surf, state_rect)
        
        # Positions des pions
        if self.player_pion and self.enemy_pion:
            pos_text = f"Joueur: ({self.player_pion.combat_tile_x}, {self.player_pion.combat_tile_y}) | Dame Indenta: ({self.enemy_pion.combat_tile_x}, {self.enemy_pion.combat_tile_y})"
            pos_surf = pygame.font.Font(None, 24).render(pos_text, True, (200, 200, 200))
            screen.blit(pos_surf, (10, screen.get_height() - 100))
            
            # Affichage de l'énergie du joueur
            energie_text = f"Énergie du joueur: {self.player_pion.energie}"
            energie_surf = pygame.font.Font(None, 24).render(energie_text, True, (255, 255, 0))
            screen.blit(energie_surf, (10, screen.get_height() - 120))
    
    def _draw_action_button(self, screen, button_data):
        """Dessine un bouton d'action avec bordure"""
        rect = button_data['rect']
        action = button_data['action']
        hovered = button_data['hovered']
        
        # Couleur selon l'état
        bg_color = (80, 80, 120) if hovered else (50, 50, 80)
        
        # Fond du bouton
        pygame.draw.rect(screen, bg_color, rect)
        
        # Bordure avec BorderManager
        self.border_manager.draw_border(screen, rect, border_thickness=2)
        
        # Texte du bouton
        text_color = (255, 255, 255)
        text_surf = pygame.font.Font(None, 24).render(action.name, True, text_color)
        text_rect = text_surf.get_rect(center=rect.center)
        screen.blit(text_surf, text_rect)

# Rétrocompatibilité avec l'ancien système
CombatManager = SimpleCombatManager