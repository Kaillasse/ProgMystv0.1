# === game/game_manager.py ===
import json
import sys
import pygame
from enum import Enum
from ui.main_menu import MainMenu
from ui.character_creator import CharacterCreator
from ui.interaction import InteractionUI
from core.session import SessionManager
from core.settings import get_player_data_path
from game.world import World
from game.character import Character
from game.camera import Camera
from game.entity import PNJManager
from game.combat_manager import SimpleCombatManager

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
        self.state = GameState.MENU
        self.running = True
        self.clock = pygame.time.Clock()       
        
        # Composants initialisés à la demande
        self.world = None
        self.character = None
        self.camera = None
        self.npc_manager = None
        self.combat_manager = None
        
        # Interface de dialogue - sera réinitialisée avec session dans run()
        self.interaction_ui = None
        
        # Configurer le callback sera fait lors de l'initialisation dans initialize_world()
        
        print(f"[GM] GameManager prêt pour session: {self.name}")

    def handle_dialogue_action(self, action):
        """Gère les actions spéciales déclenchées depuis les dialogues"""
        if action == "start_combat_dame_indenta":
            print("[GM] Déclenchement du combat contre Dame Indenta via dialogue!")
            self.start_combat_with_dame_indenta()
            # On force la sortie du dialogue, le state sera mis à COMBAT
            self.interaction_ui.end_interaction()
        else:
            print(f"[GM] Action de dialogue non reconnue: {action}")

    def get_current_session(self):
        """Récupère la session actuelle via SessionManager"""
        session = SessionManager.get_current_session()
        if session is None:
            print("[GM] ERREUR: Aucune session active!")
        return session

    def handle_menu(self):
        print("[GM] handle_menu()")
        if self.state == GameState.MENU:
            print("[GM] Ouverture du menu principal")

            session = self.get_current_session()
            if not session:
                return

            choice, name = MainMenu(self.screen, session).run()
            print(f"[GM] Choix : {choice}, Joueur : {name}")

            if choice == "new":
                self.state = GameState.CREATOR
            elif choice == "load":
                self.state = GameState.EXPLORATION
            elif choice == "quit":
                self.running = False

    def handle_creator(self):
        print("[GM] handle_creator()")
        if self.state == GameState.CREATOR:
            print("[GM] Ouverture du CharacterCreator")
            session = self.get_current_session()
            if session:
                CharacterCreator(self.screen, session).run()
                session.load_data()  # Recharge les données après création
            self.state = GameState.MENU

    def initialize_world(self):
        """Initialise le World UNE SEULE FOIS"""
        if self.world is None:
            self.world = World(self.screen)  # Plus de paramètre map_name
            self.world.session = self.session  # Donner accès à la session
            # Initialiser le PNJManager
            self.npc_manager = PNJManager(self.world)
            self.npc_manager.spawn_npcs()  # Méthode simplifiée
            
            # Initialiser l'InteractionUI avec la session
            if self.interaction_ui is None:
                self.interaction_ui = InteractionUI(self.screen.get_width(), self.screen.get_height(), session=self.session)
                # Configurer le callback pour les actions spéciales du dialogue
                self.interaction_ui.action_callback = self.handle_dialogue_action
        return self.world

    def initialize_character(self):
        """Initialise le Character UNE SEULE FOIS"""
        if self.character is None:
            session = self.get_current_session()
            world = self.initialize_world()
            self.character = Character(session, world)
        return self.character

    def initialize_camera(self):
        """Initialise la Camera UNE SEULE FOIS"""
        if self.camera is None:
            self.camera = Camera(self.screen.get_width(), self.screen.get_height())
            # Centre sur le personnage
            character = self.initialize_character()
            self.camera.center_on_character(character)
        return self.camera

    def initialize_combat_manager(self):
        """Initialise le CombatManager UNE SEULE FOIS"""
        if self.combat_manager is None:
            world = self.initialize_world()
            self.combat_manager = SimpleCombatManager(world, self.screen)
        return self.combat_manager

    def start_combat_with_dame_indenta(self):
        """Démarre un combat contre Dame Indenta"""
        print("[GM] === DÉBUT DU COMBAT CONTRE DAME INDENTA ===")
        
        # Initialiser le combat manager
        combat_manager = self.initialize_combat_manager()
        session = self.get_current_session()
        
        # Démarrer le combat
        combat_manager.start_combat(session)
        
        # Changer le mode de jeu
        self.state = GameState.COMBAT
        
    def handle_combat(self):
        """Gère le mode combat simplifié"""
        print("[GM] handle_combat() - Nouveau système simplifié")
        
        combat_manager = self.initialize_combat_manager()
        world = self.initialize_world()
        camera = self.initialize_camera()
        
        combat_active = True
        
        while combat_active:
            dt = self.clock.tick(60)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                # Gérer les événements du combat
                combat_result = combat_manager.handle_event(event)
                if combat_result == "end_combat":
                    print("[GM] Sortie du combat")
                    combat_active = False
                    self.state = GameState.EXPLORATION

            # Mise à jour du combat
            combat_manager.update()
            
            # Mettre à jour les boutons
            mouse_pos = pygame.mouse.get_pos()
            combat_manager.update_buttons(mouse_pos)
            
            # Vérification des conditions de fin
            if combat_manager.state.value in ["victory", "defeat"]:
                # Le combat est terminé, mais on reste dans l'interface pour que le joueur puisse voir le résultat
                pass
            
            # Affichage
            self.screen.fill((20, 30, 40))  # Fond sombre pour le combat
            
            # Dessiner le monde (arrière-plan)
            world.draw(self.screen, (camera.x, camera.y))
            
            # Dessiner le combat (unités, interface, boutons)
            combat_manager.draw(self.screen)
            
            pygame.display.flip()

    def handle_exploration(self):
        print("[GM] handle_exploration()")

        # Initialisation des composants (UNE SEULE FOIS)
        world = self.initialize_world()
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
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        print("[GM] Sortie demandée de la phase exploration")
                        exploring = False
                        self.state = GameState.MENU
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Clic gauche
                        # Gestion des clics sur les PNJ
                        mouse_x, mouse_y = pygame.mouse.get_pos()
                        # Ajuster les coordonnées avec l'offset de la caméra
                        world_x = mouse_x - camera.x
                        world_y = mouse_y - camera.y
                        if self.npc_manager:
                            clicked_npc = self.npc_manager.handle_click(world_x, world_y)
                            if clicked_npc:
                                # Passer en mode dialogue
                                print(f"[GM] Clic sur {clicked_npc.name} - Passage en mode dialogue")
                                self.interaction_ui.start_interaction(character, clicked_npc, self.session)
                                self.state = GameState.INTERACTION
                                exploring = False  # Sortir de la boucle d'exploration

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
            world.draw(self.screen, (camera.x, camera.y))

            # === Affichage du personnage ===
            character.draw(self.screen, camera)
            
            # === Affichage des PNJ ===
            if self.npc_manager and self.world:
                self.npc_manager.draw(self.screen, (camera.x, camera.y))

            pygame.display.flip()

    def handle_interaction(self):
        print("[GM] handle_interaction()")
        
        # Initialiser les composants pour l'affichage de fond
        world = self.initialize_world()
        character = self.initialize_character()
        camera = self.initialize_camera()
        
        interacting = True
        
        while interacting:
            dt = self.clock.tick(60)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                # Gérer les événements de dialogue
                dialogue_action = self.interaction_ui.handle_event(event)
                if dialogue_action == "start_combat":
                    print("[GM] Passage en mode combat")
                    self.state = GameState.COMBAT
                    interacting = False
                if dialogue_action == "end"or event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    print("[GM] Dialogue terminé - Retour à l'exploration ou combat")
                    # Si le state a été changé à COMBAT par une action spéciale, on ne repasse pas à EXPLORATION
                    self.interaction_ui.end_interaction()
                    if self.state == GameState.COMBAT:
                        interacting = False
                    else:
                        self.state = GameState.EXPLORATION
                        interacting = False

            
            # Mise à jour de l'interface de dialogue
            mouse_pos = pygame.mouse.get_pos()
            self.interaction_ui.update(mouse_pos)
            
            # === Affichage ===
            self.screen.fill((20, 30, 40))  # Bleu foncé
            
            # Dessiner le monde en arrière-plan (statique)
            world.draw(self.screen, (camera.x, camera.y))
            
            # Dessiner le personnage (statique)
            character.draw(self.screen, camera)
            
            # Dessiner les PNJ (statique)
            if self.npc_manager and self.world:
                self.npc_manager.draw(self.screen, (camera.x, camera.y))
            
            # Dessiner l'interface de dialogue par-dessus
            self.interaction_ui.render(self.screen)
            
            pygame.display.flip()

    def run(self):
        while self.running:
            if self.state == GameState.MENU:
                self.handle_menu()
            elif self.state == GameState.CREATOR:
                self.handle_creator()
            elif self.state == GameState.EXPLORATION:
                self.handle_exploration()
            elif self.state == GameState.INTERACTION:
                self.handle_interaction()
            elif self.state == GameState.COMBAT:
                self.handle_combat()
            # ... gestion du quit, etc.

        print("[GM] GameManager terminé")

class GameState(Enum):
    MENU = "menu"
    CREATOR = "creator"
    EXPLORATION = "exploration"
    INTERACTION = "interaction"
    COMBAT = "combat"