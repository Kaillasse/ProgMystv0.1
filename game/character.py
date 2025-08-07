import pygame
import math
from core.settings import LAYER_HEIGHT


class Character:
    def __init__(self, session, world_manager, speed=3.0):  # speed en tuiles/seconde (2x plus rapide)
        self.session = session
        self.world_manager = world_manager
        self.name = session.name
        self.sprite_path = session.sprite_path
        
        # Position logique UNIQUEMENT (flottante pour fluidité)
        spawn_x, spawn_y = self.world_manager.get_spawn_position()
        spawn_layer = self.world_manager.get_spawn_layer()
        self.position = {
            "x": float(spawn_x), 
            "y": float(spawn_y), 
            "layer": spawn_layer
        }
        
        print(f"[CHAR] Init: position logique ({spawn_x}, {spawn_y}) layer {spawn_layer}")
        
        # Timers et protections
        self.spawn_protection_timer = 1000
        self.last_spawn_time = pygame.time.get_ticks()
        
        # Sprite et animations
        self.sprite_sheet = pygame.image.load(session.data["sprite_path"]).convert_alpha()
        self.frame_width, self.frame_height, self.columns, self.rows = 48, 96, 12, 8
        self.frames = self.load_frames()
        self.animations = self.define_animations()
        self.anim_state = "idle_front"
        self.anim_index = 0
        self.anim_timer = 0
        self.anim_delay = 120
        
        # Mouvement
        self.direction = "front"
        self.input_vector = (0.0, 0.0)
        self.moving = False
        self.speed = speed  # tuiles/seconde

    # === CHARGEMENT DES RESSOURCES ===
    
    def load_frames(self):
        return [self.sprite_sheet.subsurface(pygame.Rect(col * self.frame_width, row * self.frame_height,
                self.frame_width, self.frame_height))
                for row in range(self.rows) for col in range(self.columns)]

    def define_animations(self):
        return {
            "idle_front": [1], "idle_left": [13], "idle_right": [25], "idle_back": [37],
            "idle_frontright": [16], "idle_frontleft": [4], "idle_backleft": [28], "idle_backright": [40],
            "walk_front": [0, 2], "walk_left": [12, 14], "walk_right": [24, 26], "walk_back": [36, 38],
            "walk_frontright": [15, 17], "walk_frontleft": [3, 5], "walk_backright": [39, 41], "walk_backleft": [27, 29]
        }

    # === GESTION DES ENTRÉES ===
    
    def handle_input(self, keys):
        ne_input = nw_input = se_input = sw_input = 0.0
        
        # Mappage des touches vers les directions isométriques de grille
        if keys[pygame.K_UP] or keys[pygame.K_z]:      # Nord = 0.5*NE + 0.5*NW
            ne_input += 0.5
            nw_input += 0.5
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:    # Sud = 0.5*SE + 0.5*SW
            se_input += 0.5
            sw_input += 0.5
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:   # Est = 0.5*NE + 0.5*SE
            ne_input += 0.5
            se_input += 0.5
        if keys[pygame.K_LEFT] or keys[pygame.K_q]:    # Ouest = 0.5*NW + 0.5*SW
            nw_input += 0.5
            sw_input += 0.5
        
        # Conversion vers coordonnées de grille isométrique (x, y)
        # NE/SW contrôlent l'axe X de la grille iso
        # NW/SE contrôlent l'axe Y de la grille iso
        grid_dx = nw_input - se_input  # +x = NW, -x = SE
        grid_dy = ne_input - sw_input  # +y = NE, -y = SW
        
        # Normalisation pour vitesse constante en diagonale
        norm = math.hypot(grid_dx, grid_dy)
        if norm > 0:
            grid_dx /= norm
            grid_dy /= norm

        self.input_vector = (grid_dx, grid_dy)
        self.moving = (grid_dx != 0 or grid_dy != 0)
        self.direction = self.compute_direction_from_grid(grid_dx, grid_dy)

    def compute_direction_from_grid(self, grid_dx, grid_dy):
        """Calcule la direction d'animation basée sur le mouvement de grille isométrique"""
        # Tolérance pour éviter les micro-mouvements
        tolerance = 0.1
        
        if abs(grid_dx) < tolerance and abs(grid_dy) < tolerance:
            return self.direction  # Pas de mouvement, garder la direction actuelle
        
        # Directions basées sur les coordonnées de grille isométrique
        if grid_dx > tolerance and grid_dy > tolerance:
            return "back"      # NE + NW = Nord
        elif grid_dx > tolerance and grid_dy < -tolerance:
            return "left"      # NE + SE = Est
        elif grid_dx < -tolerance and grid_dy < -tolerance:
            return "front"       # SW + SE = Sud
        elif grid_dx < -tolerance and grid_dy > tolerance:
            return "right"       # SW + NW = Ouest
        elif grid_dx > tolerance:
            return "backleft" # NE dominant
        elif grid_dx < -tolerance:
            return "frontleft"   # SW dominant
        elif grid_dy > tolerance:
            return "backright"  # NW dominant
        elif grid_dy < -tolerance:
            return "frontright"  # SE dominant

        return self.direction

    # === MISE À JOUR DU PERSONNAGE ===
    
    def update(self, dt):
        keys = pygame.key.get_pressed()
        self.handle_input(keys)
        self.anim_state = f"walk_{self.direction}" if self.moving else f"idle_{self.direction}"
        if self.moving:
            self.move(dt)
        self.update_animation(dt)
        
        # Vérifier et corriger le layer actuel si nécessaire
        self._verify_current_layer()
        
        # Vérifier les transitions (position entière pour la logique)
        current_tile_x = int(round(self.position["x"]))
        current_tile_y = int(round(self.position["y"]))
        transition = self.world_manager.check_transition(current_tile_x, current_tile_y)
        if transition:
            self._handle_transition(transition)

    def _verify_current_layer(self):
        """Vérifie que le layer courant correspond à la position actuelle"""
        current_tile_x = int(round(self.position["x"]))
        current_tile_y = int(round(self.position["y"]))
        
        # Rechercher toutes les tuiles walkable à la position actuelle
        tiles_here = [t for t in self.world_manager.zone.get_all_tiles_with_pos() 
                     if t["x"] == current_tile_x and t["y"] == current_tile_y and t["is_walkable"]]
        
        if tiles_here:
            # Vérifier si le layer actuel est valide
            valid_layers = [t["z"] for t in tiles_here]
            if self.position["layer"] not in valid_layers:
                # Corriger vers le layer le plus haut disponible
                highest_layer = max(valid_layers)
                print(f"[CHAR] Correction layer: L{self.position['layer']} -> L{highest_layer}")
                self.position["layer"] = highest_layer

    # === SYSTÈME DE MOUVEMENT ===
    
    def _handle_transition(self, transition):
        print(f"[TRANSITION] Passage vers {transition['target_map']}")
        self.world_manager.change_zone(transition['target_map'])
        spawn_x, spawn_y = self.world_manager.get_spawn_position()
        spawn_layer = self.world_manager.get_spawn_layer()
        self.position = {
            "x": float(spawn_x), 
            "y": float(spawn_y), 
            "layer": spawn_layer
        }
        self.last_spawn_time = pygame.time.get_ticks()
    
    def move(self, dt):
        # Mouvement linéaire fluide sur la grille isométrique logique
        grid_dx, grid_dy = self.input_vector
        if grid_dx == 0 and grid_dy == 0:
            return
            
        # Calculer le déplacement en tuiles de grille
        dt_seconds = dt / 1000.0
        movement_distance = self.speed * dt_seconds
        
        # Nouvelle position flottante sur la grille isométrique
        new_pos_x = self.position["x"] + grid_dx * movement_distance
        new_pos_y = self.position["y"] + grid_dy * movement_distance
        
        # Comparaison flottante pour la collision (plus d'arrondis)
        current_tile_x = self.position["x"]
        current_tile_y = self.position["y"]
        target_tile_x = new_pos_x
        target_tile_y = new_pos_y

        # Tester collision seulement si changement de tuile (flottant)
        if (target_tile_x != current_tile_x) or (target_tile_y != current_tile_y):
            result = self.world_manager.can_move(
                current_tile_x, current_tile_y,
                target_tile_x, target_tile_y, self.position["layer"])
            if not result["can_move"]:
                return  # Mouvement bloqué
            self.position["layer"] = result["target_layer"]
            print(f"[MOVE] Layer mis à jour: L{self.position['layer']} ({result['reason']})")

        # Mise à jour de la position logique (toujours en float)
        self.position["x"] = new_pos_x
        self.position["y"] = new_pos_y

    # === SYSTÈME DE COLLISION ET CHUTE ===
    
    def trigger_fall(self):
        print("[CHAR.trigger_fall] Chute détectée !")
        fall_destination = self.world_manager.get_fall_destination()
        if fall_destination:
            self.world_manager.change_zone(fall_destination)
            spawn_x, spawn_y = self.world_manager.get_spawn_position()
            spawn_layer = self.world_manager.get_spawn_layer()
            self.position = {
                "x": float(spawn_x), 
                "y": float(spawn_y), 
                "layer": spawn_layer
            }
            print(f"[CHAR.trigger_fall] Respawn à ({spawn_x}, {spawn_y}) layer {spawn_layer}")

    # === ANIMATION ===
    
    def update_animation(self, dt):
        frames = self.animations.get(self.anim_state)
        if not frames:
            self.anim_state = "idle_front"
            frames = self.animations["idle_front"]
            self.anim_index = 0
        self.anim_timer += dt
        if self.anim_timer >= self.anim_delay:
            self.anim_timer = 0
            self.anim_index = (self.anim_index + 1) % len(frames)

    def get_current_frame(self):
        frames = self.animations.get(self.anim_state)
        return self.frames[frames[self.anim_index % len(frames)]] if frames else self.frames[0]

    # === RENDU (conversion tuile→pixel à la volée) ===
    
    def get_render_position(self):
        """Calcule la position pixel pour le rendu à partir de la position logique"""
        pixel_x, pixel_y = self.world_manager.tile_to_pixel(self.position["x"], self.position["y"])
        height_offset = -(self.position["layer"] * LAYER_HEIGHT)
        return pixel_x, pixel_y + height_offset

    def draw(self, surface, camera):
        frame = self.get_current_frame()
        pixel_x, pixel_y = self.get_render_position()
        
        draw_x = pixel_x - camera.x - frame.get_width() // 2
        draw_y = pixel_y - camera.y - frame.get_height() + 16
        
        surface.blit(frame, (draw_x, draw_y))
        self.draw_debug_info(surface, camera)

    def draw_debug_info(self, surface, camera):
        font = pygame.font.SysFont("Arial", 14, bold=True)
        
        # Position logique
        pos_text = f"Position: ({self.position['x']:.2f}, {self.position['y']:.2f}) Layer: L{self.position['layer']}"
        pos_surface = font.render(pos_text, True, (255, 255, 0))
        surface.blit(pos_surface, (10, 10))
        
        # Position entière pour collision
        tile_x = int(round(self.position["x"]))
        tile_y = int(round(self.position["y"]))
        tile_text = f"Tuile collision: ({tile_x}, {tile_y})"
        tile_surface = font.render(tile_text, True, (255, 255, 0))
        surface.blit(tile_surface, (10, 25))
        
        # Vecteur de mouvement (grille isométrique)
        vector_text = f"Grille: ({self.input_vector[0]:.2f}, {self.input_vector[1]:.2f})"
        vector_surface = font.render(vector_text, True, (0, 255, 255))
        surface.blit(vector_surface, (10, 40))
