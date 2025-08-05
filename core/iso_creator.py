# Créateur de sprite 3D isométrique à partir des assets et de la config personnage
import os
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