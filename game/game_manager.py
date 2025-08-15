import json
import sys
import pygame
from enum import Enum
from ui.main_menu import MainMenu
from ui.character_creator import CharacterCreator
from ui.interaction import InteractionUI
from ui.quest_table import QuestTable
from ui.uitools import QuestButton
from core.session import SessionManager
from core.settings import get_player_data_path
from game.world import World
from game.character import Character
from game.camera import Camera
from game.entity import PNJManager
from game.combat_manager import SimpleCombatManager

class GameState(Enum):
    MENU = "menu"
    CREATOR = "creator"
    EXPLORATION = "exploration"
    INTERACTION = "interaction"
    COMBAT = "combat"
    QUEST_TABLE = "quest_table"

def load_player_data(name):
    path = get_player_data_path(name)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

class GameManager:
    def __init__(self, screen, session=None):
        self.screen = screen
        self.session = session
        self.name = session.name if session else "unknown"
        self.state = GameState.MENU
        self.running = True
        self.clock = pygame.time.Clock()
        
        self.world = None
        self.character = None
        self.camera = None
        self.npc_manager = None
        self.combat_manager = None
        self.interaction_ui = None
        self.quest_table = None
        self.quest_button = None
        self.previous_state = None  # Pour retourner au state précédent
        
    def get_current_session(self):
        session = SessionManager.get_current_session()
        if session is None:
            print("[GM] ERREUR: Aucune session active!")
        return session

    def handle_menu(self):
        if self.state == GameState.MENU:
            session = self.get_current_session()
            if not session:
                return

            choice, name = MainMenu(self.screen, session).run()

            if choice == "new":
                self.state = GameState.CREATOR
            elif choice == "load":
                self.state = GameState.EXPLORATION
            elif choice == "quit":
                self.running = False

    def handle_creator(self):
        if self.state == GameState.CREATOR:
            session = self.get_current_session()
            if session:
                CharacterCreator(self.screen, session).run()
                session.load_data()
            self.state = GameState.MENU

    def initialize_world(self):
        if self.world is None:
            self.world = World(self.screen)
            self.world.session = self.session
            self.npc_manager = PNJManager(self.world)
            self.npc_manager.spawn_npcs()
            
            if self.interaction_ui is None:
                self.interaction_ui = InteractionUI(
                    self.screen.get_width(), 
                    self.screen.get_height(), 
                    session=self.session
                )
        return self.world

    def initialize_character(self):
        if self.character is None:
            session = self.get_current_session()
            world = self.initialize_world()
            self.character = Character(session, world)
        return self.character

    def initialize_camera(self):
        if self.camera is None:
            self.camera = Camera(self.screen.get_width(), self.screen.get_height())
            character = self.initialize_character()
            self.camera.center_on_character(character)
        return self.camera

    def initialize_combat_manager(self):
        if self.combat_manager is None:
            world = self.initialize_world()
            self.combat_manager = SimpleCombatManager(world, self.screen)
        return self.combat_manager

    def handle_exploration(self):
        world = self.initialize_world()
        character = self.initialize_character()
        camera = self.initialize_camera()
        quest_button = self.initialize_quest_button()

        exploring = True

        while exploring:
            dt = self.clock.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        exploring = False
                        self.state = GameState.MENU
                    elif event.key == pygame.K_F1:
                        # Debug: print entity positions
                        world.print_entity_positions()
                
                # Gestion du bouton de quête
                quest_result = self.handle_quest_button_event(event)
                if quest_result == "quest_table_opened":
                    exploring = False
                    continue
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        mouse_x, mouse_y = pygame.mouse.get_pos()
                        world_x = mouse_x - camera.x
                        world_y = mouse_y - camera.y
                        if self.npc_manager:
                            clicked_npc = self.npc_manager.handle_click(world_x, world_y)
                            if clicked_npc:
                                self.interaction_ui.start_interaction(character, clicked_npc, self.session)
                                self.state = GameState.INTERACTION
                                exploring = False

            keys = pygame.key.get_pressed()
            character.handle_input(keys)
            character.update(dt)
            camera.center_on_character(character)

            if self.npc_manager:
                self.npc_manager.update(dt)

            # Met à jour le bouton de quête
            quest_button.update()

            self.screen.fill((20, 30, 40))
            world.draw(self.screen, (camera.x, camera.y))
            character.draw(self.screen, camera)
            
            if self.npc_manager:
                camera_offset = (camera.x, camera.y)
                self.npc_manager.draw(self.screen, camera_offset)
            
            # Dessine le bouton de quête
            quest_button.draw(self.screen)

            pygame.display.flip()

    def handle_interaction(self):
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
                
                dialogue_action = self.interaction_ui.handle_event(event)
                if dialogue_action == "end" or (event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN):
                    self.interaction_ui.end_interaction()
                    self.state = GameState.EXPLORATION
                    interacting = False

            mouse_pos = pygame.mouse.get_pos()
            self.interaction_ui.update(mouse_pos)
            
            self.screen.fill((20, 30, 40))
            world.draw(self.screen, (camera.x, camera.y))
            character.draw(self.screen, camera)
            
            if self.npc_manager:
                camera_offset = (camera.x, camera.y)
                self.npc_manager.draw(self.screen, camera_offset)
            
            self.interaction_ui.render(self.screen)
            pygame.display.flip()

    def handle_combat(self):
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
                
                combat_result = combat_manager.handle_event(event)
                if combat_result == "end_combat":
                    combat_active = False
                    self.state = GameState.EXPLORATION

            combat_manager.update()
            
            mouse_pos = pygame.mouse.get_pos()
            combat_manager.update_buttons(mouse_pos)
            
            self.screen.fill((20, 30, 40))
            world.draw(self.screen, (camera.x, camera.y))
            combat_manager.draw(self.screen)
            
            pygame.display.flip()
    
    def initialize_quest_table(self):
        """Initialise la table des quêtes"""
        if self.quest_table is None:
            session = self.get_current_session()
            screen_width, screen_height = self.screen.get_size()
            self.quest_table = QuestTable(screen_width, screen_height, session)
        return self.quest_table
    
    def initialize_quest_button(self):
        """Initialise le bouton de quête"""
        if self.quest_button is None:
            screen_width, screen_height = self.screen.get_size()
            # Positionne le bouton en bas au centre
            button_x = screen_width // 2 - 50
            button_y = screen_height - 10  # Presque tout en bas
            self.quest_button = QuestButton(button_x, button_y, screen_height)
        return self.quest_button
    
    def handle_quest_table(self):
        """Gère l'état de la table des quêtes"""
        quest_table = self.initialize_quest_table()
        quest_table.show()
        
        quest_table_active = True
        
        while quest_table_active:
            dt = self.clock.tick(60)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                # Gère les événements de la quest table
                result = quest_table.handle_event(event)
                if result == "close" or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    quest_table.hide()
                    quest_table_active = False
                    # Retourne au state précédent
                    self.state = self.previous_state if self.previous_state else GameState.EXPLORATION
                    
                    # Remet le bouton en position
                    if self.quest_button:
                        self.quest_button.reset_position()
            
            # Affichage
            self.screen.fill((30, 30, 50))
            quest_table.render(self.screen, dt)
            
            pygame.display.flip()
    
    def handle_quest_button_event(self, event):
        """Gère les événements du bouton de quête"""
        if not self.quest_button:
            return None
        
        result = self.quest_button.handle_event(event)
        
        if result == "quest_table_open":
            # Sauvegarde l'état actuel et passe à la quest table
            self.previous_state = self.state
            self.state = GameState.QUEST_TABLE
            return "quest_table_opened"
        
        return result

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
            elif self.state == GameState.QUEST_TABLE:
                self.handle_quest_table()

        print("[GM] GameManager terminé")