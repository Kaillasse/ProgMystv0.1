import pygame

# Import des classes PNJ individuelles
from game.pnj.dame_indenta import DameIndenta
from game.pnj.neuill import Neuill
from game.pnj.json import JSON
from game.pnj.loopfang import Loopfang


class PNJManager:
    def __init__(self, world):
        self.world = world
        self.active_npcs = []
    def load_npcs(self):
        """Charge tous les PNJ de la clairière en validant leurs positions sur la grille du monde"""
        print("[NPC_MGR] === CHARGEMENT PNJ CLAIRIÈRE ===")
        self.active_npcs = []
        print("[NPC_MGR] Chargement de tous les PNJ dans la clairière...")

        # Liste des PNJ à charger avec leur classe et start_tile par défaut
        npc_classes = [
            (DameIndenta, (4, 8)),
            (Neuill, (1, 6)),
            (JSON, (3, 6)),
            (Loopfang, (1, 8)),
        ]

        for npc_cls, default_tile in npc_classes:
            if self.world.is_valid_tile_position(*default_tile):
                valid_tile = default_tile
            try:
                npc = npc_cls(start_tile=valid_tile)
                npc.tile_pos = list(valid_tile)
                npc.world = self.world
                if hasattr(self.world, 'session'):
                    npc.load_progress_from_session(self.world.session)
                self.active_npcs.append(npc)
            except (ImportError, AttributeError) as e:
                print(f"[NPC_MGR] ✗ Erreur lors du spawn de {npc_cls.__name__}: {e}")

        print(f"[NPC_MGR] === RÉSULTAT: {len(self.active_npcs)} PNJ chargés dans la clairière ===")

    def get_active_npcs(self):
        """Retourne la liste des PNJ actifs de la clairière"""
        return self.active_npcs

    def update(self, dt):
        """Met à jour tous les PNJ actifs"""
        for npc in self.active_npcs:
            if hasattr(npc, 'update_animation'):
                npc.update_animation(dt)
    
    def draw(self, screen, camera_offset=(0, 0)):
        """Dessine tous les PNJ actifs """
        for npc in self.active_npcs:
            # Conversion tuile → pixel (CORRECTION)
            npc_pixel_x, npc_pixel_y = self.world.tile_to_pixel(*npc.tile_pos)
            draw_x = npc_pixel_x + camera_offset[0]
            draw_y = npc_pixel_y + camera_offset[1]

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
        """Gère les clics sur les PNJ - test précis sur le sprite"""
        for npc in self.active_npcs:
            npc_pixel_x, npc_pixel_y = self.world.tile_to_pixel(*npc.tile_pos)
            frame = npc.get_current_frame() if hasattr(npc, 'get_current_frame') else getattr(npc, 'sprite', None)
            if frame:
                rect = frame.get_rect(topleft=(npc_pixel_x, npc_pixel_y))
                if rect.collidepoint(pixel_x, pixel_y):
                    rel_x = pixel_x - rect.x
                    rel_y = pixel_y - rect.y
                    # Test alpha si disponible et coordonnées valides
                    if (frame.get_bitsize() == 32 and 
                        0 <= rel_x < frame.get_width() and 0 <= rel_y < frame.get_height() and
                        frame.get_at((rel_x, rel_y)).a == 0):
                        continue  # Pixel transparent, ignorer
                    
                    # Interaction unifiée
                    print(f"[NPC_MGR] Interaction avec {npc.name} à la tuile {npc.tile_pos}")
                    if hasattr(npc, 'interact') and hasattr(self.world, 'session'):
                        npc.interact(self.world.session)
                    else:
                        npc.speak()
                    return npc
        return None
