# Créateur de sprite 3D isométrique à partir des assets et de la config personnage
import os
import pygame
from PIL import Image


# Ordre et mapping des couches pour le rendu isométrique selon la structure réelle
ISO_LAYERS = [
    ('shadow', 'shadow'),         # (catégorie logique, dossier)
    ('base', 'base'),
    ('front_hair', 'FrontHair'),
    ('bottom', 'Bottom'),
    ('rear_hair', 'RearHair'),
    ('top1', 'Top1'),
    ('accessory', 'Accessory'),
    ('shoes', 'Shoes'),
    ('eyes', 'Eyes'),
]

ASSET_DIR = os.path.join('assets', 'sprites')

# Frames d'animation idle pour le prévisualisateur (même logique que main_menu)
IDLE_FRAMES = [1, 4, 13, 28, 37, 40, 25, 16]

class IsoSpriteAnimator:
    """Prévisualisateur d'animation isométrique en temps réel"""
    
    def __init__(self):
        self.frame_cache = {}
        self.current_frame = 0
        self.animation_timer = 0.0
        self.animation_speed = 0.15
        
    def get_animated_iso_sprite(self, config):
        """Retourne le sprite iso animé pour la frame courante"""
        # Utiliser la frame courante pour l'animation idle
        frame_index = IDLE_FRAMES[int(self.current_frame) % len(IDLE_FRAMES)]
        
        # Clé de cache basée sur config + frame
        cache_key = (str(config), frame_index)
        
        if cache_key not in self.frame_cache:
            # Créer le sprite pour cette frame
            sprite = self._create_frame_sprite(config, frame_index)
            if sprite:
                # Convertir PIL en pygame surface
                sprite_surface = pygame.image.fromstring(sprite.tobytes(), sprite.size, sprite.mode)
                self.frame_cache[cache_key] = sprite_surface
            else:
                self.frame_cache[cache_key] = None
                
        return self.frame_cache[cache_key]
    
    def update_animation(self):
        """Met à jour l'animation"""
        self.animation_timer += self.animation_speed
        self.current_frame = self.animation_timer % len(IDLE_FRAMES)
    
    def _create_frame_sprite(self, config, frame_index):
        """Crée un sprite iso pour une frame d'animation donnée"""
        base_index = config.get('base', {}).get('index', 0)
        
        layers = []
        for logical, folder in ISO_LAYERS:
            layer_conf = config.get(logical, {})
            idx = layer_conf.get('index', 0)
            color = layer_conf.get('color', None)
            
            # Pour l'animation, on utilise la frame courante
            img = load_layer_image_animated(folder, base_index, idx, frame_index, color)
            if img:
                layers.append(img)
        
        if not layers:
            return None
            
        final = Image.new('RGBA', layers[0].size, (0,0,0,0))
        for img in layers:
            final.alpha_composite(img)
            
        return final
    
    def clear_cache(self):
        """Vide le cache des frames"""
        self.frame_cache.clear()


def load_layer_image_animated(layer_folder, base_index, index=0, frame_index=0, color=None):
    """Charge une frame d'animation spécifique pour une couche"""
    layer_dir = os.path.join(ASSET_DIR, layer_folder, str(base_index))
    img_path = os.path.join(layer_dir, f"{index}.png")
    
    if not os.path.exists(img_path):
        return None
    
    try:
        # Charger la spritesheet
        sheet = Image.open(img_path).convert('RGBA')
        frame_width, frame_height = 48, 96
        columns = 12
        
        # Calculer la position de la frame dans la grille
        col = frame_index % columns
        row = frame_index // columns
        
        # Extraire la frame
        left = col * frame_width
        top = row * frame_height
        right = left + frame_width
        bottom = top + frame_height
        
        img = sheet.crop((left, top, right, bottom))
        
        # Appliquer la couleur si fournie
        if color is not None:
            if isinstance(color, list):
                color = tuple(color)
            elif isinstance(color, str):
                color = tuple(map(int, color.strip("() ").split(",")))
            elif not isinstance(color, tuple):
                raise ValueError(f"[ISO_CREATOR] Couleur invalide : {color}")
            
            r, g, b = Image.new('RGB', img.size, color).split()
            img = Image.merge("RGBA", (r, g, b, img.split()[3]))
        
        return img
        
    except Exception as e:
        print(f"[ISO] Erreur chargement frame {frame_index} pour {img_path}: {e}")
        return None



def load_layer_image(layer_folder, base_index, index=0, color=None):
    layer_dir = os.path.join(ASSET_DIR, layer_folder, str(base_index))
    img_path = os.path.join(layer_dir, f"{index}.png")
    if not os.path.exists(img_path):
        print(f"[ISO] Asset manquant : {img_path}")
        return None

    img = Image.open(img_path).convert('RGBA')

    # Si aucune couleur n'est fournie, retourner l'image telle quelle
    if color is None:
        return img

    # Correction : conversion intelligente
    if isinstance(color, list):
        color = tuple(color)
    elif isinstance(color, str):
        color = tuple(map(int, color.strip("() ").split(",")))
    elif not isinstance(color, tuple):
        raise ValueError(f"[ISO_CREATOR] Couleur invalide : {color} (type {type(color)})")

    # Application de la recoloration
    r, g, b = Image.new('RGB', img.size, color).split()
    recolored = Image.merge("RGBA", (r, g, b, img.split()[3]))  # Alpha
    return recolored







def create_iso_sprite(config, output_path='output/character_iso_export.png'):
    """
    Compose le sprite isométrique à partir de la config personnage.
    Utilise base.index pour déterminer le body_type global (0/1).
    """
    base_index = config.get('base', {}).get('index', 0) #0-masculin, 1-féminin

    layers = []
    for logical, folder in ISO_LAYERS:
        layer_conf = config.get(logical, {})
        idx = layer_conf.get('index', 0)
        layer_body_type = base_index  # Plus de body_type à chercher ailleurs
        color = layer_conf.get('color', None)
        img = load_layer_image(folder, layer_body_type, idx, color)
        if img:
            layers.append(img)

    if not layers:
        print("[ISO] Aucune couche à composer.")
        return

    final = Image.new('RGBA', layers[0].size, (0,0,0,0))
    for img in layers:
        final.alpha_composite(img)

    out_dir = os.path.dirname(output_path)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir)
    final.save(output_path)
    print(f"[ISO] Sprite isométrique exporté dans {output_path}")


# Exemple d'utilisation (à remplacer par la liaison automatique plus tard)
if __name__ == '__main__':
    import json
    config_path = 'output/character_data.json'
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        create_iso_sprite(config)
    else:
        print("[ISO] Fichier de config personnage non trouvé.")