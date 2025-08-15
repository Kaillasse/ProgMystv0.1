import pygame
import math
from core.settings import TILE_HEIGHT, grid_to_iso

class Entity:
    """Unified Entity with reliable position system"""
    
    def __init__(self, grid_pos, name):
        # REAL grid coordinates (0-32, matching tile array indices)
        self.grid_pos = [int(round(grid_pos[0])), int(round(grid_pos[1]))]
        self.name = str(name)
        
        # Ensure coordinates are within map bounds
        self.grid_pos[0] = max(0, min(32, self.grid_pos[0]))
        self.grid_pos[1] = max(0, min(32, self.grid_pos[1]))
        
        # Movement system (simplified)
        self.is_moving = False
        
        # Combat stats
        self.current_hp = 1
        self.max_hp = 1
        
        # World reference (set during registration)
        self.world = None
        
        print(f"[ENTITY] {self.name} initialized at REAL grid {tuple(self.grid_pos)}")
        
    def get_grid_position(self):
        """Get reliable grid position (always integers)"""
        return tuple(self.grid_pos)
    
    def get_position(self):
        """Get current position - override in subclasses for smooth movement"""
        return self.get_grid_position()
    
    def get_screen_position(self, camera_offset=(0, 0)):
        """Get reliable screen position using world transformation"""
        if not self.world:
            return (0, 0)
        
        pos = self.get_position()
        screen_x, screen_y = self.world.get_screen_position(pos[0], pos[1], camera_offset)
        return (int(screen_x), int(screen_y))
    
    def move_to(self, x, y):
        """Reliable movement to grid position"""
        target_x, target_y = int(round(x)), int(round(y))
        
        # Validate position if world exists
        if self.world and not self.world.is_valid_position(target_x, target_y):
            print(f"[ENTITY] {self.name} move blocked: ({target_x}, {target_y}) invalid")
            return False
        
        # Update position
        old_pos = tuple(self.grid_pos)
        self.grid_pos = [target_x, target_y]
        print(f"[ENTITY] {self.name} moved from {old_pos} to {tuple(self.grid_pos)}")
        return True
    
    def register_to_world(self, world):
        """Register with world"""
        self.world = world
        world.register_entity(self)
    
    def get_current_frame(self):
        """Must be implemented by subclasses"""
        raise NotImplementedError()
    
    def interact_with_dialogue_state(self, session):
        """
        Méthode d'interaction qui utilise le système de dialogue_state.
        À utiliser dans les classes PNJ.
        """
        if not session:
            print(f"[ENTITY] {self.name}: pas de session pour dialogue_state")
            return None
        
        # Utilise le DialogueDispatcher avec le nouveau système
        from core.dialogue_dispatcher import DialogueDispatcher
        dispatcher = DialogueDispatcher()
        
        # Récupère l'arbre de dialogue basé sur l'état sauvegardé
        dialogue_tree = dispatcher.get_dialogue_tree_for_npc(self.name, session)
        
        if dialogue_tree:
            print(f"[ENTITY] {self.name}: dialogue_state chargé, {len(dialogue_tree)} noeuds")
        else:
            print(f"[ENTITY] {self.name}: aucun dialogue trouvé")
        
        return dialogue_tree
    
    def update(self, dt):
        """Basic update - override in subclasses"""
        pass
    
    def draw(self, screen, camera_offset=(0, 0)):
        """Simple draw using world screen position"""
        screen_x, screen_y = self.get_screen_position(camera_offset)
        frame = self.get_current_frame()
        if frame:
            # Simple center-bottom anchoring
            draw_x = screen_x - frame.get_width() // 2
            draw_y = screen_y - frame.get_height() + TILE_HEIGHT
            screen.blit(frame, (draw_x, draw_y))
    
    # Combat methods
    @property
    def is_alive(self):
        return self.current_hp > 0
    
    def take_damage(self, amount):
        self.current_hp = max(0, self.current_hp - amount)
        return self.current_hp <= 0
    
    def heal(self, amount):
        self.current_hp = min(self.max_hp, self.current_hp + amount)


