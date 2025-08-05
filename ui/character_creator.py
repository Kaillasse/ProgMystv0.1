# === ui/character_creator.py ===
import pygame
import json
import os
from core.iso_creator import create_iso_sprite
from PIL import Image

ASSET_PATH = "assets/Bust"
CATEGORIES = [
    "hair", "base", "head", "ears", "eyebrows", "nose", "mouth",
    "rear_hair", "front_hair", "eyes", "clothes", "accessory"
]

class CharacterCreator:
    def __init__(self, screen, session):
        self.screen = screen
        self.session = session
        self.player_name = session.name
        self.base_type = "1"
        self.assets = {cat: [] for cat in CATEGORIES}
        self.original_pil_assets = {cat: [] for cat in CATEGORIES}
        self.indices = {cat: 0 for cat in CATEGORIES}
        self.colors = {cat: None for cat in CATEGORIES}
        self.current_category_index = 0
        self.color_r = 128
        self.color_g = 128
        self.color_b = 128
        self.load_assets()
        self.running = True
        self.data_path = os.path.join("data", f"{self.player_name}.json")

        if os.path.exists(self.data_path):
            with open(self.data_path, "r", encoding="utf-8") as f:
                self.player_data = json.load(f)
            if "buste" in self.player_data:
                for cat in CATEGORIES:
                    self.indices[cat] = self.player_data["buste"].get(cat, {}).get("index", 0)
                    self.colors[cat] = self.player_data["buste"].get(cat, {}).get("color")
                    if self.colors[cat]:
                        self.apply_color_pil(cat, tuple(self.colors[cat]))
        else:
            self.player_data = {}

    def load_assets(self):
        for cat in CATEGORIES:
            path = os.path.join(ASSET_PATH, cat, self.base_type)
            if os.path.exists(path):
                self.assets[cat] = []
                self.original_pil_assets[cat] = []
                for f in sorted(os.listdir(path)):
                    if f.endswith(".png"):
                        img_path = os.path.join(path, f)
                        pil_img = Image.open(img_path).convert("RGBA")
                        self.original_pil_assets[cat].append(pil_img)
                        mode = pil_img.mode
                        size = pil_img.size
                        data = pil_img.tobytes()
                        pg_img = pygame.image.fromstring(data, size, mode)
                        self.assets[cat].append(pg_img)
            else:
                print(f"[WARN] Aucun asset trouvé pour {cat} avec base_type {self.base_type}")

    def draw_preview(self):
        self.screen.fill((40, 40, 40))
        base_x, base_y = 300, 100
        for cat in CATEGORIES:
            if self.assets[cat]:
                sprite = self.assets[cat][self.indices[cat]]
                self.screen.blit(sprite, (base_x, base_y))

        font = pygame.font.Font(None, 28)
        current_cat = CATEGORIES[self.current_category_index]
        txt = font.render(f"{current_cat.upper()} : {self.indices[current_cat]}", True, (255, 255, 255))
        self.screen.blit(txt, (50, 50))

        # UI sliders
        slider_y = 400
        for i, (label, value) in enumerate(zip(["R", "G", "B"], [self.color_r, self.color_g, self.color_b])):
            pygame.draw.rect(self.screen, (100, 100, 100), (50, slider_y + i*30, 255, 20))
            pygame.draw.rect(self.screen, (255, 0, 0) if label == "R" else (0, 255, 0) if label == "G" else (0, 0, 255),
                             (50, slider_y + i*30, value, 20))
            label_surface = font.render(f"{label}: {value}", True, (255, 255, 255))
            self.screen.blit(label_surface, (320, slider_y + i*30))

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RIGHT:
                self.change_selection(1)
            elif event.key == pygame.K_LEFT:
                self.change_selection(-1)
            elif event.key == pygame.K_DOWN:
                self.change_category(1)
            elif event.key == pygame.K_UP:
                self.change_category(-1)
            elif event.key == pygame.K_RETURN:
                self.export_preview()
                self.running = False
            elif event.key == pygame.K_c:
                self.change_selection_color((self.color_r, self.color_g, self.color_b))
            elif event.key == pygame.K_r:
                self.color_r = max(0, min(255, self.color_r + 5))
            elif event.key == pygame.K_f:
                self.color_r = max(0, min(255, self.color_r - 5))
            elif event.key == pygame.K_t:
                self.color_g = max(0, min(255, self.color_g + 5))
            elif event.key == pygame.K_g:
                self.color_g = max(0, min(255, self.color_g - 5))
            elif event.key == pygame.K_y:
                self.color_b = max(0, min(255, self.color_b + 5))
            elif event.key == pygame.K_h:
                self.color_b = max(0, min(255, self.color_b - 5))

    def change_selection(self, direction):
        cat = CATEGORIES[self.current_category_index]
        if self.assets[cat]:
            self.indices[cat] = (self.indices[cat] + direction) % len(self.assets[cat])

    def change_category(self, direction):
        self.current_category_index = (self.current_category_index + direction) % len(CATEGORIES)
        print(f"[INFO] Catégorie sélectionnée : {CATEGORIES[self.current_category_index]}")

    def apply_color_pil(self, cat, color):
        idx = self.indices[cat]
        original = self.original_pil_assets[cat][idx].copy()
        r, g, b = Image.new('RGB', original.size, color).split()
        img_r, img_g, img_b, img_a = original.split()
        tinted = Image.merge('RGBA', (
            Image.blend(img_r, r, 0.5),
            Image.blend(img_g, g, 0.5),
            Image.blend(img_b, b, 0.5),
            img_a
        ))
        mode = tinted.mode
        size = tinted.size
        data = tinted.tobytes()
        self.assets[cat][idx] = pygame.image.fromstring(data, size, mode)

    def change_selection_color(self, color):
        cat = CATEGORIES[self.current_category_index]
        if self.assets[cat]:
            self.colors[cat] = color
            self.apply_color_pil(cat, color)
            print(f"[INFO] Couleur appliquée à {cat} : {color}")

    def export_preview(self):
        width = max(sprite.get_width() for cat in CATEGORIES if self.assets[cat] for sprite in self.assets[cat])
        height = max(sprite.get_height() for cat in CATEGORIES if self.assets[cat] for sprite in self.assets[cat])
        composite = pygame.Surface((width, height), pygame.SRCALPHA)

        config = {"base": {"index": int(self.base_type)}}
        for cat in CATEGORIES:
            if self.assets[cat]:
                sprite = self.assets[cat][self.indices[cat]]
                composite.blit(sprite, (0, 0))

            config[cat] = {"index": self.indices[cat]}
            if self.colors[cat]:
                config[cat]["color"] = self.colors[cat]

        image_path = os.path.join("data", f"{self.player_name}_bust.png")
        pygame.image.save(composite, image_path)
        print(f"[OK] Personnage exporté : {image_path}")

        self.player_data["buste"] = config
        with open(self.data_path, "w", encoding="utf-8") as f:
            json.dump(self.player_data, f, indent=4)
        print(f"[OK] Fichier mis à jour : {self.data_path}")

        create_iso_sprite(config, output_path=os.path.join("data", f"{self.player_name}_iso.png"))

    def run(self):
        clock = pygame.time.Clock()
        font = pygame.font.Font(None, 24)

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                self.handle_input(event)

            self.draw_preview()
            hint = font.render("↑/↓ changer catégorie | ←/→ modifier | Entrée = valider | C = appliquer couleur | R/F/T/G/Y/H = sliders RGB", True, (255, 255, 255))
            self.screen.blit(hint, (50, 10))
            pygame.display.flip()
            clock.tick(30)
