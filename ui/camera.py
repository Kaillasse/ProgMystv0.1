from game.character import Character
from core.session import GameSession

# === game/camera.py ===
class Camera:
    def center_on_character(self, character):
        """
        Centre la caméra sur le personnage (mode exploration).
        """
        self.x = character.pixel_pos[0] - self.width // 2
        self.y = character.pixel_pos[1] - self.height // 2
        print(f"[CAMERA] Centrage de la caméra sur le personnage à la position : {character.pixel_pos[0]}, {character.pixel_pos[1]}")
    def __init__(self, width, height, x=0, y=0):
        """
        Initialise la caméra.
        """
        self.width = width
        self.height = height
        self.x = x
        self.y = y


    def follow(self, target):
        self.x = target.pixel_pos[0] - self.width // 2
        self.y = target.pixel_pos[1] - self.height // 2
        print(f"[CAMERA] Suivi du personnage à la position : {target.pixel_pos[0]}, {target.pixel_pos[1]}") 

    def apply(self, pos):
        return pos[0] - self.x, pos[1] - self.y
