# === ui/character_creator.py ===
import pygame
import json
import os
from core.iso_creator import create_iso_sprite
from PIL import Image
import tempfile

ASSET_PATH = "assets/Bust"
CATEGORIES = [
    "hair", "base", "head", "ears", "eyebrows", "nose", "mouth",
    "rear_hair", "front_hair", "eyes", "clothes", "accessory"
]

# Nouvelles catégories pour le sprite complet
SPRITE_CATEGORIES = ["bottom", "shoes", "top1", "accessory"]

class Slider:
    def __init__(self, x, y, width, height, min_val, max_val, initial_val, color):
        self.rect = pygame.Rect(x, y, width, height)
        self.min_val = min_val
        self.max_val = max_val
        self.val = initial_val
        self.color = color
        self.dragging = False
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
                self.update_value(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP:
            if self.dragging:
                self.dragging = False
                return True  # Signal que le slider a été relâché
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.update_value(event.pos[0])
        return False
    
    def update_value(self, mouse_x):
        relative_x = mouse_x - self.rect.x
        relative_x = max(0, min(self.rect.width, relative_x))
        ratio = relative_x / self.rect.width
        self.val = int(self.min_val + ratio * (self.max_val - self.min_val))
    
    def draw(self, screen, font):
        # Arrière-plan du slider
        pygame.draw.rect(screen, (100, 100, 100), self.rect)
        # Partie colorée
        colored_width = int((self.val - self.min_val) / (self.max_val - self.min_val) * self.rect.width)
        colored_rect = pygame.Rect(self.rect.x, self.rect.y, colored_width, self.rect.height)
        pygame.draw.rect(screen, self.color, colored_rect)
        # Bouton glissant
        button_x = self.rect.x + colored_width - 5
        button_rect = pygame.Rect(button_x, self.rect.y - 2, 10, self.rect.height + 4)
        pygame.draw.rect(screen, (255, 255, 255), button_rect)

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
        self.sliders = [
            Slider(50, 400, 255, 20, 0, 255, 128, (255, 0, 0)),
            Slider(50, 430, 255, 20, 0, 255, 128, (0, 255, 0)),
            Slider(50, 460, 255, 20, 0, 255, 128, (0, 0, 255))
        ]
        self.sprite_indices = {cat: 0 for cat in SPRITE_CATEGORIES}
        self.sprite_colors = {cat: None for cat in SPRITE_CATEGORIES}
        self.current_sprite_category_index = 0
        self.show_sprite_view = False
        self.iso_sprite_cache = None
        self.cache_dirty = True
        self.load_assets()
        self.running = True
        self.data_path = os.path.join("data", f"{self.player_name}.json")
        self.player_data = {}
        if os.path.exists(self.data_path):
            with open(self.data_path, "r", encoding="utf-8") as f:
                self.player_data = json.load(f)
            for cat in CATEGORIES:
                self.indices[cat] = self.player_data.get("buste", {}).get(cat, {}).get("index", 0)
                self.colors[cat] = self.player_data.get("buste", {}).get(cat, {}).get("color")
                if self.colors[cat]:
                    self.apply_color_pil(cat, tuple(self.colors[cat]))
            for cat in SPRITE_CATEGORIES:
                self.sprite_indices[cat] = self.player_data.get("sprite", {}).get(cat, {}).get("index", 0)
                self.sprite_colors[cat] = self.player_data.get("sprite", {}).get(cat, {}).get("color")

    def load_assets(self):
        for cat in CATEGORIES:
            path = os.path.join(ASSET_PATH, cat, self.base_type)
            self.assets[cat], self.original_pil_assets[cat] = [], []
            if os.path.exists(path):
                for f in sorted(os.listdir(path)):
                    if f.endswith(".png"):
                        img_path = os.path.join(path, f)
                        pil_img = Image.open(img_path).convert("RGBA")
                        self.original_pil_assets[cat].append(pil_img)
                        self.assets[cat].append(pygame.image.fromstring(pil_img.tobytes(), pil_img.size, pil_img.mode))
            else:
                print(f"[WARN] Aucun asset trouvé pour {cat} avec base_type {self.base_type}")

    def update_iso_sprite_cache(self):
        if not self.cache_dirty:
            return
        config = {"base": {"index": int(self.base_type)}}
        for cat in CATEGORIES:
            config[cat] = {"index": self.indices[cat]}
            if self.colors[cat]:
                config[cat]["color"] = self.colors[cat]
        for cat in SPRITE_CATEGORIES:
            config[cat] = {"index": self.sprite_indices[cat]}
            if self.sprite_colors[cat]:
                config[cat]["color"] = self.sprite_colors[cat]
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_path = temp_file.name
        try:
            create_iso_sprite(config, temp_path)
            if os.path.exists(temp_path):
                self.iso_sprite_cache = pygame.image.load(temp_path)
                os.unlink(temp_path)
            self.cache_dirty = False
        except Exception as e:
            print(f"[WARN] Erreur lors de la création du sprite iso: {e}")
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def draw_preview(self):
        self.screen.fill((40, 40, 40))
        if self.show_sprite_view:
            self.update_iso_sprite_cache()
            if self.iso_sprite_cache:
                sprite_x = 300 - self.iso_sprite_cache.get_width() // 2
                sprite_y = 150 - self.iso_sprite_cache.get_height() // 2
                self.screen.blit(self.iso_sprite_cache, (sprite_x, sprite_y))
            font = pygame.font.Font(None, 28)
            current_cat = SPRITE_CATEGORIES[self.current_sprite_category_index]
            txt = font.render(f"SPRITE - {current_cat.upper()} : {self.sprite_indices[current_cat]}", True, (255, 255, 255))
            self.screen.blit(txt, (50, 50))
        else:
            base_x, base_y = 300, 100
            for cat in CATEGORIES:
                if self.assets[cat]:
                    self.screen.blit(self.assets[cat][self.indices[cat]], (base_x, base_y))
            font = pygame.font.Font(None, 28)
            current_cat = CATEGORIES[self.current_category_index]
            txt = font.render(f"BUST - {current_cat.upper()} : {self.indices[current_cat]}", True, (255, 255, 255))
            self.screen.blit(txt, (50, 50))
        font = pygame.font.Font(None, 24)
        for i, (slider, label) in enumerate(zip(self.sliders, ["R", "G", "B"])):
            slider.draw(self.screen, font)
            self.screen.blit(font.render(f"{label}: {slider.val}", True, (255, 255, 255)), (320, 400 + i*30))
        mode_text = "SPRITE" if self.show_sprite_view else "BUST"
        self.screen.blit(font.render(f"[TAB] Mode: {mode_text}", True, (255, 255, 0)), (50, 500))

    def handle_input(self, event):
        for slider in self.sliders:
            if slider.handle_event(event):
                self.apply_current_color()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB:
                self.show_sprite_view = not self.show_sprite_view
                self.cache_dirty = True
            elif event.key == pygame.K_RIGHT:
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

    def apply_current_color(self):
        color = tuple(slider.val for slider in self.sliders)
        if self.show_sprite_view:
            cat = SPRITE_CATEGORIES[self.current_sprite_category_index]
            self.sprite_colors[cat] = color
            self.cache_dirty = True
            print(f"[INFO] Couleur appliquée au sprite {cat} : {color}")
        else:
            cat = CATEGORIES[self.current_category_index]
            if self.assets[cat]:
                self.colors[cat] = color
                self.apply_color_pil(cat, color)
                print(f"[INFO] Couleur appliquée au bust {cat} : {color}")

    def change_selection(self, direction):
        if self.show_sprite_view:
            cat = SPRITE_CATEGORIES[self.current_sprite_category_index]
            self.sprite_indices[cat] = (self.sprite_indices[cat] + direction) % 10
            self.cache_dirty = True
        else:
            cat = CATEGORIES[self.current_category_index]
            if self.assets[cat]:
                self.indices[cat] = (self.indices[cat] + direction) % len(self.assets[cat])

    def change_category(self, direction):
        if self.show_sprite_view:
            self.current_sprite_category_index = (self.current_sprite_category_index + direction) % len(SPRITE_CATEGORIES)
            print(f"[INFO] Catégorie sprite sélectionnée : {SPRITE_CATEGORIES[self.current_sprite_category_index]}")
        else:
            self.current_category_index = (self.current_category_index + direction) % len(CATEGORIES)
            print(f"[INFO] Catégorie bust sélectionnée : {CATEGORIES[self.current_category_index]}")

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
        self.assets[cat][idx] = pygame.image.fromstring(tinted.tobytes(), tinted.size, tinted.mode)

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

        # Configuration du bust
        config = {"base": {"index": int(self.base_type)}}
        for cat in CATEGORIES:
            if self.assets[cat]:
                sprite = self.assets[cat][self.indices[cat]]
                composite.blit(sprite, (0, 0))

            config[cat] = {"index": self.indices[cat]}
            if self.colors[cat]:
                config[cat]["color"] = self.colors[cat]

        # Configuration du sprite complet
        sprite_config = {}
        for cat in SPRITE_CATEGORIES:
            sprite_config[cat] = {"index": self.sprite_indices[cat]}
            if self.sprite_colors[cat]:
                sprite_config[cat]["color"] = self.sprite_colors[cat]

        # Sauvegarde des images
        image_path = os.path.join("data", f"{self.player_name}_bust.png")
        pygame.image.save(composite, image_path)
        print(f"[OK] Personnage exporté : {image_path}")

        # Sauvegarde des données
        self.player_data["buste"] = config
        self.player_data["sprite"] = sprite_config
        with open(self.data_path, "w", encoding="utf-8") as f:
            json.dump(self.player_data, f, indent=4)
        print(f"[OK] Fichier mis à jour : {self.data_path}")

        # Création du sprite isométrique final
        full_config = {**config, **sprite_config}
        create_iso_sprite(full_config, output_path=os.path.join("data", f"{self.player_name}_iso.png"))

    def run(self):
        clock = pygame.time.Clock()
        font = pygame.font.Font(None, 24)

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                self.handle_input(event)

            self.draw_preview()
            hint = font.render("↑/↓ changer catégorie | ←/→ modifier | TAB = mode | Sliders RGB | Entrée = valider", True, (255, 255, 255))
            self.screen.blit(hint, (50, 10))
            pygame.display.flip()
            clock.tick(30)
