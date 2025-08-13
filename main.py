# === main.py ===
import pygame
import os
import json

from game.game_manager import GameManager
from core.session import SessionManager
from ui.main_menu import ask_player_name
from ui.character_creator import CharacterCreator


def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Progmyst")
    saves = SessionManager.check_existing_saves()
    name = None
    session = None
    if not saves:
        name = ask_player_name(screen)
        if name:
            SessionManager.create_player_files(name)
            session = SessionManager.get_session(name)
            CharacterCreator(screen, session).run()
    else:
        name = saves[0]  # TODO: proposer un vrai menu de sélection
        session = SessionManager.get_session(name)
    if session:
        GameManager(screen, session).run()

if __name__ == "__main__":
    main()