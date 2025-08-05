import pygame
from game.pnj import DameIndenta, Neuill, JSON, Loopfang

class NPCManager:
    """
    Gestionnaire des PNJ - Gère le spawn, l'affichage et les interactions des PNJ
    """
    
    def __init__(self, world_manager):
        self.world_manager = world_manager
        self.npcs = {}  # Dict des PNJ par map
        self.active_npcs = []  # PNJ actifs sur la map actuelle
        
    def load_npcs_for_map(self, map_name):
        """Charge les PNJ pour une map donnée"""
        print(f"[NPC_MGR] === CHARGEMENT PNJ POUR MAP: {map_name} ===")
        self.active_npcs = []
        
        if map_name == "clairiere":
            print(f"[NPC_MGR] Chargement de tous les PNJ dans la clairière...")
            
            # Spawner Dame Indenta dans clairiere
            try:
                dame_indenta = DameIndenta()
                dame_indenta.world_manager = self.world_manager  # Donner accès au world_manager
                # Charger la progression si la session est disponible
                if hasattr(self.world_manager, 'session'):
                    dame_indenta.load_progress_from_session(self.world_manager.session)
                self.active_npcs.append(dame_indenta)
                # Debug de position au chargement
                pixel_x, pixel_y = self.world_manager.tile_to_pixel(*dame_indenta.tile_pos)
                print(f"[NPC_MGR] ✓ Dame Indenta spawnée - tuile {dame_indenta.tile_pos} -> pixel ({pixel_x}, {pixel_y})")
            except Exception as e:
                print(f"[NPC_MGR] ✗ Erreur lors du spawn de Dame Indenta: {e}")
                import traceback
                traceback.print_exc()
            
            # Spawner Neuill dans clairiere pour debug
            try:
                neuill = Neuill()
                neuill.world_manager = self.world_manager
                if hasattr(self.world_manager, 'session'):
                    neuill.load_progress_from_session(self.world_manager.session)
                self.active_npcs.append(neuill)
                # Debug de position au chargement
                pixel_x, pixel_y = self.world_manager.tile_to_pixel(*neuill.tile_pos)
                print(f"[NPC_MGR] ✓ Neuill spawnée - tuile {neuill.tile_pos} -> pixel ({pixel_x}, {pixel_y})")
            except Exception as e:
                print(f"[NPC_MGR] ✗ Erreur lors du spawn de Neuill: {e}")
                import traceback
                traceback.print_exc()
            
            # Spawner JSON dans clairiere pour debug
            try:
                json_npc = JSON()
                json_npc.world_manager = self.world_manager
                if hasattr(self.world_manager, 'session'):
                    json_npc.load_progress_from_session(self.world_manager.session)
                self.active_npcs.append(json_npc)
                # Debug de position au chargement
                pixel_x, pixel_y = self.world_manager.tile_to_pixel(*json_npc.tile_pos)
                print(f"[NPC_MGR] ✓ JSON spawnée - tuile {json_npc.tile_pos} -> pixel ({pixel_x}, {pixel_y})")
            except Exception as e:
                print(f"[NPC_MGR] ✗ Erreur lors du spawn de JSON: {e}")
                import traceback
                traceback.print_exc()
            
            # Spawner Loopfang dans clairiere pour debug
            try:
                loopfang = Loopfang()
                loopfang.world_manager = self.world_manager
                if hasattr(self.world_manager, 'session'):
                    loopfang.load_progress_from_session(self.world_manager.session)
                self.active_npcs.append(loopfang)
                # Debug de position au chargement
                pixel_x, pixel_y = self.world_manager.tile_to_pixel(*loopfang.tile_pos)
                print(f"[NPC_MGR] ✓ Loopfang spawnée - tuile {loopfang.tile_pos} -> pixel ({pixel_x}, {pixel_y})")
            except Exception as e:
                print(f"[NPC_MGR] ✗ Erreur lors du spawn de Loopfang: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"[NPC_MGR] Pas de PNJ configurés pour la map '{map_name}'")
            
        print(f"[NPC_MGR] === RÉSULTAT: {len(self.active_npcs)} PNJ chargés pour '{map_name}' ===")
    
    def update(self, dt):
        """Met à jour tous les PNJ actifs"""
        for npc in self.active_npcs:
            if hasattr(npc, 'update_animation'):
                npc.update_animation(dt)
    
    def draw(self, screen, camera_offset=(0, 0)):
        """Dessine tous les PNJ actifs - Conversion tile vers pixel à la volée"""
        for npc in self.active_npcs:
            # Conversion à la volée de la position tuile vers pixel
            pixel_x, pixel_y = self.world_manager.tile_to_pixel(*npc.tile_pos)
            
            # Position d'affichage avec offset caméra
            draw_x = pixel_x + camera_offset[0]
            draw_y = pixel_y + camera_offset[1]
            
            # Essayer d'abord avec get_current_frame
            frame = None
            if hasattr(npc, 'get_current_frame'):
                frame = npc.get_current_frame()
            
            # Si pas de frame, utiliser le sprite de base ou créer un placeholder
            if not frame:
                if hasattr(npc, 'sprite') and npc.sprite:
                    frame = npc.sprite
                else:
                    # Créer un rectangle coloré temporaire pour debug
                    frame = pygame.Surface((48, 96))
                    if npc.name == "Dame Indenta":
                        frame.fill((255, 0, 0))  # Rouge
                    elif npc.name == "Neuill":
                        frame.fill((0, 255, 0))  # Vert
                    elif npc.name == "JSON":
                        frame.fill((0, 0, 255))  # Bleu
                    elif npc.name == "Loopfang":
                        frame.fill((255, 255, 0))  # Jaune
                    else:
                        frame.fill((255, 0, 255))  # Magenta
            
            if frame:
                screen.blit(frame, (draw_x, draw_y))
    
    def handle_click(self, pixel_x, pixel_y):
        """Gère les clics sur les PNJ - Conversion tile vers pixel à la volée"""
        for npc in self.active_npcs:
            # Conversion à la volée de la position tuile vers pixel
            npc_pixel_x, npc_pixel_y = self.world_manager.tile_to_pixel(*npc.tile_pos)
            
            # Vérifier si le clic est sur le PNJ (zone approximative)
            npc_rect = pygame.Rect(npc_pixel_x, npc_pixel_y, 48, 96)
            if npc_rect.collidepoint(pixel_x, pixel_y):
                print(f"[NPC_MGR] Interaction avec {npc.name} à la tuile {npc.tile_pos}")
                if hasattr(npc, 'interact'):
                    # Passer la session via le world_manager
                    if hasattr(self.world_manager, 'session'):
                        npc.interact(self.world_manager.session)
                    else:
                        npc.speak()
                else:
                    npc.speak()
                return True
        return False
    
    def get_npc_at_tile(self, tile_x, tile_y):
        """Retourne le PNJ à une position tuile donnée"""
        for npc in self.active_npcs:
            if npc.tile_pos[0] == tile_x and npc.tile_pos[1] == tile_y:
                return npc
        return None
