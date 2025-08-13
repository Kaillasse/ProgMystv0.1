import pygame

class Entity:
    """Base class for all game entities (player and NPCs)"""
    def __init__(self, tile_pos, name):
        self.tile_pos = [float(tile_pos[0]), float(tile_pos[1])]
        self.name = str(name)
        self.combat_tile_x = int(tile_pos[0])
        self.combat_tile_y = int(tile_pos[1])
        
        # Attributs de combat par défaut
        self.current_hp = 1
        self.max_hp = 1
        self.is_in_combat = False
        
    def get_current_frame(self):
        """Return current sprite frame (must be implemented)"""
        raise NotImplementedError()
        
    def update(self, dt):
        """Update entity state"""
        pass
        
    def draw(self, screen, world, camera_offset=(0,0)):
        """Draw entity using unified drawing logic"""
        px, py = world.get_entity_pixel_pos(
            self.tile_pos[0], self.tile_pos[1], camera_offset)
        frame = self.get_current_frame()
        if frame:
            screen.blit(frame, (px, py))
    
    @property
    def is_alive(self):
        """Vérifie si l'entité est vivante"""
        return self.current_hp > 0
    
    def take_damage(self, amount):
        """Applique des dégâts à l'entité"""
        self.current_hp = max(0, self.current_hp - amount)
        return self.current_hp <= 0  # Retourne True si l'entité meurt
    
    def heal(self, amount):
        """Soigne l'entité"""
        self.current_hp = min(self.max_hp, self.current_hp + amount)

class PNJManager:
    def __init__(self, world):
        self.world = world
        self.active_npcs = []

    def spawn_npcs(self):
        """Initialise tous les PNJ à leur position centrale via World."""
        # Import des classes PNJ ici pour éviter l'importation circulaire
        from game.pnj.dame_indenta import DameIndenta
        from game.pnj.neuill import Neuill
        from game.pnj.json import JSON
        from game.pnj.loopfang import Loopfang
        
        self.active_npcs = []
        npc_classes = {
            "DameIndenta": DameIndenta,
            "Neuill": Neuill,
            "JSON": JSON,
            "Loopfang": Loopfang,
        }
        for name, cls in npc_classes.items():
            try:
                spawn_x, spawn_y = self.world.get_spawn_position(name)
            except ValueError:
                print(f"[PNJManager] Avertissement: spawn point manquant pour {name}, placement en (0,0)")
                spawn_x, spawn_y = 0, 0
            npc = cls([float(spawn_x), float(spawn_y)])
            # Sécurise le nom du PNJ (doit être une chaîne)
            if not hasattr(npc, "name") or not isinstance(npc.name, str):
                npc.name = name
            self.active_npcs.append(npc)
        print(f"[PNJManager] PNJs spawn at unified positions: {[npc.tile_pos for npc in self.active_npcs]}")

    def get_active_npcs(self):
        """Retourne la liste des PNJ actifs (spawn si vide)"""
        if not self.active_npcs:
            self.spawn_npcs()
        return self.active_npcs

    def update(self, dt):
        """Met à jour tous les PNJ actifs"""
        for npc in self.active_npcs:
            if hasattr(npc, 'update_animation'):
                npc.update_animation(dt)
    
    def draw(self, screen, camera_offset=(0, 0)):
        """Dessine tous les PNJ actifs avec API unifiée"""
        for npc in self.active_npcs:
            # API UNIFIÉE : une seule méthode pour tous
            draw_x, draw_y = self.world.get_entity_pixel_pos(npc.tile_pos[0], npc.tile_pos[1], camera_offset)

            # Récupération frame unifiée
            frame = self._get_npc_frame(npc)
            
            if frame:
                screen.blit(frame, (draw_x, draw_y))
    
    def _get_npc_frame(self, npc):
        """MÉTHODE UNIFIÉE : Récupération des frames PNJ via get_current_frame()"""
        if hasattr(npc, 'get_current_frame'):
            return npc.get_current_frame()
        elif hasattr(npc, 'sprite') and npc.sprite:
            return npc.sprite
        else:
            # Fallback debug: rectangle coloré par PNJ
            frame = pygame.Surface((48, 96))
            colors = {
                "Dame Indenta": (255, 0, 0),   # Rouge
                "Neuill": (0, 255, 0),         # Vert
                "JSON": (0, 0, 255),           # Bleu
                "Loopfang": (255, 255, 0)      # Jaune
            }
            frame.fill(colors.get(npc.name, (255, 0, 255)))  # Magenta par défaut
            return frame

    def handle_click(self, pixel_x, pixel_y):
        """Gère les clics sur les PNJ avec debug unifié"""
        for npc in self.active_npcs:
            # API UNIFIÉE
            npc_pixel_x, npc_pixel_y = self.world.get_entity_pixel_pos(npc.tile_pos[0], npc.tile_pos[1])
            frame = self._get_npc_frame(npc)
            
            if frame:
                rect = frame.get_rect(topleft=(npc_pixel_x, npc_pixel_y))
                if rect.collidepoint(pixel_x, pixel_y):
                    rel_x = pixel_x - rect.x
                    rel_y = pixel_y - rect.y
                    # Test alpha si disponible
                    if (frame.get_bitsize() == 32 and 
                        0 <= rel_x < frame.get_width() and 0 <= rel_y < frame.get_height() and
                        frame.get_at((rel_x, rel_y)).a == 0):
                        continue  # Pixel transparent
                    
                    # DEBUG INFO UNIFIÉ via World
                    self._debug_npc_interaction(npc)
                    
                    # Interaction
                    if hasattr(npc, 'interact') and hasattr(self.world, 'session'):
                        npc.interact(self.world.session)
                    else:
                        npc.speak()
                    return npc
        return None
    
    def _debug_npc_interaction(self, npc):
        """DEBUG : Affiche les infos détaillées du PNJ via les méthodes unifiées de World"""
        print(f"[NPC_MGR] === INTERACTION AVEC {npc.name} ===")
        grid_x, grid_y = self.world.get_grid_position(npc)
        pixel_x, pixel_y = self.world.get_entity_pixel_pos(npc.tile_pos[0], npc.tile_pos[1])
        combat_pos = f"combat({getattr(npc, 'combat_tile_x', '?')}, {getattr(npc, 'combat_tile_y', '?')})"
        
        print("[NPC_MGR] Position détaillée:")
        print(f"[NPC_MGR]   tile_pos: ({npc.tile_pos[0]:.2f}, {npc.tile_pos[1]:.2f})")
        print(f"[NPC_MGR]   grid: ({grid_x}, {grid_y})")
        print(f"[NPC_MGR]   {combat_pos}")
        print(f"[NPC_MGR]   pixel: ({pixel_x:.1f}, {pixel_y:.1f})")
        print("[NPC_MGR] ==========================")
