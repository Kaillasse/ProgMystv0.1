import pygame
from core.settings import LAYER_HEIGHT


class Character:
    
    def __init__(self, session, world_manager, speed=120):
        """
        Initialise un nouveau personnage joueur
        """
        # Références principales
        self.session = session
        self.world_manager = world_manager
        self.name = session.name
        self.sprite_path = session.sprite_path
    
        # Une seule source de vérité pour la position
        spawn_x, spawn_y = self.world_manager.get_spawn_position()
        spawn_layer = self.world_manager.get_spawn_layer()
        spawn_tile = (spawn_x, spawn_y)  # Ajout de cette variable manquante
    
        self.position = {"x": spawn_x, "y": spawn_y, "layer": spawn_layer}
        self.pixel_pos = list(self.world_manager.tile_to_pixel(spawn_x, spawn_y))
        
        # Pour compatibilité avec le code existant
        self.tile_pos = [spawn_x, spawn_y]
        self.stable_tile_pos = [spawn_x, spawn_y]
    
        # Calculer la hauteur pour le rendu
        self.height_offset = self._get_height_offset(spawn_x, spawn_y)
        
        print(f"[CHAR.INIT] Spawn: {spawn_tile}, Layer: {spawn_layer} | Height offset: {self.height_offset}")
        print(f"[CHAR.INIT] Position initiale complète: ({spawn_tile[0]}, {spawn_tile[1]}, {spawn_layer})")
        
        # Reste du code inchangé...
        # Protection contre chute immédiate après respawn
        self.spawn_protection_timer = 1000  # 1 seconde de protection
        self.last_spawn_time = pygame.time.get_ticks()
        self._position_check_timer = 0  # Timer pour vérification périodique de position
        self.free_mode = False  # Mode libre pour explorer sans collision
        
        # Chargement du spritesheet
        self.sprite_sheet = pygame.image.load(session.data["sprite_path"]).convert_alpha()
        self.frame_width = 48
        self.frame_height = 96
        self.columns = 12
        self.rows = 8
        self.frames = self.load_frames()

        # Animation
        self.current_animation = []   # ou une animation par défaut comme [0]
        self.frame_index = 0
        self.frame_timer = 0    # nécessaire pour draw_static
        self.animations = self.define_animations()
        self.anim_state = "idle_front"
        self.anim_index = 0
        self.anim_timer = 0
        self.anim_delay = 120  # ms

        # Mouvement
        self.direction = "front"  # Nom directionnel (pour anim)
        self.input_vector = (0, 0)
        self.moving = False
        self.speed = speed  # Pixels par seconde
        
        # Compteur pour réduire les logs de debug
        self._draw_counter = 0

    # === CHARGEMENT DES RESSOURCES ===
    
    def load_frames(self):
        """
        Découpe le spritesheet en frames individuelles
        
        Returns:
            list: Liste des surfaces pygame pour chaque frame
        """
        frames = []
        for row in range(self.rows):
            for col in range(self.columns):
                rect = pygame.Rect(col * self.frame_width, row * self.frame_height,
                                   self.frame_width, self.frame_height)
                frames.append(self.sprite_sheet.subsurface(rect))
        return frames

    def define_animations(self):
        """
        Définit les séquences d'animation pour chaque état/direction
        
        Returns:
            dict: Dictionnaire des animations {nom: [indices_frames]}
        """
        animations = {
            "idle_front": [1], "idle_left": [13], "idle_right": [25], "idle_back": [37],
            "idle_frontright": [16], "idle_frontleft": [4], "idle_backleft": [28], "idle_backright": [40],
            "walk_front": [0, 2], "walk_left": [12, 14], "walk_right": [24, 26], "walk_back": [36, 38],
            "walk_frontright": [15, 17], "walk_frontleft": [3, 5], "walk_backright": [39, 41], "walk_backleft": [27, 29]
        }
        return animations

    # === GESTION DES ENTRÉES ===
    
    def handle_input(self, keys):
        """
        Traite les entrées clavier pour le mouvement
        
        Args:
            keys: État des touches (pygame.key.get_pressed())
        """
        dx = dy = 0
        if keys[pygame.K_UP] or keys[pygame.K_z]: dy += 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: dy -= 1
        if keys[pygame.K_LEFT] or keys[pygame.K_q]: dx += 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx -= 1

        # Mode libre avec F (pour explorer le vide)
        if 102 in keys:  # 102 = ord('f')
            self.free_mode = True
        else:
            self.free_mode = False
        
        self.input_vector = (dx, dy)
        self.moving = (dx != 0 or dy != 0)
        self.direction = self.compute_direction(dx, dy)

    def compute_direction(self, dx, dy):
        """
        Calcule la direction du personnage selon le vecteur de mouvement
        
        Args:
            dx, dy: Composantes du vecteur de déplacement
            
        Returns:
            str: Nom de la direction pour l'animation
        """
        direction_map = {
            (-1, -1): "frontright",
            (1, -1): "frontleft", 
            (-1, 1): "backright",
            (1, 1): "backleft",
            (0, 1): "back",
            (0, -1): "front",
            (-1, 0): "right",
            (1, 0): "left"
        }
        
        new_direction = direction_map.get((dx, dy), self.direction)
        return new_direction
    # === MISE À JOUR DU PERSONNAGE ===
    
    def update(self, dt):
        """
        MISE À JOUR SIMPLIFIÉE - Standardise l'utilisation de stable_tile_pos comme
        source unique de vérité pour la position du personnage
        """
        keys = pygame.key.get_pressed()
        self.handle_input(keys)

        if self.moving:
            self.move(dt)  # Mouvement avec système hybride intelligent
            self.anim_state = f"walk_{self.direction}"
        else:
            self.anim_state = f"idle_{self.direction}"

        self.update_animation(dt)

        # Vérifier les transitions seulement si stable_tile_pos a changé
        if self.stable_tile_pos != self.tile_pos:
            self.tile_pos = list(self.stable_tile_pos)
            
            # Vérifier les transitions (portails) directement avec stable_tile_pos
            transition = self.world_manager.check_transition(*self.stable_tile_pos)
            if transition:
                self._handle_transition(transition)
        
    # === SYSTÈME DE MOUVEMENT ===
    
    def _handle_transition(self, transition):
        """Gère les transitions de zone - Méthode optimisée centralisée."""
        print(f"[TRANSITION] Passage vers {transition['target_map']} depuis position {self.stable_tile_pos}")
        self.world_manager.change_zone(transition['target_map'])
        
        # Respawn au nouveau spawn - Centralisation des calculs
        spawn_tile = self.world_manager.get_spawn_position()
        spawn_layer = self.world_manager.get_spawn_layer()
        spawn_pixel = self.world_manager.tile_to_pixel(*spawn_tile)
        
        # Mise à jour unifiée de toutes les positions
        self.tile_pos = list(spawn_tile)
        self.stable_tile_pos = list(spawn_tile)
        self.pixel_pos = list(spawn_pixel)
        self.position["layer"] = spawn_layer
        self.height_offset = self._get_height_offset(*spawn_tile)
        
        # Réinitialiser la protection après transition
        self.last_spawn_time = pygame.time.get_ticks()
    
    def move(self, dt):
        """Mouvement simplifié avec position standardisée"""
        dx, dy = self.input_vector
        if dx == 0 and dy == 0:
            return
        
        # Calculer nouvelle position pixel
        dt_seconds = max(float(dt) / 1000.0, 0.016)
        distance = self.speed * dt_seconds
        new_pixel_x = self.pixel_pos[0] + dx * distance
        new_pixel_y = self.pixel_pos[1] + dy * distance
        
        # Convertir en coordonnées de tuile
        new_tile_x, new_tile_y = self.world_manager.pixel_to_tile(new_pixel_x, new_pixel_y)
        
        # Vérifier si on change de tuile
        if (new_tile_x, new_tile_y) != (self.position["x"], self.position["y"]):
            if self.free_mode:
                # Mode libre: ignorer collisions
                self.position["x"] = new_tile_x
                self.position["y"] = new_tile_y
                
                # Mettre à jour les variables pour compatibilité
                self.tile_pos = [new_tile_x, new_tile_y]
                self.stable_tile_pos = [new_tile_x, new_tile_y]
            else:
                # Valider le mouvement
                result = self.world_manager.can_move(
                    self.position["x"], self.position["y"],
                    new_tile_x, new_tile_y, self.position["layer"])
                
                if result["can_move"]:
                    # Mettre à jour position et layer
                    self.position["x"] = new_tile_x
                    self.position["y"] = new_tile_y
                    self.position["layer"] = result["target_layer"]
                    
                    # Mettre à jour les variables pour compatibilité
                    self.tile_pos = [new_tile_x, new_tile_y]
                    self.stable_tile_pos = [new_tile_x, new_tile_y]
                else:
                    return  # Mouvement bloqué
            
            # Mise à jour de la hauteur pour le rendu
            self.height_offset = self._get_height_offset(self.position["x"], self.position["y"])
        
        # Mise à jour position pixel
        self.pixel_pos[0] = new_pixel_x
        self.pixel_pos[1] = new_pixel_y

    # === SYSTÈME DE COLLISION ET CHUTE ===
    
    def trigger_fall(self):
        """
        Déclenche la chute du joueur et change de monde selon les règles définies
        """
        print("[CHAR.trigger_fall] Appelée - CHUTE ! Le joueur tombe dans le vide...")

        # Changer de monde à la chute selon les destinations définies
        if hasattr(self, "world_manager") and self.world_manager:
            print("[CHAR.trigger_fall] Changement de map suite à la chute...")
            fall_destination = self.world_manager.get_fall_destination()
            if fall_destination:
                print(f"[CHAR.trigger_fall] Destination de chute: {fall_destination}")
                self.world_manager.change_zone(fall_destination)
                
                # Respawn au nouveau spawn
                spawn_tile = self.world_manager.get_spawn_position()
                spawn_pixel = self.world_manager.tile_to_pixel(*spawn_tile)
                self.tile_pos = list(spawn_tile)
                self.pixel_pos = list(spawn_pixel)
                self.position["layer"] = self.world_manager.get_height_at(*spawn_tile)
                self.height_offset = self._get_height_offset(*spawn_tile)
                print(f"[CHAR.trigger_fall] 🔄 Respawn au spawn: tuile {self.tile_pos}, couche {self.position['layer']}")
            else:
                print("[CHAR.trigger_fall] Aucune destination de chute trouvée")
        else:
            print("[CHAR.trigger_fall] Impossible de changer de monde : world_manager manquant")
        
        print("[CHAR.trigger_fall] Terminée")
    
    def _get_height_offset(self, tile_x, tile_y):
        """
        Calcule l'offset de hauteur basé sur le layer le plus haut à la position donnée.
        """
        tiles = [t for t in self.world_manager.zone.get_all_tiles_with_pos() if t["x"] == tile_x and t["y"] == tile_y]
        if tiles:
            highest_layer = max(t["z"] for t in tiles)
            offset = -(highest_layer * 16)
            return offset
        return 0

    # === ANIMATION ===
    
    def update_animation(self, dt):
        """
        Met à jour l'animation du personnage
        
        Args:
            dt: Delta time en millisecondes
        """
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
        """
        Récupère la frame actuelle de l'animation
        
        Returns:
            pygame.Surface: Image de la frame courante
        """
        frames = self.animations.get(self.anim_state)
        if not frames:
            return self.frames[0]
        
        frame_index = frames[self.anim_index % len(frames)]
        return self.frames[frame_index]


    # --- Positionnement ---
    def get_pixel_to_iso(self, camera):
        """Position d'affichage avec offset de hauteur pour effet 3D"""
        base_x = self.pixel_pos[0] - camera.x
        base_y = self.pixel_pos[1] - camera.y + self.height_offset
        return base_x, base_y

    # --- Dessin ---
    def draw(self, surface, camera):
        """Rendu optimisé du personnage"""
        frame = self.get_current_frame()
        
        # Position de rendu avec offset de hauteur
        final_x = self.pixel_pos[0] - camera.x
        final_y = self.pixel_pos[1] - camera.y + self.height_offset
        
        # Centrage du sprite
        draw_x = final_x - frame.get_width() // 2
        draw_y = final_y - frame.get_height() + 16
        
        surface.blit(frame, (draw_x, draw_y))
        
        self.draw_debug_info(surface, camera)  # Afficher les infos de debug

    def draw_debug_info(self, surface, camera):
        """Affiche les informations de debug (position, layer) en temps réel"""
        # Création d'une police pour le texte
        font = pygame.font.SysFont("Arial", 14, bold=True)
        
        # Position et layer
        pos_text = f"Position: ({self.position['x']}, {self.position['y']}, L{self.position['layer']})"
        pos_surface = font.render(pos_text, True, (255, 255, 0))
        
        # Tuiles autour (aux 4 directions cardinales)
        tiles_text = "Tuiles autour: "
        all_tiles = self.world_manager.zone.get_all_tiles_with_pos()
        
        # Compter les tuiles dans chaque direction (N, E, S, O)
        north = [t for t in all_tiles if t["x"] == self.position["x"] and t["y"] == self.position["y"]-1]
        east = [t for t in all_tiles if t["x"] == self.position["x"]+1 and t["y"] == self.position["y"]]
        south = [t for t in all_tiles if t["x"] == self.position["x"] and t["y"] == self.position["y"]+1]
        west = [t for t in all_tiles if t["x"] == self.position["x"]-1 and t["y"] == self.position["y"]]
        
        tiles_text += f"N:{len(north)} E:{len(east)} S:{len(south)} W:{len(west)}"
        tiles_surface = font.render(tiles_text, True, (255, 255, 0))
        
        # Walkable status
        walkable_n = any(t["is_walkable"] for t in north)
        walkable_e = any(t["is_walkable"] for t in east)
        walkable_s = any(t["is_walkable"] for t in south)
        walkable_w = any(t["is_walkable"] for t in west)
        walk_text = f"Walkable: N:{walkable_n} E:{walkable_e} S:{walkable_s} W:{walkable_w}"
        walk_surface = font.render(walk_text, True, (255, 255, 0))
        
        # Afficher les textes
        surface.blit(pos_surface, (10, 10))
        surface.blit(tiles_surface, (10, 30))
        surface.blit(walk_surface, (10, 50))