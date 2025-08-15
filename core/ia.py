# core/ia.py
from game.pnj.dame_indenta import DameIndenta
# Module IA pour les actions et déplacements de l'ordinateur (ex: Dame Indenta)

class DameIndentaAI:
    def __init__(self, name, world_manager, speed=3.0):
        """IA surcheatée pour Dame Indenta - peut se déplacer partout sur ses lignes x/y et one-shot le joueur"""
        self.name = name
        self.world_manager = world_manager
        self.speed = speed
        # UNIFIED: Use grid_pos for positioning
        self.grid_pos = [0, 4]
        self.current_hp = 2
        self.max_hp = 2
        self.current_frame = 0
# === COMPORTEMENT EN COMBAT ===
    def get_current_frame(self):
        frames = self.animations.get(self.anim_state)
        return self.frames[frames[self.anim_index % len(frames)]] if frames else self.frames[0]
    
    def combat_move_set(self, dx, dy):
        #liste de differents mouvements possibles pour affichage
        movements = {
            "up": (0, -1),
            "down": (0, 1),
            "left": (-1, 0),
            "right": (1, 0)
        }
        #calculer la direction du mouvement
        for direction, (mx, my) in movements.items():
            if dx == mx and dy == my:
                print(f"[COMBAT] Mouvement en {direction} activé")
                return direction
        print("[COMBAT] Aucun mouvement valide")
        return None
    def combat_attack_set(self, dx, dy):
        # Liste des directions d'attaque possibles pour affichage
        attacks = {
            "up": (0, -1),
            "down": (0, 1),
            "left": (-1, 0),
            "right": (1, 0)
        }
        # Calculer la direction de l'attaque
        for direction, (mx, my) in attacks.items():
            if dx == mx and dy == my:
                print(f"[COMBAT] Attaque en {direction} activée")
                return direction
        print("[COMBAT] Aucun mouvement valide")
        return None
    @property
    def is_alive(self):
        return self.current_hp > 0 
    def choose_action(self, dame_unit, player_units):
        """Choisit l'action de Dame Indenta (surcheatée volontairement)"""
        if not player_units:
            return ("wait", None)
            
        player = player_units[0]  # Le joueur principal
        
        # UNIFIED: Check if player is on same line X or Y
        if dame_unit.grid_pos[0] == player.grid_pos[0] or dame_unit.grid_pos[1] == player.grid_pos[1]:
            return ("attack", player)
        
        # UNIFIED: Move to common line to prepare attack
        dx = abs(dame_unit.grid_pos[0] - player.grid_pos[0])
        dy = abs(dame_unit.grid_pos[1] - player.grid_pos[1])
        
        if dx <= dy:
            # Move to same X line as player
            return ("move", (player.grid_pos[0], dame_unit.grid_pos[1]))
        else:
            # Move to same Y line as player
            return ("move", (dame_unit.grid_pos[0], player.grid_pos[1]))
    
    def execute_action(self, dame_unit, action_type, target):
        """Exécute l'action choisie par l'IA"""
        if action_type == "move" and target:
            new_x, new_y = target
            dame_unit.move_to(new_x, new_y)
            print(f"[IA] UNIFIED: Dame Indenta moves to ({new_x}, {new_y})")
            return True
            
        elif action_type == "attack" and target:
            # One-shot attack
            target.current_hp = 0
            print(f"[IA] UNIFIED: Dame Indenta attacks {target.name} - One Shot!")
            return True
            
        return False
