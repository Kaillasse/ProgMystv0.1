# core/ia.py
from game.pnj.dame_indenta import DameIndenta
# Module IA pour les actions et déplacements de l'ordinateur (ex: Dame Indenta)

class DameIndentaAI:
    def __init__(self, name, world_manager, speed=3.0):
        """IA surcheatée pour Dame Indenta - peut se déplacer partout sur ses lignes x/y et one-shot le joueur"""
        self.name = name
        self.world_manager = world_manager
        self.speed = speed
        self.combat_tile_x = 0
        self.combat_tile_y = 4
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
        
        # Si le joueur est sur la même ligne X ou Y, attaquer immédiatement
        if dame_unit.tile_x == player.tile_x or dame_unit.tile_y == player.tile_y:
            return ("attack", player)
        
        # Sinon, se déplacer sur une ligne commune pour préparer l'attaque
        # Choisir la ligne la plus proche
        dx = abs(dame_unit.tile_x - player.tile_x)
        dy = abs(dame_unit.tile_y - player.tile_y)
        
        if dx <= dy:
            # Se déplacer sur la même ligne X que le joueur
            return ("move", (player.tile_x, dame_unit.tile_y))
        else:
            # Se déplacer sur la même ligne Y que le joueur
            return ("move", (dame_unit.tile_x, player.tile_y))
    
    def execute_action(self, dame_unit, action_type, target):
        """Exécute l'action choisie par l'IA"""
        if action_type == "move" and target:
            new_x, new_y = target
            dame_unit.tile_x = new_x
            dame_unit.tile_y = new_y
            print(f"[IA] Dame Indenta se déplace vers ({new_x}, {new_y})")
            return True
            
        elif action_type == "attack" and target:
            # Attaque one-shot
            target.current_hp = 0
            target.is_alive = False
            print(f"[IA] Dame Indenta attaque {target.name} - One Shot!")
            return True
            
        return False