class PNJManager(Entity):
    """Simplified NPC management"""
    
    def __init__(self, world):
        self.world = world
        self.active_npcs = []
        print("[PNJ_MGR] UNIFIED: PNJ Manager initialized")

    def spawn_npcs(self):
        """Spawn all NPCs using Character-compatible coordinate system"""
        from game.pnj.dame_indenta import DameIndenta
        from game.pnj.neuill import Neuill
        from game.pnj.json import JSON
        from game.pnj.loopfang import Loopfang
        
        npc_classes = {"DameIndenta": DameIndenta, "Neuill": Neuill, "JSON": JSON, "Loopfang": Loopfang}
        self.active_npcs = []
        
        # Use Character-compatible spawn positions (same logic as Character movement)
        character_compatible_spawns = {
            "DameIndenta": (12, 20),    # Sud-ouest du centre (Character logic) 
            "Neuill": (16, 12),         # Nord du centre (visible sur screenshot)  
            "JSON": (12, 16),           # Ouest du centre
            "Loopfang": (20, 16),       # Est du centre
        }
        
        for name, cls in npc_classes.items():
            # Use Character-compatible position if available
            if name in character_compatible_spawns:
                spawn_pos = character_compatible_spawns[name]
                print(f"[PNJ_MGR] Using Character-compatible spawn for {name}: {spawn_pos}")
            else:
                try:
                    spawn_pos = self.world.get_spawn_position(name)
                except ValueError:
                    spawn_pos = (16, 16)  # Default to center
                    print(f"[PNJ_MGR] WARNING: No spawn for {name}, using center")
            
            npc = cls(list(spawn_pos))
            npc.name = name
            npc.register_to_world(self.world)
            self.active_npcs.append(npc)
            print(f"[PNJ_MGR] Spawned {name} at {tuple(npc.grid_pos)}")
        
        print(f"[PNJ_MGR] All {len(self.active_npcs)} NPCs spawned with Character-compatible axes")

    def get_active_npcs(self):
        """Get active NPCs (spawn if empty)"""
        if not self.active_npcs:
            print("[PNJ_MGR] UNIFIED: No active NPCs, spawning...")
            self.spawn_npcs()
        return self.active_npcs

    def update(self, dt):
        """UNIFIED: Update all active NPCs with movement and animation"""
        for npc in self.active_npcs:
            # Use unified update method that handles both movement and animation
            if hasattr(npc, 'update'):
                npc.update(dt)
                
                # Log active NPC movement
                if hasattr(npc, 'is_moving') and npc.is_moving:
                    print(f"[PNJ_MGR] {npc.name} moving: progress {npc.movement_progress:.2f}")
            elif hasattr(npc, 'update_animation'):
                print(f"[PNJ_MGR] WARNING: {npc.name} using legacy update_animation method")
                npc.update_animation(dt)
    
    def draw(self, screen, camera_offset=(0, 0)):
        """Draw all NPCs using unified positioning"""
        for npc in self.active_npcs:
            npc.draw(screen, camera_offset)
    
    def handle_click(self, pixel_x, pixel_y):
        """Simplified sprite-based click detection"""
        for npc in self.active_npcs:
            if self._is_npc_clicked(npc, pixel_x, pixel_y):
                print(f"[PNJ_MGR] Clicked: {npc.name}")
                if hasattr(npc, 'interact') and hasattr(self.world, 'session'):
                    npc.interact(self.world.session)
                else:
                    npc.speak()
                return npc
        return None
    
    def _is_npc_clicked(self, npc, pixel_x, pixel_y):
        """Check if NPC sprite is clicked (excluding transparent pixels)"""
        screen_pos = npc.get_screen_position()
        frame = self._get_npc_frame(npc)
        
        if not frame:
            return False
        
        # Calculate sprite position (center-bottom anchored)
        draw_x = screen_pos[0] - frame.get_width() // 2
        draw_y = screen_pos[1] - frame.get_height() + 16
        
        # Check if click is within sprite bounds
        rel_x = pixel_x - draw_x
        rel_y = pixel_y - draw_y
        
        if not (0 <= rel_x < frame.get_width() and 0 <= rel_y < frame.get_height()):
            return False
        
        # Check for transparent pixel (if frame has alpha)
        if frame.get_bitsize() == 32:
            try:
                pixel_alpha = frame.get_at((rel_x, rel_y)).a
                return pixel_alpha > 0  # Non-transparent pixel
            except:
                return True  # Fallback to true if pixel check fails
        
        return True  # No alpha channel, accept click
    
    def _get_npc_frame(self, npc):
        """Get NPC frame with fallback"""
        if hasattr(npc, 'get_current_frame'):
            return npc.get_current_frame()
        if hasattr(npc, 'sprite') and npc.sprite:
            return npc.sprite
        
        # Debug fallback
        import pygame
        frame = pygame.Surface((48, 96))
        colors = {"Dame Indenta": (255, 0, 0), "Neuill": (0, 255, 0), "JSON": (0, 0, 255), "Loopfang": (255, 255, 0)}
        frame.fill(colors.get(npc.name, (255, 0, 255)))
        return frame
    
    def debug_positions(self):
        """UNIFIED: Debug all NPC positions"""
        print("[PNJ_MGR] === NPC POSITION DEBUG ===")
        for npc in self.active_npcs:
            screen_pos = npc.get_screen_position()
            print(f"[PNJ_MGR] UNIFIED: {npc.name} - grid: {tuple(npc.grid_pos)}, float: {tuple(npc.float_pos)}, screen: {screen_pos}, moving: {getattr(npc, 'is_moving', False)}")
        print("[PNJ_MGR] === END NPC DEBUG ===")
    
    def test_npc_movement(self):
        """Simple movement test"""
        if self.active_npcs:
            npc = self.active_npcs[0]
            print(f"[PNJ] Testing movement: {npc.name}")
            current_x, current_y = npc.grid_pos
            
            # Simple test: move one tile east
            success = npc.move_to(current_x + 1, current_y)
            if success:
                print(f"[PNJ] {npc.name} moved to {tuple(npc.grid_pos)}")
                # Restore position
                npc.move_to(current_x, current_y)
            else:
                print(f"[PNJ] Movement blocked")