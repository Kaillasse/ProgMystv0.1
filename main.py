# === main.py ===
import pygame
import os
import json

from game.game_manager import GameManager
from core.session_manager import SessionManager
from core.settings import get_player_data_path, get_grimoire_path
from ui.main_menu import ask_player_name
from ui.character_creator import CharacterCreator

def check_existing_saves():
    return [f[:-5] for f in os.listdir("data") if f.endswith(".json")]

def create_player_files(name):
    with open(get_grimoire_path(name), "w") as f:
        f.write(f"# Grimoire de {name}\n\n")
    player_data = {"name": name, "progress": {}, "bust": {}, "sprite": {}}
    with open(get_player_data_path(name), "w", encoding="utf-8") as f:
        json.dump(player_data, f, indent=4)

def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Progmyst")
    saves = check_existing_saves()
    name = None
    session = None
    if not saves:
        name = ask_player_name(screen)
        if name:
            create_player_files(name)
            session = SessionManager.get_session(name)
            CharacterCreator(screen, session).run()
    else:
        name = saves[0]  # TODO: proposer un vrai menu de sélection
        session = SessionManager.get_session(name)
    if session:
        GameManager(screen, session).run()

if __name__ == "__main__":
    main()
q