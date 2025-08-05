# === game/game_manager.py ===
import json
import sys
import pygame
from ui.main_menu import MainMenu
from ui.character_creator import CharacterCreator
from ui.interaction import InteractionUI
from core.session_manager import SessionManager
from core.settings import get_player_data_path
from game.world_manager import WorldManager
from game.character import Character
from game.camera import Camera
from game.npc_manager import NPCManager

def load_player_data(name):
    path = get_player_data_path(name)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

class GameManager:
    def __init__(self, screen, session=None):
        print("[GM] Initialisation GameManager")
        self.screen = screen
        self.session = session
        self.name = session.name if session else "unknown"
        self.state = "menu"
        self.substate = "main"  # Peut être "main", "explo", "dialogue", etc.
        self.running = True
        self.clock = pygame.time.Clock()       
        
        # Composants initialisés à la demande
        self.world_manager = None
        self.character = None
        self.camera = None
        self.npc_manager = None
        
        # Interface de dialogue
        self.interaction_ui = InteractionUI(screen.get_width(), screen.get_height())
        
        print(f"[GM] GameManager prêt pour session: {self.name}")

    def get_current_session(self):
        """Récupère la session actuelle via SessionManager"""
        session = SessionManager.get_current_session()
        if session is None:
            print("[GM] ERREUR: Aucune session active!")
        return session

    def handle_menu(self):
        print("[GM] handle_menu()")
        if self.substate == "main":
            print("[GM] Ouverture du menu principal")

            session = self.get_current_session()
            if not session:
                return

            choice, name = MainMenu(self.screen, session).run()
            print(f"[GM] Choix : {choice}, Joueur : {name}")

            if choice == "new":
                self.state = "creator"
                self.substate = "bust"
            elif choice == "load":
                self.state = "exploration"
                self.substate = "explo"
            elif choice == "quit":
                self.running = False

    def handle_creator(self):
        print("[GM] handle_creator()")
        if self.substate == "bust":
            print("[GM] Ouverture du CharacterCreator")
            session = self.get_current_session()
            if session:
                CharacterCreator(self.screen, session).run()
                session.load_data()  # Recharge les données après création
            self.state = "menu"
            self.substate = "main"

    def initialize_world(self):
        """Initialise le WorldManager UNE SEULE FOIS"""
        if self.world_manager is None:
            self.world_manager = WorldManager("clairiere", self.screen)
            self.world_manager.session = self.session  # Donner accès à la session
            # Initialiser le NPCManager après le WorldManager
            self.npc_manager = NPCManager(self.world_manager)
            self.npc_manager.load_npcs_for_map("clairiere")
        return self.world_manager

    def initialize_character(self):
        """Initialise le Character UNE SEULE FOIS"""
        if self.character is None:
            session = self.get_current_session()
            world_manager = self.initialize_world()
            self.character = Character(session, world_manager)
        return self.character

    def initialize_camera(self):
        """Initialise la Camera UNE SEULE FOIS"""
        if self.camera is None:
            self.camera = Camera(self.screen.get_width(), self.screen.get_height())
            # Centre sur le personnage
            character = self.initialize_character()
            self.camera.center_on_character(character)
        return self.camera

    def handle_exploration(self):
        print("[GM] handle_exploration()")

        # Initialisation des composants (UNE SEULE FOIS)
        world_manager = self.initialize_world()
        character = self.initialize_character()
        camera = self.initialize_camera()

        exploring = True
        frame_count = 0

        while exploring:
            frame_count += 1
            dt = self.clock.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                # Gestion des événements selon le substate
                if self.substate == "dialogue":
                    # En mode dialogue, seuls certains événements sont traités
                    dialogue_action = self.interaction_ui.handle_event(event)
                    if dialogue_action == "end":
                        print("[GM] Dialogue terminé - Retour à l'exploration")
                        self.substate = "explo"
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        print("[GM] Escape pressé - Fin du dialogue")
                        self.interaction_ui.end_interaction()
                        self.substate = "explo"
                else:
                    # Mode exploration normal
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            print("[GM] Sortie demandée de la phase exploration")
                            exploring = False
                            self.state = "menu"
                            self.substate = "main"
                        elif event.key == pygame.K_TAB:
                            # Gestion centralisée du changement de zone
                            self.change_zone(character)
                    
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        if event.button == 1:  # Clic gauche
                            # Gestion des clics sur les PNJ
                            mouse_x, mouse_y = pygame.mouse.get_pos()
                            # Ajuster les coordonnées avec l'offset de la caméra
                            world_x = mouse_x - camera.x
                            world_y = mouse_y - camera.y
                            if self.npc_manager:
                                clicked_npc = self._get_clicked_npc(world_x, world_y)
                                if clicked_npc:
                                    # Passer en mode dialogue
                                    print(f"[GM] Clic sur {clicked_npc.name} - Passage en mode dialogue")
                                    self.substate = "dialogue"
                                    self.interaction_ui.start_interaction(character, clicked_npc, self.session)

            # === Mise à jour selon le substate ===
            if self.substate == "dialogue":
                # En mode dialogue, on met à jour seulement l'interface
                mouse_pos = pygame.mouse.get_pos()
                self.interaction_ui.update(mouse_pos)
            else:
                # Mode exploration - mise à jour normale
                keys = pygame.key.get_pressed()
                character.handle_input(keys)
                character.update(dt)
                camera.center_on_character(character)

                # === Mise à jour des PNJ ===
                if self.npc_manager:
                    self.npc_manager.update(dt)

            # === Affichage ===
            self.screen.fill((20, 30, 40))  # Bleu foncé
            
            # Dessiner le monde via WorldManager
            world_manager.draw(self.screen, (camera.x, camera.y))

            # === Affichage du personnage ===
            character.draw(self.screen, camera)
            
            # === Affichage des PNJ ===
            if self.npc_manager:
                self.npc_manager.draw(self.screen, (camera.x, camera.y))

            # === Affichage de l'interface de dialogue ===
            if self.substate == "dialogue":
                self.interaction_ui.render(self.screen)

            pygame.display.flip()

    def change_zone(self, character):
        """Gère le changement de zone via Tab."""
        if not self.world_manager or not character:
            return
        
        # Déclencher la chute du personnage
        player_x, player_y = character.tile_pos
        print(f"[GM] Tab pressé - Position actuelle: ({player_x}, {player_y})")
        print("[GM] Déclenchement de trigger_fall...")
        character.trigger_fall()
        
        # Recharger les PNJ pour la nouvelle zone
        if self.npc_manager:
            current_map = self.world_manager.zone.map_name
            self.npc_manager.load_npcs_for_map(current_map)

    def run(self):
        print("[GM] GameManager.run() démarré")
        while self.running:
            print(f"[GM] État actuel : {self.state} / Sous-état : {self.substate}")
            if self.state == "menu":
                self.handle_menu()

            elif self.state == "creator":
                self.handle_creator()

            elif self.state == "exploration":
                self.handle_exploration()

        print("[GM] GameManager terminé")

    def _get_clicked_npc(self, world_x, world_y):
        """
        Retourne le PNJ cliqué ou None
        
        Args:
            world_x, world_y: Coordonnées dans le monde (avec offset caméra appliqué)
            
        Returns:
            NPC ou None
        """
        if not self.npc_manager:
            return None
            
        for npc in self.npc_manager.active_npcs:
            # Vérifier si le clic est sur le PNJ (zone approximative)
            pixel_x, pixel_y = self.world_manager.tile_to_pixel(*npc.tile_pos)
            npc_rect = pygame.Rect(pixel_x, pixel_y, 48, 96)
            if npc_rect.collidepoint(world_x, world_y):
                return npc
        return None
