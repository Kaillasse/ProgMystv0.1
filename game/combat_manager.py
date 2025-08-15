import pygame
from enum import Enum
from ui.uitools import BorderManager

class CombatState(Enum):
    PLAYER_TURN = "player_turn"
    ENEMY_TURN = "enemy_turn"
    VICTORY = "victory"
    DEFEAT = "defeat"

class CombatAction:
    def __init__(self, name, description, action_func):
        self.name = name
        self.description = description
        self.action_func = action_func

class SimpleCombatManager:
    def __init__(self, world, screen):
        self.world = world
        self.screen = screen
        self.state = CombatState.PLAYER_TURN
        
        self.player_entity = None
        self.enemy_entity = None
        
        self.is_active = False
        self.border_manager = None
        self.font = pygame.font.Font(None, 32)
        self.action_buttons = []
        
        self.player_actions = [
            CombatAction("Move", "Se déplacer", self._handle_move_action),
            CombatAction("Attack", "Attaquer", self._handle_attack_action),
            CombatAction("Abandon", "Quitter le combat", self._abandon_combat)
        ]
        
    def start_combat(self, player_entity, enemy_entity, session=None):
        print("[COMBAT] Début du combat")
        
        if session and not self.border_manager:
            self.border_manager = BorderManager(session=session)
        
        self.player_entity = player_entity
        self.enemy_entity = enemy_entity
        
        self.state = CombatState.PLAYER_TURN
        self.is_active = True
        self._create_action_buttons()
        
    def _handle_move_action(self):
        print("[COMBAT] Action mouvement")
        self._end_player_turn()
        return None
        
    def _handle_attack_action(self):
        print("[COMBAT] Action attaque")
        self._end_player_turn() 
        return None
        
    def _end_player_turn(self):
        self.state = CombatState.ENEMY_TURN
        
    def _abandon_combat(self):
        print("[COMBAT] Combat abandonné")
        self.is_active = False
        return "end_combat"
        
    def _create_action_buttons(self):
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
        if not self.is_active:
            return
        if self.state == CombatState.ENEMY_TURN:
            self._update_enemy_turn()
        self._check_victory_conditions()
        
    def _update_enemy_turn(self):
        print("[COMBAT] Tour ennemi")
        self.state = CombatState.PLAYER_TURN
        
    def _check_victory_conditions(self):
        pass
        
    def handle_event(self, event):
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
        for button_data in self.action_buttons:
            button_data['hovered'] = button_data['rect'].collidepoint(mouse_pos)
            
    def draw(self, screen):
        if not self.is_active:
            return
            
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((20, 20, 40, 150))
        screen.blit(overlay, (0, 0))
        
        self._draw_combat_ui(screen)
        
        for button_data in self.action_buttons:
            self._draw_action_button(screen, button_data)
            
    def _draw_combat_ui(self, screen):
        title = "Combat"
        title_surf = self.font.render(title, True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(screen.get_width() // 2, 30))
        screen.blit(title_surf, title_rect)
        
        state_text = f"Phase: {self.state.value}"
        state_surf = self.font.render(state_text, True, (255, 255, 0))
        state_rect = state_surf.get_rect(center=(screen.get_width() // 2, 60))
        screen.blit(state_surf, state_rect)
        
    def _draw_action_button(self, screen, button_data):
        rect = button_data['rect']
        action = button_data['action']
        hovered = button_data['hovered']
        
        bg_color = (80, 80, 120) if hovered else (50, 50, 80)
        pygame.draw.rect(screen, bg_color, rect)
        
        if self.border_manager:
            self.border_manager.draw_border(screen, rect, border_thickness=2)
        
        text_surf = pygame.font.Font(None, 24).render(action.name, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=rect.center)
        screen.blit(text_surf, text_rect)

CombatManager = SimpleCombatManager