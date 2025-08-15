class Camera:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.x = 0
        self.y = 0

    def follow(self, target):
        self.center_on_character(target)

    def center_on_character(self, character):
        if hasattr(character, 'get_screen_position'):
            screen_x, screen_y = character.get_screen_position()
            self.x = screen_x - self.width // 2
            self.y = screen_y - self.height // 2

    def center_on_position(self, x, y):
        self.x = x - self.width // 2
        self.y = y - self.height // 2

    def apply(self, pos):
        return pos[0] - self.x, pos[1] - self.y

    def get_offset(self):
        return (self.x, self.y)