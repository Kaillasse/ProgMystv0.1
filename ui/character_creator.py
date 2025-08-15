# === ui/character_creator.py ===
import pygame
import json
import os
from core.iso_creator import create_iso_sprite, IsoSpriteAnimator
from core.settings import get_star_sprite_path, FONTS
from ui.uitools import (BorderManager, load_star_frames, load_background_image, 
                       create_starry_background, draw_starry_background, 
                       draw_text_with_effects, oscillate_color, PrevNextButton, UISlider)
from PIL import Image
import tempfile

pygame.font.init()
title_font = pygame.font.Font(FONTS["title"], 48)
button_font = pygame.font.Font(FONTS["button"], 24)
default_font = pygame.font.Font(FONTS["default"], 24)

ASSET_PATH = "assets/Bust"
CATEGORIES = [
    "hair", "base", "head", "ears", "eyebrows", "nose", "mouth",
    "rear_hair", "front_hair", "eyes", "clothes", "accessory"
]

# Nouvelles catégories pour le sprite complet
SPRITE_CATEGORIES = ["bottom", "shoes", "top1", "accessory"]

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

        # Nouveaux éléments UI avec esthétique du menu
        screen_w, screen_h = self.screen.get_width(), self.screen.get_height()

        # Fond étoilé avec filtre noir
        self.bg_image = load_background_image("assets/other/blueaura.png", (screen_w, screen_h))
        self.star_frames = load_star_frames(get_star_sprite_path())
        self.stars = create_starry_background(self.star_frames, screen_w, screen_h, 30)
        self.filter_surface = pygame.Surface((screen_w, screen_h))
        self.filter_surface.fill((0, 0, 0))
        self.filter_surface.set_alpha(128)  # Opacité 0.5

        # Interface avec les nouveaux boutons et sliders
        self.border_mgr = BorderManager.get_instance(session)

        # Slider vertical pour les catégories (centré entre cadre et colonne)
        slider_x = (500 + 200) // 2  # Centré entre colonne (200px) et cadre buste (500px)
        self.color_sliders = [
            UISlider(120, 400, 0, 255, 128, "rouge", "horizontal"),   # Rouge, agrandi
            UISlider(120, 430, 0, 255, 128, "vert", "horizontal"),    # Vert, agrandi
            UISlider(120, 460, 0, 255, 128, "bleu", "horizontal")     # Bleu, agrandi
        ]
        # Ajuster la taille des sliders de couleur pour qu'ils soient plus grands
        for slider in self.color_sliders:
            slider.rect.width = 350  # Plus large
        
        self.category_slider = UISlider(slider_x, 125, 0, len(CATEGORIES)-1, 4, "normal", "vertical")
        self.category_slider.rect = pygame.Rect(slider_x, 125, 32, 250)

        # Boutons prev/next pour chaque catégorie et cadre (maintenant séparés du slider)
        self.category_buttons = []
        for cat in CATEGORIES:
            self.category_buttons.append({
                'prev': PrevNextButton(0, 0, is_prev=True),  # Position sera calculée dynamiquement
                'next': PrevNextButton(0, 0, is_prev=False)
            })
        self.frame_left_btn = PrevNextButton(540, 445, is_prev=True)
        self.frame_right_btn = PrevNextButton(690, 445, is_prev=False)

        # Sprites et données
        self.sprite_indices = {cat: 0 for cat in SPRITE_CATEGORIES}
        self.sprite_colors = {cat: None for cat in SPRITE_CATEGORIES}
        self.current_sprite_category_index = 0
        self.show_sprite_view = False
        
        # Nouveau système de prévisualisation animée
        self.iso_animator = IsoSpriteAnimator()
        self.preview_scale = 2  # Agrandir la prévisualisation

        self.load_assets()
        self.running = True
        self.data_path = os.path.join("data", f"{self.player_name}.json")
        self.player_data = {}

        # Charger les données existantes
        if os.path.exists(self.data_path):
            with open(self.data_path, "r", encoding="utf-8") as f:
                self.player_data = json.load(f)
            for cat in CATEGORIES:
                # Support des deux formats : "bust" (nouveau) et "buste" (ancien)
                bust_data = self.player_data.get("bust", {}).get(cat, {})
                if not bust_data:  # Fallback vers l'ancien format
                    bust_data = self.player_data.get("buste", {}).get(cat, {})
                self.indices[cat] = bust_data.get("index", 0)
                self.colors[cat] = bust_data.get("color")
                if self.colors[cat]:
                    self.apply_color_pil(cat, tuple(self.colors[cat]))
            for cat in SPRITE_CATEGORIES:
                sprite = self.player_data.get("sprite", {}).get(cat, {})
                self.sprite_indices[cat] = sprite.get("index", 0)
                self.sprite_colors[cat] = sprite.get("color")
                
            # Charger l'index de bordure
            border_data = self.player_data.get("border", {})
            if isinstance(border_data, dict):
                border_index = border_data.get("current_index", 0)
            else:
                border_index = border_data  # Ancien format (juste un nombre)
            self.border_mgr.set_border_index(border_index)

    def load_assets(self):
        """Charge les assets PIL et pygame pour chaque catégorie."""
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

    def get_current_config(self):
        """Retourne la config courante pour le preview animé."""
        config = {"base": {"index": int(self.base_type)}}
        for cat in CATEGORIES:
            d = {"index": self.indices[cat]}
            if self.colors[cat]: d["color"] = self.colors[cat]
            config[cat] = d
        for cat in SPRITE_CATEGORIES:
            d = {"index": self.sprite_indices[cat]}
            if self.sprite_colors[cat]: d["color"] = self.sprite_colors[cat]
            config[cat] = d
        return config

    def draw_preview(self):
        """Dessine l'interface selon le design cible avec colonne de catégories et slider blanc."""
        draw_starry_background(self.screen, self.stars, self.bg_image)
        self.screen.blit(self.filter_surface, (0, 0))
        tick = pygame.time.get_ticks()
        color_main = oscillate_color(tick)
        title_text = f"Création de {self.player_name}"
        title_pos = (self.screen.get_width() // 2, 60)
        draw_text_with_effects(self.screen, title_font, title_text, title_pos, color_main, (3, 3), 2)

        # Grand cadre buste
        bust_rect = pygame.Rect(500, 120, 250, 250)
        self.border_mgr.draw_border(self.screen, bust_rect, border_thickness=8)
        bust_bg = pygame.Surface((bust_rect.width - 16, bust_rect.height - 16))
        bust_bg.fill((20, 20, 40)); bust_bg.set_alpha(180)
        self.screen.blit(bust_bg, (bust_rect.x + 8, bust_rect.y + 8))

        # Petit cadre sprite iso
        sprite_rect = pygame.Rect(580, 400, 90, 90)
        self.border_mgr.draw_border(self.screen, sprite_rect, border_thickness=6)
        sprite_bg = pygame.Surface((sprite_rect.width - 12, sprite_rect.height - 12))
        sprite_bg.fill((20, 20, 40)); sprite_bg.set_alpha(180)
        self.screen.blit(sprite_bg, (sprite_rect.x + 6, sprite_rect.y + 6))
        self.frame_left_btn.draw(self.screen)
        self.frame_right_btn.draw(self.screen)

        # Affichage sliders couleur sous le cadre principal
        for slider in self.color_sliders:
            slider.draw(self.screen)

        # Colonne de catégories avec slider unifié à gauche
        self._draw_category_column(color_main)

        # Affichage du contenu buste/sprite
        self._draw_character_content(bust_rect, sprite_rect)

    def _draw_category_column(self, color_main):
        self.category_slider.draw(self.screen)
        base_y = 100
        spacing = 36
        center_index = int(self.category_slider.val)
        visible_range = 7
        total = len(CATEGORIES)
        half = visible_range // 2
    
        # Calcul du début et de la fin de la fenêtre
        start_idx = center_index - half
        end_idx = center_index + half + 1
    
        # Nombre de lignes vides à afficher en haut
        empty_top = max(0, 0 - start_idx)
        # Nombre de lignes vides à afficher en bas
        empty_bottom = max(0, end_idx - total)
    
        # Correction des bornes pour ne pas dépasser la liste
        start_idx = max(0, start_idx)
        end_idx = min(total, end_idx)
    
        # Affichage des lignes vides en haut
        for i in range(empty_top):
            y_pos = base_y + 150 + (i - half) * spacing
            # Optionnel : dessiner un cadre vide ou rien
    
        # Affichage des catégories visibles
        for i, cat_idx in enumerate(range(start_idx, end_idx)):
            y_pos = base_y + 150 + ((i + empty_top) - half) * spacing
            cat = CATEGORIES[cat_idx]
            selected = (cat_idx == center_index)
            distance = abs((i + empty_top) - half)
            # ... (calcul alpha/font, dessin cadre, texte, boutons comme avant) ...
    
            if distance == 0:
                alpha = 255
                font = default_font
            elif distance == 1:
                alpha = 200
                font = default_font
            elif distance == 2:
                alpha = 150
                font = default_font
            else:
                alpha = 100
                font = default_font
    
            txt = f"{cat.upper()} : {self.indices[cat]}"
            text_x = 200
            text_rect = pygame.Rect(text_x - 80, y_pos - 15, 160, 30)
            frame_rect = pygame.Rect(text_x - 100, y_pos - 18, 200, 36)
            if selected:
                self.border_mgr.draw_border(self.screen, frame_rect, border_thickness=4)
                frame_bg = pygame.Surface((frame_rect.width - 8, frame_rect.height - 8))
                frame_bg.fill((20, 20, 40))
                frame_bg.set_alpha(180)
                self.screen.blit(frame_bg, (frame_rect.x + 4, frame_rect.y + 4))
                btns = self.category_buttons[cat_idx]
                btns['prev'].rect.right = text_rect.left - 8
                btns['prev'].rect.centery = text_rect.centery
                btns['next'].rect.left = text_rect.right + 8
                btns['next'].rect.centery = text_rect.centery
                btns['prev'].draw(self.screen)
                btns['next'].draw(self.screen)
            else:
                pygame.draw.rect(self.screen, (80, 80, 120, alpha // 2), frame_rect, 2)
            text_surface = font.render(txt, True, color_main)
            if alpha < 255:
                text_surface.set_alpha(alpha)
            text_display_rect = text_surface.get_rect(center=text_rect.center)
            self.screen.blit(text_surface, text_display_rect)
    
        # Affichage des lignes vides en bas
        for i in range(empty_bottom):
            y_pos = base_y + 150 + ((i + empty_top + end_idx - start_idx) - half) * spacing
            # Optionnel : dessiner un cadre vide ou rien
    def _draw_character_content(self, bust_rect, sprite_rect):
        """Affiche le contenu des zones de personnage"""
        # Mise à jour de l'animation
        self.iso_animator.update_animation()
        config = self.get_current_config()
        
        # Affichage du BUSTE dans le grand cadre
        base_x = bust_rect.centerx - 300
        base_y = bust_rect.centery - 170
        for cat in CATEGORIES:
            idx = self.indices[cat]
            if self.assets[cat] and idx < len(self.assets[cat]):
                asset = self.assets[cat][self.indices[cat]]
                scaled_asset = pygame.transform.scale(asset, 
                    (asset.get_width(), asset.get_height())) 
                self.screen.blit(scaled_asset, (base_x, base_y))
        
        # Affichage du SPRITE ISO dans le petit cadre
        iso_sprite = self.iso_animator.get_animated_iso_sprite(config)
        if iso_sprite:
            # Centrer dans le petit cadre
            sprite_x = sprite_rect.centerx - iso_sprite.get_width() // 2
            sprite_y = sprite_rect.centery - iso_sprite.get_height() // 2
            self.screen.blit(iso_sprite, (sprite_x, sprite_y))

    def handle_input(self, event):
        """Gère les entrées pour le système unifié slider + catégories."""
        cache_invalidated = False
        
        # Gestion du slider vertical pour les catégories
        if self.category_slider.handle_event(event):
            self.current_category_index = int(self.category_slider.val)
        
        # Boutons prev/next pour la catégorie actuellement sélectionnée
        current_cat = CATEGORIES[self.current_category_index]
        btns = self.category_buttons[self.current_category_index]
        
        if btns['prev'].handle_event(event):
            cache_invalidated = self._change_asset_index(current_cat, -1)
                
        if btns['next'].handle_event(event):
            cache_invalidated = self._change_asset_index(current_cat, 1)
                
        if self.frame_left_btn.handle_event(event):
            if self.border_mgr.borders:
                new_index = (self.border_mgr.current_border_index - 1) % len(self.border_mgr.borders)
                self.border_mgr.set_border_index(new_index)
        if self.frame_right_btn.handle_event(event):
            if self.border_mgr.borders:
                new_index = (self.border_mgr.current_border_index + 1) % len(self.border_mgr.borders)
                self.border_mgr.set_border_index(new_index)

        # Gestion clavier simplifiée
        if event.type == pygame.KEYDOWN:
            key_actions = {
                pygame.K_UP: lambda: self._change_category(-1),
                pygame.K_DOWN: lambda: self._change_category(1),
                pygame.K_LEFT: lambda: self._change_asset_index(current_cat, -1),
                pygame.K_RIGHT: lambda: self._change_asset_index(current_cat, 1),
                pygame.K_TAB: lambda: self._toggle_sprite_view(),
                pygame.K_RETURN: lambda: self._export_and_exit()
            }
            
            action = key_actions.get(event.key)
            if action:
                result = action()
                if result:
                    cache_invalidated = True

        # Gestion des sliders couleur
        for slider in self.color_sliders:
            if slider.handle_event(event):
                self._apply_color_from_sliders()
                cache_invalidated = True

        if cache_invalidated:
            self.iso_animator.clear_cache()

    def _change_category(self, direction):
        """Change la catégorie courante"""
        self.current_category_index = max(0, min(len(CATEGORIES) - 1, self.current_category_index + direction))
        self.category_slider.val = self.current_category_index

    def _change_asset_index(self, cat, direction):
        """Change l'index d'un asset et retourne si le cache doit être invalidé"""
        if self.assets[cat]:
            self.indices[cat] = (self.indices[cat] + direction) % len(self.assets[cat])
            return True
        return False

    def _toggle_sprite_view(self):
        """Toggle entre les vues sprite et buste"""
        self.show_sprite_view = not self.show_sprite_view
        self.iso_animator.clear_cache()

    def _export_and_exit(self):
        """Exporte le personnage et quitte"""
        self.export_preview()
        self.running = False

    def _apply_color_from_sliders(self):
        """Applique la couleur depuis les sliders RGB"""
        r, g, b = [int(slider.val) for slider in self.color_sliders]
        cat = CATEGORIES[self.current_category_index]
        self.colors[cat] = (r, g, b)
        self.apply_color_pil(cat, (r, g, b))


    def apply_color_pil(self, cat, color):
        """Applique une couleur à un asset PIL (blend 50%)."""
        idx = self.indices[cat]
        if idx >= len(self.original_pil_assets[cat]): return
        orig = self.original_pil_assets[cat][idx].copy()
        r, g, b = Image.new('RGB', orig.size, color).split()
        img_r, img_g, img_b, img_a = orig.split()
        tinted = Image.merge('RGBA', (
            Image.blend(img_r, r, 0.5),
            Image.blend(img_g, g, 0.5),
            Image.blend(img_b, b, 0.5),
            img_a
        ))
        self.assets[cat][idx] = pygame.image.fromstring(tinted.tobytes(), tinted.size, tinted.mode)

    def export_preview(self):
        """Exporte le personnage avec la nouvelle configuration"""
        try:
            # Vérification que les assets sont bien chargés
            if not any(self.assets.values()):
                print("[ERREUR] Aucun asset chargé pour l'export")
                return

            # Dimensions basées sur les premiers assets trouvés
            first_asset = None
            for cat in CATEGORIES:
                if self.assets[cat] and self.indices[cat] < len(self.assets[cat]):
                    first_asset = self.assets[cat][self.indices[cat]]
                    break
            
            if first_asset is None:
                print("[ERREUR] Aucun asset valide trouvé")
                return
                
            width = first_asset.get_width()
            height = first_asset.get_height()
            composite = pygame.Surface((width, height), pygame.SRCALPHA)
            composite.fill((0, 0, 0, 0))  # Transparent background

            print(f"[EXPORT] Composition du bust ({width}x{height})")

            # Composition du bust dans le même ordre que l'affichage
            layers_drawn = 0
            for cat in CATEGORIES:
                if self.assets[cat] and self.indices[cat] < len(self.assets[cat]):
                    sprite = self.assets[cat][self.indices[cat]]
                    if sprite:
                        composite.blit(sprite, (0, 0))
                        layers_drawn += 1
                        print(f"[EXPORT] Layer {cat}: index {self.indices[cat]} ajouté")

            print(f"[EXPORT] {layers_drawn} layers composés")

            # Sauvegarde des images
            os.makedirs("data", exist_ok=True)
            image_path = os.path.join("data", f"{self.player_name}_bust.png")
            pygame.image.save(composite, image_path)
            print(f"[OK] Personnage exporté : {image_path}")

            # Sauvegarde des données JSON (correction: "bust" au lieu de "buste")
            self.player_data["bust"] = {cat: {"index": self.indices[cat], "color": self.colors[cat]} 
                                       for cat in CATEGORIES if self.colors[cat] or self.indices[cat] > 0}
            self.player_data["sprite"] = {cat: {"index": self.sprite_indices[cat], "color": self.sprite_colors[cat]} 
                                         for cat in SPRITE_CATEGORIES if self.sprite_colors[cat] or self.sprite_indices[cat] > 0}
            
            # Sauvegarde de la bordure dans session.py
            self.player_data["border"] = {"current_index": self.border_mgr.current_border_index}
            
            # Mise à jour de la session pour la bordure
            if hasattr(self.session, 'data'):
                self.session.data["border"] = {"current_index": self.border_mgr.current_border_index}
                self.session.save_data()
            
            with open(self.data_path, "w", encoding="utf-8") as f:
                json.dump(self.player_data, f, indent=4)
            print(f"[OK] Fichier mis à jour : {self.data_path}")

            # Configuration complète pour le sprite iso
            config = self.get_current_config()
            create_iso_sprite(config, output_path=os.path.join("data", f"{self.player_name}_iso.png"))
            
        except Exception as e:
            print(f"[ERREUR] Export : {e}")
            import traceback
            traceback.print_exc()

    def run(self):
        """Boucle principale avec la nouvelle interface"""
        clock = pygame.time.Clock()

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                self.handle_input(event)

            self.draw_preview()
            pygame.display.flip()
            clock.tick(30)
