import pygame
import math
from game.entity import Entity

class Character(Entity):
    """Simplified Character with fluid movement"""
    
    def __init__(self, session, world_manager, speed=3.0):
        # Get reliable spawn position
        spawn_x, spawn_y = world_manager.get_spawn_position('joueur')
        
        # Initialize as Entity with grid position
        super().__init__([spawn_x, spawn_y], session.name)
        
        # Character uses float position for smooth movement
        self.float_pos = [float(spawn_x), float(spawn_y)]
        
        print(f"[CHAR] Initialized - grid: {tuple(self.grid_pos)}, float: {tuple(self.float_pos)}")
        
        # Character-specific attributes
        self.session = session
        self.world_manager = world_manager
        self.speed = speed
        
        # Combat stats
        self.current_hp = 2
        self.max_hp = 2
        self.energie = 1
        
        # Load sprite
        self.sprite_sheet = pygame.image.load(session.data["sprite_path"]).convert_alpha()
        self.frame_width, self.frame_height, self.columns, self.rows = 48, 96, 12, 8
        self.frames = self.load_frames()
        self.animations = self.define_animations()
        
        # Animation state
        self.anim_state = "idle_front"
        self.anim_index = 0
        self.anim_timer = 0
        self.anim_delay = 120
        
        # Movement state
        self.direction = "front"
        self.moving = False
        
        # Register with world
        self.register_to_world(world_manager)
        
        print(f"[CHAR] Initialized at {tuple(self.grid_pos)}")
    
    def get_position(self):
        """Character returns float position for smooth movement"""
        return tuple(self.float_pos)
    
    def sync_positions(self):
        """Synchronize grid and float positions using unified coordinate system"""
        # Update grid position from float position
        new_grid_x = int(round(self.float_pos[0]))
        new_grid_y = int(round(self.float_pos[1]))
        
        # Ensure within map bounds (0-32)
        new_grid_x = max(0, min(32, new_grid_x))
        new_grid_y = max(0, min(32, new_grid_y))
        
        if [new_grid_x, new_grid_y] != self.grid_pos:
            old_grid = tuple(self.grid_pos)
            self.grid_pos = [new_grid_x, new_grid_y]
            print(f"[CHAR] Grid synced from {old_grid} to {tuple(self.grid_pos)}")
            
            # Update session on grid change
            if hasattr(self, 'session'):
                self.session.update_grid_position(new_grid_x, new_grid_y)
    
    def get_current_frame(self):
        """Get current animation frame"""
        frames = self.animations.get(self.anim_state)
        return self.frames[frames[self.anim_index % len(frames)]] if frames else self.frames[0]
    
    def load_frames(self):
        """Load sprite frames"""
        return [self.sprite_sheet.subsurface(pygame.Rect(
            col * self.frame_width, row * self.frame_height,
            self.frame_width, self.frame_height))
            for row in range(self.rows) for col in range(self.columns)]

    def define_animations(self):
        """Define animation sequences"""
        return {
            "idle_front": [1], "idle_left": [13], "idle_right": [25], "idle_back": [37],
            "idle_frontright": [16], "idle_frontleft": [4], "idle_backleft": [28], "idle_backright": [40],
            "walk_front": [0, 2], "walk_left": [12, 14], "walk_right": [24, 26], "walk_back": [36, 38],
            "walk_frontright": [15, 17], "walk_frontleft": [3, 5], "walk_backright": [39, 41], "walk_backleft": [27, 29]
        }

    def handle_input(self, keys):
        """Handle movement input following exact grid axis mapping"""
        grid_dx = grid_dy = 0.0
        
        # Direct mapping from table: World axes are -x/+x = NW/SE, -y/+y = NE/SW
        if keys[pygame.K_UP] or keys[pygame.K_z]:         # UP: Δx=-0.5, Δy=-0.5
            grid_dx -= 0.5
            grid_dy -= 0.5
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:       # DOWN: Δx=+0.5, Δy=+0.5  
            grid_dx += 0.5
            grid_dy += 0.5
        if keys[pygame.K_LEFT] or keys[pygame.K_q]:       # LEFT: Δx=-0.5, Δy=+0.5
            grid_dx -= 0.5
            grid_dy += 0.5
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:      # RIGHT: Δx=+0.5, Δy=-0.5
            grid_dx += 0.5
            grid_dy -= 0.5

        # Normalize for diagonal movement
        norm = math.hypot(grid_dx, grid_dy)
        if norm > 0:
            grid_dx /= norm
            grid_dy /= norm

        self.input_vector = (grid_dx, grid_dy)
        self.moving = (grid_dx != 0 or grid_dy != 0)
        self.direction = self.compute_direction_from_grid(grid_dx, grid_dy)

    def compute_direction_from_grid(self, grid_dx, grid_dy):
        """Compute animation direction from table mapping"""
        tolerance = 0.1
        
        if abs(grid_dx) < tolerance and abs(grid_dy) < tolerance:
            return self.direction
        
        # Direction mapping from table
        if grid_dx < -tolerance and grid_dy < -tolerance:
            return "back"       # UP: Δx=-1, Δy=-1 → back animation
        elif grid_dx > tolerance and grid_dy > tolerance:
            return "front"      # DOWN: Δx=+1, Δy=+1 → front animation
        elif grid_dx < -tolerance and grid_dy > tolerance:
            return "left"       # LEFT: Δx=-1, Δy=+1 → left animation
        elif grid_dx > tolerance and grid_dy < -tolerance:
            return "right"      # RIGHT: Δx=+1, Δy=-1 → right animation
        elif grid_dx < -tolerance:
            return "backleft"   # UP+LEFT: Δx=-2, Δy=0 → back_left
        elif grid_dy < -tolerance:
            return "backright"  # UP+RIGHT: Δx=0, Δy=-2 → back_right
        elif grid_dy > tolerance:
            return "frontleft"  # DOWN+LEFT: Δx=0, Δy=+2 → front_left
        elif grid_dx > tolerance:
            return "frontright" # DOWN+RIGHT: Δx=+2, Δy=0 → front_right

        return self.direction

    def update(self, dt):
        """Update character"""
        # Handle input
        keys = pygame.key.get_pressed()
        self.handle_input(keys)
        
        # Update animation state
        self.anim_state = f"walk_{self.direction}" if self.moving else f"idle_{self.direction}"
        
        # Move if moving
        if self.moving:
            self.move(dt)
        
        # Update animation
        self.update_animation(dt)

    def move(self, dt):
        """Smooth character movement using exact grid axes"""
        grid_dx, grid_dy = self.input_vector
        if grid_dx == 0 and grid_dy == 0:
            return
        
        # Calculate movement delta
        dt_seconds = dt / 1000.0
        movement_distance = self.speed * dt_seconds
        
        # Calculate new float position
        new_x = self.float_pos[0] + grid_dx * movement_distance
        new_y = self.float_pos[1] + grid_dy * movement_distance
        
        # Check if new grid position is valid
        test_grid_x = int(round(new_x))
        test_grid_y = int(round(new_y))
        
        if self.world and self.world.is_valid_position(test_grid_x, test_grid_y):
            # Update float position
            self.float_pos = [new_x, new_y]
            
            # Sync grid position only when needed (not forced)
            self.sync_positions()
        else:
            # Movement blocked
            print(f"[CHAR] Movement blocked at ({test_grid_x}, {test_grid_y})")

    def update_animation(self, dt):
        """Update sprite animation"""
        frames = self.animations.get(self.anim_state)
        if not frames:
            self.anim_state = "idle_front"
            frames = self.animations["idle_front"]
            self.anim_index = 0
        
        self.anim_timer += dt
        if self.anim_timer >= self.anim_delay:
            self.anim_timer = 0
            self.anim_index = (self.anim_index + 1) % len(frames)

    def draw(self, surface, camera):
        """Draw character using float position for smooth movement"""
        camera_offset = (-camera.x, -camera.y)
        super().draw(surface, camera_offset)
        
        # Simple debug info
        if hasattr(self, 'show_debug') and self.show_debug:
            font = pygame.font.SysFont("Arial", 12)
            debug_text = f"POS: {tuple(self.grid_pos)} | FLOAT: ({self.float_pos[0]:.1f}, {self.float_pos[1]:.1f})"
            text_surface = font.render(debug_text, True, (255, 255, 255))
            surface.blit(text_surface, (10, 10))

    # Combat methods for compatibility
    def combat_move_to(self, target_x, target_y):
        """Combat positioning using unified grid system"""
        target_x, target_y = int(round(target_x)), int(round(target_y))
        
        if self.world and self.world.is_valid_position(target_x, target_y):
            # Sync both positions
            self.grid_pos = [target_x, target_y]
            self.float_pos = [float(target_x), float(target_y)]
            print(f"[CHAR] Combat moved to {tuple(self.grid_pos)}")
            return "none"
        
        print(f"[CHAR] Combat move blocked to ({target_x}, {target_y})")
        return "blocked"

    def combat_attack_direction(self, target_x, target_y):
        """Calculate attack direction"""
        dx = target_x - self.grid_pos[0]
        dy = target_y - self.grid_pos[1]
        return "none"  # Simplified for now