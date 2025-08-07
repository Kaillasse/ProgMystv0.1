# === game/camera.py ===
class Camera:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.x = 0
        self.y = 0
        self._last_pos = (0, 0)

    def follow(self, target):
        """Suit le personnage (méthode legacy)"""
        self.center_on_character(target)

    def center_on_character(self, character):
        """Centre la caméra sur le personnage (mode exploration) en utilisant la position de rendu logique."""
        pixel_x, pixel_y = character.get_render_position()
        new_x = pixel_x - self.width // 2
        new_y = pixel_y - self.height // 2
        # Affiche seulement si la position change significativement
        if abs(new_x - self._last_pos[0]) > 1 or abs(new_y - self._last_pos[1]) > 1:
            self._last_pos = (new_x, new_y)
        self.x = new_x
        self.y = new_y

    def apply(self, pos):
        """Applique l'offset de la caméra à une position"""
        return pos[0] - self.x, pos[1] - self.y

    def get_offset(self):
        """Retourne l'offset actuel de la caméra"""
        return (self.x, self.y)
