import pygame
import math
from game.entity import Entity




class Character(Entity):
    def __init__(self, session, world_manager, speed=3.0):
        # Récupération du spawn depuis World
        spawn_x, spawn_y = world_manager.get_spawn_position('joueur')
        
        # Initialisation Entity avec position et nom
        super().__init__([spawn_x, spawn_y], session.name)
        
        # Attributs spécifiques au Character
        self.session = session
        self.world_manager = world_manager
        self.sprite_path = session.sprite_path
        
        # Stats de combat (redéfinition des valeurs Entity)
        self.current_hp = 2
        self.max_hp = 2
        self.energie = 1
        
        # Synchronisation automatique via World
        self.world_manager.sync_combat_positions([self])
        
        print(f"[CHAR] Init: position unifiée ({spawn_x}, {spawn_y}) via World")
        
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
        self.speed = speed
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
            return "frontright"   # SW dominant
        elif grid_dy > tolerance:
            return "backright"  # NW dominant
        elif grid_dy < -tolerance:
            return "frontleft"  # SE dominant

        return self.direction

    # === MISE À JOUR DU PERSONNAGE ===
    
    def update(self, dt):
        """Update unifié utilisant les méthodes de World"""
        keys = pygame.key.get_pressed()
        self.handle_input(keys)
        self.anim_state = f"walk_{self.direction}" if self.moving else f"idle_{self.direction}"
        if self.moving:
            self.move(dt)
            # Synchronisation moins fréquente via World après mouvement
            # On ne synchronise que si la position de grille a changé
            new_grid_x, new_grid_y = self.world_manager.get_grid_position(self)
            if (new_grid_x != self.combat_tile_x or new_grid_y != self.combat_tile_y):
                self.world_manager.sync_combat_positions([self])
        self.update_animation(dt)


    # === SYSTÈME DE MOUVEMENT ===
    
    # === SYSTÈME DE MOUVEMENT HYBRIDE ===
    # 
    # LOGIQUE HYBRIDE FLOAT + INT :
    # - Position du personnage : stockée en float pour la fluidité (ex: 15.6, 12.3)
    # - Grille du monde : en coordonnées entières (ex: tuile (16, 12))
    # - Collision : testée uniquement lors du franchissement d'une frontière de tuile entière
    # 
    # AVANTAGES :
    # 1. Fluidité : le personnage se déplace de manière continue en float
    # 2. Performance : collision testée seulement aux changements de tuile (pas à chaque frame)
    # 3. Précision : logique de collision basée sur des tuiles entières discrètes
    # 4. Robustesse : évite les micro-déplacements et les tests redondants
    #
    

    def move(self, dt):
        """Mouvement fluide unifié"""
        grid_dx, grid_dy = self.input_vector
        if grid_dx == 0 and grid_dy == 0:
            return
            
        # Calcul mouvement simplifié
        dt_seconds = dt / 1000.0
        movement_distance = self.speed * dt_seconds
        
        # Mise à jour position unifiée
        self.tile_pos[0] += grid_dx * movement_distance
        self.tile_pos[1] += grid_dy * movement_distance

    # === SYSTÈME DE COLLISION ET CHUTE ===
    
    def trigger_fall(self):
        print("[CHAR.trigger_fall] Chute détectée !")
        fall_destination = self.world_manager.get_fall_destination()
        if fall_destination:
            self.world_manager.change_zone(fall_destination)
            spawn_x, spawn_y = self.world_manager.get_spawn_position()
            # NOUVEAU : Position unifiée avec tile_pos
            self.tile_pos = [float(spawn_x), float(spawn_y)]
            # Synchroniser les positions de combat
            self.combat_tile_x = spawn_x
            self.combat_tile_y = spawn_y
            print(f"[CHAR.trigger_fall] Respawn à ({spawn_x}, {spawn_y}) - position unifiée")

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

    # === RENDU UNIFIÉ ===
    
    def get_render_position(self):
        """API UNIFIÉE : Position pixel via World (comme PNJs)"""
        return self.world_manager.get_entity_pixel_pos(self.tile_pos[0], self.tile_pos[1])

    def draw(self, surface, camera):
        """Rendu unifié du Character - compatible avec l'appel depuis game_manager"""
        frame = self.get_current_frame()
        pixel_x, pixel_y = self.get_render_position()
        
        # Utilise camera.x et camera.y comme avant la refactorisation
        draw_x = pixel_x - camera.x - frame.get_width() // 2
        draw_y = pixel_y - camera.y - frame.get_height() + 16
        
        surface.blit(frame, (draw_x, draw_y))
        self.draw_debug_info(surface)

    def draw_debug_info(self, surface):
        """DEBUG UNIFIÉ : Affichage via World (comme PNJs)"""
        font = pygame.font.SysFont("Arial", 14, bold=True)
        
        # Position unifiée via World
        grid_x, grid_y = self.world_manager.get_grid_position(self)
        pixel_x, pixel_y = self.get_render_position()
        combat_pos = f"combat({self.combat_tile_x}, {self.combat_tile_y})"
        
        debug_texts = [
            f"Character: {self.name}",
            f"tile_pos: ({self.tile_pos[0]:.2f}, {self.tile_pos[1]:.2f})",
            f"grid: ({grid_x}, {grid_y})",
            combat_pos,
            f"pixel: ({pixel_x:.1f}, {pixel_y:.1f})",
            f"direction: {self.direction}",
            f"moving: {self.moving}"
        ]
        
        for i, text in enumerate(debug_texts):
            color = (255, 255, 255) if i != 2 else (255, 255, 0)  # Surbrillance pour grid
            text_surface = font.render(text, True, color)
            surface.blit(text_surface, (10, 10 + i * 16))
            text_surface = font.render(text, True, (255, 255, 0))
            surface.blit(text_surface, (10, 10 + i * 16))
