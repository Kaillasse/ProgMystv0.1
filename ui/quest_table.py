import pygame
from core.quest import Quest
from core.session import SessionManager

# Renvoie la listes des quetes donnée et accomplies par le joueur
starquest1_sprite = pygame.image.load("assets/other/questStar.png").convert_alpha()
starquest2_sprite = pygame.image.load("assets/other/queststar2.png").convert_alpha()
secretstarquest_sprite = pygame.image.load("assets/other/secretstar.png").convert_alpha()
uncompleted_quest_sprite = pygame.image.load("assets/other/uncompletedquest.png").convert_alpha()

def get_player_quests(player):
    return {
        "active": [quest for quest in player.quests if quest.status == "active"],
        "completed": [quest for quest in player.quests if quest.status == "completed"]
    }