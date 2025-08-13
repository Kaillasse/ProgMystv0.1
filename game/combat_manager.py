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
# Dans combat_manager.py
class CombatEntity:
    """Mixin pour les capacités de combat"""
    def prepare_for_combat(self):
        """Prépare l'entité pour le combat"""
        pass
        
    def get_combat_actions(self):
        """Retourne les actions disponibles en combat"""
        return []
        
    def execute_action(self, action, target):
        """Exécute une action de combat"""
        pass

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
        self.border_manager = None  # Sera initialisé dans start_combat avec session
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
        """Démarre le combat avec synchronisation unifiée via World"""
        print("[COMBAT] === DÉBUT DU COMBAT SIMPLIFIÉ ===")
        
        # Initialiser BorderManager avec la session
        if not self.border_manager:
            self.border_manager = BorderManager(session=session)
        
        self.player_pion = Character(session, self.world_manager)
        self.enemy_pion = DameIndenta(self)
        entities = [self.player_pion, self.enemy_pion]
        
        # UTILISATION API UNIFIÉE DE WORLD
        self.world_manager.sync_combat_positions(entities)
        self.world_manager.validate_entity_positions(entities)
        
        self.state = CombatState.PLAYER_TURN
        self.is_active = True
        self._create_action_buttons()
        print(f"[COMBAT] Combat démarré - {self.player_pion.name} vs {self.enemy_pion.name}")

    def _handle_move_action(self):
        """Gère l'action de mouvement du joueur"""
        if self.player_pion and self.player_pion.energie > 0:
            print("[COMBAT] Mode sélection de mouvement activé")
        else:
            print("[COMBAT] Plus d'énergie pour se déplacer")
            self._end_player_turn()
        return None


    def _handle_attack_action(self):
        """Gère l'action d'attaque du joueur (buff sur soi-même)"""
        if self.player_pion and hasattr(self.player_pion, 'can_attack') and self.player_pion.can_attack(self.player_pion):
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
        """Crée les boutons d'action"""
        self.action_buttons = []
        w, h = self.screen.get_width(), self.screen.get_height()
        bw, bh, bs = 120, 35, 10
        total_w = len(self.player_actions) * bw + (len(self.player_actions) - 1) * bs
        start_x = (w - total_w) // 2
        y = h - 60
        for i, action in enumerate(self.player_actions):
            rect = pygame.Rect(start_x + i * (bw + bs), y, bw, bh)
            self.action_buttons.append({'rect': rect, 'action': action, 'hovered': False})
    
    def update(self):
        """Met à jour la logique du combat"""
        if not self.is_active:
            return
        if self.state == CombatState.ENEMY_TURN:
            self._update_enemy_turn()
        self._check_victory_conditions()
    
    def _update_enemy_turn(self):
        """Tour de Dame Indenta (IA)"""
        print("[COMBAT] Tour de Dame Indenta")
        action_type, target = self.ai.choose_action(self.enemy_pion, [self.player_pion])
        self.ai.execute_action(self.enemy_pion, action_type, target)
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
        """Gère les événements (clics et touches)"""
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
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return self._abandon_combat()
        return None
    
    def update_buttons(self, mouse_pos):
        """Met à jour l'état hover des boutons"""
        for button_data in self.action_buttons:
            button_data['hovered'] = button_data['rect'].collidepoint(mouse_pos)
    
    def draw(self, screen):
        """Affiche le combat et l'interface"""
        if not self.is_active:
            return
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((20, 20, 40, 150))
        screen.blit(overlay, (0, 0))
        if self.player_pion:
            self._draw_pion(screen, self.player_pion)
        if self.enemy_pion:
            self._draw_pion(screen, self.enemy_pion)
        self._draw_combat_ui(screen)
        for button_data in self.action_buttons:
            self._draw_action_button(screen, button_data)
    
    def _draw_pion(self, surface, pion):
        # 1. Récupérer le sprite/image à dessiner
        sprite = pion.get_current_frame()  # ou pion.sprite_sheet/frame selon l’animation

        # 2. NOUVELLE API UNIFIÉE : utiliser get_entity_pixel_pos du World
        pixel_x, pixel_y = self.world_manager.get_entity_pixel_pos(pion.combat_tile_x, pion.combat_tile_y)

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