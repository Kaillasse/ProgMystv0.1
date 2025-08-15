import json
import pygame
import os
from core.settings import *

class World:
    """Simple isometric world with clean coordinate system"""
    
    def __init__(self, screen):
        self.screen = screen
        self.screen_center_x = screen.get_width() // 2
        self.screen_center_y = screen.get_height() // 2
        
        # Simple entity system
        self.entities = []
        
        # Spawn points using REAL tile coordinates (0-32)
        # Based on visual observation from screenshot
        self.spawn_points = {
            "joueur": (16, 16),         # Center of 33x33 map (correct)
            "DameIndenta": (10, 20),    # Lower left area (south-west of center)
            "Neuill": (16, 10),         # North of center (as seen in screenshot)
            "JSON": (10, 16),           # West of center  
            "Loopfang": (22, 16),       # East of center
        }
        
        # Reference walkable layer (layer_1 = index 2)
        self.walkable_layer_index = 2
        
        # Tile system
        self.tile_images = []
        self.tile_grid = {}  # grid_pos -> tile_data
        
        # Load everything
        self.load_tiles()
        self.load_map()
        self.validate_spawn_points()
        
    def load_tiles(self):
        """Load tile images from assets/tiles/"""
        self.tile_images = []
        tiles_dir = "assets/tiles"
        
        try:
            if os.path.exists(tiles_dir):
                tile_files = [f for f in sorted(os.listdir(tiles_dir)) 
                             if f.endswith(".png") and f.startswith("tile_")]
                
                for filename in tile_files:
                    path = os.path.join(tiles_dir, filename)
                    img = pygame.image.load(path).convert_alpha()
                    img = pygame.transform.scale(img, (TILE_WIDTH, TILE_HEIGHT))
                    self.tile_images.append(img)
                
                print(f"[WORLD] Loaded {len(self.tile_images)} tile images")
            else:
                print("[WORLD] Tiles directory not found, using fallback")
                self._create_fallback_tile()
                
        except Exception as e:
            print(f"[WORLD] Error loading tiles: {e}")
            self._create_fallback_tile()
    
    def _create_fallback_tile(self):
        """Create simple fallback tile"""
        fallback = pygame.Surface((TILE_WIDTH, TILE_HEIGHT), pygame.SRCALPHA)
        
        # Draw diamond shape
        points = [
            (TILE_WIDTH//2, 0),           # Top
            (TILE_WIDTH, TILE_HEIGHT//2), # Right
            (TILE_WIDTH//2, TILE_HEIGHT), # Bottom
            (0, TILE_HEIGHT//2)           # Left
        ]
        pygame.draw.polygon(fallback, (100, 150, 100), points)
        pygame.draw.polygon(fallback, (80, 120, 80), points, 2)
        
        self.tile_images = [fallback]
    
    def load_map(self):
        """Load map data and create isometric grid"""
        map_path = "data/map/clairiere.json"
        
        try:
            if os.path.exists(map_path):
                with open(map_path, 'r', encoding='utf-8') as f:
                    map_data = json.load(f)
                
                self._process_map_data(map_data)
                print(f"[WORLD] Map loaded with {len(self.tile_grid)} tiles")
            else:
                print("[WORLD] Map file not found, creating default grid")
                self._create_default_grid()
                
        except Exception as e:
            print(f"[WORLD] Error loading map: {e}")
            self._create_default_grid()
    
    def _process_map_data(self, map_data):
        """Process JSON map data using REAL coordinates (0-32)"""
        self.tile_grid = {}
        self.walkable_grid = {}  # Simplified walkable reference from layer_1
        
        layers = [l for l in map_data.get("layers", []) if l.get("type") == "tilelayer"]
        
        for layer_index, layer in enumerate(layers):
            width = layer.get("width", 0)
            height = layer.get("height", 0)
            data = layer.get("data", [])
            
            print(f"[WORLD] Processing layer {layer_index}: {width}x{height}")
            
            for y in range(height):
                for x in range(width):
                    idx = y * width + x
                    if idx < len(data):
                        tile_id = data[idx]
                        
                        # Use REAL coordinates (no centering)
                        real_x, real_y = x, y
                        
                        # Store all layers
                        if tile_id > 0:
                            tile_key = (real_x, real_y, layer_index)
                            self.tile_grid[tile_key] = {
                                'tile_id': tile_id,
                                'layer': layer_index
                            }
                        
                        # Layer_1 (index 2) defines walkability
                        if layer_index == self.walkable_layer_index:
                            self.walkable_grid[(real_x, real_y)] = tile_id > 0
                            
                            # Store base walkable tiles for position checks
                            if tile_id > 0:
                                self.tile_grid[(real_x, real_y)] = {
                                    'tile_id': tile_id,
                                    'layer': layer_index,
                                    'walkable': True
                                }
    
    def _create_default_grid(self):
        """Create simple default grid for testing"""
        self.tile_grid = {}
        for x in range(-10, 11):
            for y in range(-10, 11):
                self.tile_grid[(x, y)] = {
                    'tile_id': 1,
                    'walkable': True
                }
    
    def _is_walkable(self, tile_id):
        """Determine if tile is walkable - simple rules"""
        # Most tiles are walkable except obvious obstacles
        blocked_tiles = {91, 92, 93, 94, 95, 101, 102, 103, 104}  # Trees, rocks, etc
        return tile_id not in blocked_tiles
    
    def validate_spawn_points(self):
        """Ensure all spawn points are on walkable tiles"""
        invalid_spawns = []
        
        for name, (x, y) in list(self.spawn_points.items()):
            if not self.is_valid_position(x, y):
                # Find nearest walkable tile
                new_pos = self.find_nearest_walkable(x, y)
                if new_pos:
                    print(f"[WORLD] Moved spawn point {name} from ({x}, {y}) to {new_pos}")
                    self.spawn_points[name] = new_pos
                else:
                    print(f"[WORLD] Error: Could not find walkable position for {name}")
                    invalid_spawns.append(name)
        
        if invalid_spawns:
            print(f"[WORLD] Warning: {len(invalid_spawns)} spawn points remain invalid: {invalid_spawns}")
    
    def find_nearest_walkable(self, x, y, max_distance=5):
        """Find nearest walkable position using spiral search"""
        # Start from distance 1 and spiral outward
        for distance in range(1, max_distance + 1):
            # Check all positions at this distance
            for dx in range(-distance, distance + 1):
                for dy in range(-distance, distance + 1):
                    # Only check positions on the border of the current distance
                    if abs(dx) == distance or abs(dy) == distance:
                        test_x, test_y = int(x + dx), int(y + dy)
                        if self.is_valid_position(test_x, test_y):
                            return (test_x, test_y)
        
        print(f"[WORLD] No walkable position found near ({x}, {y}) within {max_distance} tiles")
        return None
    
    def get_spawn_position(self, entity_name):
        """Get reliable spawn position aligned with tile grid"""
        spawn_pos = self.spawn_points.get(entity_name, (0, 0))
        
        # Debug: show which tile this corresponds to
        print(f"[WORLD] {entity_name} spawn: grid {spawn_pos}")
        
        # Ensure spawn position is valid and walkable
        if not self.is_valid_position(spawn_pos[0], spawn_pos[1]):
            print(f"[WORLD] Warning: Spawn {spawn_pos} for {entity_name} not walkable")
            
            # Try to find a nearby walkable position
            valid_pos = self.find_nearest_walkable(spawn_pos[0], spawn_pos[1])
            if valid_pos:
                print(f"[WORLD] Found walkable position {valid_pos} for {entity_name}")
                return valid_pos
            else:
                print(f"[WORLD] Error: No walkable position found for {entity_name}, using default (0,0)")
                return (0, 0)
        
        print(f"[WORLD] {entity_name} spawn validated: {spawn_pos}")
        return spawn_pos
    
    def is_valid_position(self, x, y):
        """Simple position validation using layer_1"""
        # Convert to real grid coordinates (0-32)
        grid_x = int(round(float(x)))
        grid_y = int(round(float(y)))
        
        # Check bounds
        if not (0 <= grid_x < 33 and 0 <= grid_y < 33):
            return False
        
        # Check if walkable in layer_1
        return self.walkable_grid.get((grid_x, grid_y), False)
    
    def get_screen_position(self, grid_x, grid_y, camera_offset=(0, 0)):
        """Convert grid coordinates to screen position with unified axis correction"""
        # Apply axis correction: transform to visual-consistent coordinates
        # This matches Character's input logic: +X goes NW, +Y goes NE visually
        corrected_x, corrected_y = self.apply_axis_correction(grid_x, grid_y)
        
        # Center coordinates: (0,0) of map = top-left, (16,16) = center
        centered_x = corrected_x - 16.0
        centered_y = corrected_y - 16.0
        
        # Simple isometric conversion (same for all entities)
        iso_x, iso_y = grid_to_iso(centered_x, centered_y, TILE_WIDTH, TILE_HEIGHT)
        
        # Apply screen centering and camera offset
        screen_x = iso_x + self.screen_center_x + camera_offset[0]
        screen_y = iso_y + self.screen_center_y + camera_offset[1]
        
        return (screen_x, screen_y)
    
    def apply_axis_correction(self, grid_x, grid_y):
        """Apply unified axis correction for all entities
        
        Transforms grid coordinates to match visual movement:
        - Input UP should decrease both visual X and Y (toward NW+NE)
        - Input DOWN should increase both visual X and Y (toward SE+SW)
        - Input LEFT should decrease visual X and increase visual Y (toward NW+SW)  
        - Input RIGHT should increase visual X and decrease visual Y (toward SE+NE)
        """
        # This transformation makes movement visually consistent
        # The same correction that was in Character's handle_input
        corrected_x = float(grid_x)
        corrected_y = float(grid_y)
        
        return corrected_x, corrected_y
    
    def reverse_axis_correction(self, corrected_x, corrected_y):
        """Reverse axis correction for position storage"""
        # Currently identity, but allows future modifications
        grid_x = float(corrected_x)
        grid_y = float(corrected_y)
        
        return grid_x, grid_y
    
    def register_entity(self, entity):
        """Reliably register entity with world"""
        if entity not in self.entities:
            self.entities.append(entity)
            entity.world = self  # Set world reference
            
            # Log registration with reliable position
            grid_pos = entity.get_grid_position()
            screen_pos = self.get_screen_position(grid_pos[0], grid_pos[1])
            print(f"[WORLD] Registered {entity.name} at grid {grid_pos} -> screen {screen_pos}")
    
    def get_tile_image(self, tile_id):
        """Get tile image by ID"""
        if not self.tile_images:
            return None
            
        # Use tile_id as index (with bounds checking)
        idx = (tile_id - 1) % len(self.tile_images)
        return self.tile_images[idx]
    
    def draw(self, screen, camera_offset=(0, 0)):
        """Draw the isometric world with proper layer ordering"""
        # Clear background
        screen.fill((50, 80, 50))  # Dark green
        
        # Get visible tiles with layer support
        visible_tiles = []
        for tile_key, tile_data in self.tile_grid.items():
            # Handle both (x,y) and (x,y,layer) keys
            if len(tile_key) == 3:  # (x, y, layer)
                grid_x, grid_y, layer = tile_key
            elif len(tile_key) == 2:  # (x, y) - skip these, we want layered ones
                continue
            else:
                continue
                
            screen_x, screen_y = self.get_screen_position(grid_x, grid_y, camera_offset)
            
            # Only draw tiles that might be visible
            if (-TILE_WIDTH < screen_x < screen.get_width() + TILE_WIDTH and 
                -TILE_HEIGHT < screen_y < screen.get_height() + TILE_HEIGHT):
                
                visible_tiles.append((grid_x, grid_y, layer, tile_data, screen_x, screen_y))
        
        # Sort for proper isometric rendering: layer first, then y, then x
        visible_tiles.sort(key=lambda t: (t[2], t[1], t[0]))  # Sort by layer, y, x
        
        # Draw tiles with layer offset
        for grid_x, grid_y, layer, tile_data, screen_x, screen_y in visible_tiles:
            tile_img = self.get_tile_image(tile_data['tile_id'])
            if tile_img:
                # Apply Z offset: each layer is 16px higher
                z_offset = layer * 16
                draw_x = screen_x - TILE_WIDTH//2
                draw_y = screen_y - TILE_HEIGHT//2 - z_offset
                screen.blit(tile_img, (draw_x, draw_y))
            
            # Debug: draw layer info
            if False:  # Enable for debugging
                font = pygame.font.Font(None, 16)
                text = font.render(f"L{layer}", True, (255, 255, 255))
                screen.blit(text, (screen_x - 10, screen_y - 10))
    
    def draw_debug_grid(self, screen, camera_offset=(0, 0)):
        """Draw debug grid overlay"""
        for x in range(-5, 6):
            for y in range(-5, 6):
                screen_x, screen_y = self.get_screen_position(x, y, camera_offset)
                
                # Draw diamond outline
                points = [
                    (screen_x, screen_y - TILE_HEIGHT//4),
                    (screen_x + TILE_WIDTH//4, screen_y),
                    (screen_x, screen_y + TILE_HEIGHT//4),
                    (screen_x - TILE_WIDTH//4, screen_y)
                ]
                pygame.draw.polygon(screen, (255, 255, 255), points, 1)
                
                # Draw coordinates
                font = pygame.font.Font(None, 16)
                text = font.render(f"{x},{y}", True, (255, 255, 255))
                text_rect = text.get_rect(center=(screen_x, screen_y))
                screen.blit(text, text_rect)
    
    def print_entity_positions(self):
        """Debug: Print reliable positions of all entities"""
        print("[WORLD] === ENTITY POSITIONS ===")
        for entity in self.entities:
            grid_pos = entity.get_grid_position()
            float_pos = entity.get_position()
            screen_pos = self.get_screen_position(float_pos[0], float_pos[1])
            
            # Check if position is on a tile
            is_on_tile = grid_pos in self.tile_grid
            is_walkable = self.is_valid_position(grid_pos[0], grid_pos[1]) if is_on_tile else False
            
            position_info = f"  {entity.name}: grid {grid_pos}"
            if hasattr(entity, 'float_pos'):
                position_info += f", float {tuple(entity.float_pos)}"
            position_info += f" -> screen {screen_pos}"
            position_info += f" [tile: {is_on_tile}, walkable: {is_walkable}]"
            
            print(position_info)
        print("[WORLD] ========================")
    
    def debug_spawn_points(self):
        """Debug spawn points with REAL coordinates"""
        print("[WORLD] === SPAWN POINTS DEBUG (REAL COORDS) ===")
        for name, (x, y) in self.spawn_points.items():
            is_valid = self.is_valid_position(x, y)
            is_walkable = self.walkable_grid.get((x, y), False)
            tile_in_layer1 = (x, y, self.walkable_layer_index) in self.tile_grid
            
            print(f"  {name}: real({x}, {y}) -> valid: {is_valid}, walkable: {is_walkable}, layer1: {tile_in_layer1}")
        print("[WORLD] =================================")