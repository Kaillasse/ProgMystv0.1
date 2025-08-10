import os
import numpy as np

# === COULEURS ===
COLORS = {
    'primary_bg': '#0A0F0A',       # Noir organique, comme une forêt très sombre
    'secondary_bg': '#112A12',     # Vert très foncé, évoque les sous-bois humides
    'card_bg': '#1B3B1B',          # Fond pour les cartes, un peu plus lumineux
    'border': '#2D5E2D',           # Vert mousse pour les bordures
    'text_light': '#D5FFD5',       # Texte lisible type terminal phosphorescent
    'text_muted': '#88A488',       # Texte désactivé ou secondaire, vert délavé
    'text_highlight': '#00FF00',   # Accent type "hacker", vert fluo terminal
    'accent_warm': '#54E38E',      # Magie positive, émeraude enchantée
    'accent_contrast': '#24613D',  # Accent plus profond (liens, boutons appuyés)
    'success': '#44FF44',          # Succès : classique vert vif
    'warning': '#FFFF66',          # Alerte douce type luciole
    'error': '#FF4F4F',            # Rouge hacker vif pour erreurs critiques
}

# === RACINES ===
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# === DOSSIERS ===
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
DATA_DIR   = os.path.join(BASE_DIR, "data")
GRIMOIRES_DIR = os.path.join(BASE_DIR, "grimoires")
SPRITES_DIR = os.path.join(ASSETS_DIR, "sprites")
BUSTS_DIR   = os.path.join(ASSETS_DIR, "Bust")
MAP_DIR     = os.path.join(DATA_DIR, "map")
FONT_DIR = os.path.join(ASSETS_DIR, "fonts")

# Fonts
FONTS = {
    "title": os.path.join(FONT_DIR, "DungeonFont.ttf"),
    'button': os.path.join(FONT_DIR, "dungeon-mode.ttf")
}

# === FICHIERS FONDAMENTAUX ===
CLAIRIERE_MAP = os.path.join(MAP_DIR, "clairiere.json")
JSON_MAP = os.path.join(MAP_DIR, "JSON.json")
LOOPFANG_MAP = os.path.join(MAP_DIR, "loopfanglerecursif.json")
NEUILL_MAP = os.path.join(MAP_DIR, "neuill.json")
ROI_MAP = os.path.join(MAP_DIR, "roi.json")
TYRAN_MAP = os.path.join(MAP_DIR, "tyran.json")

# === TUILES ===
TILE_WIDTH = 64
TILE_HEIGHT = 64
LAYER_HEIGHT = 16

# === ÉCRAN ===
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# === FONCTIONS UTILITAIRES COORDONNÉES (Matrices de transformation) ===

def _get_iso_transformation_matrix(tile_width=64, tile_height=64):
    """
    Matrice de transformation grille → isométrique
    [iso_x]   [tw/2  -tw/2] [grid_x]
    [iso_y] = [th/4   th/4] [grid_y]
    """
    return np.array([
        [tile_width / 2, -tile_width / 2],
        [tile_height / 4, tile_height / 4]
    ], dtype=np.float64)

def _get_inverse_iso_transformation_matrix(tile_width=64, tile_height=64):
    """
    Matrice inverse isométrique → grille
    Calculée automatiquement via l'inverse de la matrice de transformation
    """
    transform_matrix = _get_iso_transformation_matrix(tile_width, tile_height)
    return np.linalg.inv(transform_matrix)

def grid_to_iso(x, y, tile_width=64, tile_height=64):
    """Convertit les coordonnées grille en coordonnées isométriques pixels via matrice"""
    try:
        grid_coords = np.array([x, y], dtype=np.float64)
        transform_matrix = _get_iso_transformation_matrix(tile_width, tile_height)
        iso_coords = transform_matrix @ grid_coords
        return int(round(iso_coords[0])), int(round(iso_coords[1]))
    except Exception as e:
        print(f"[SETTINGS] Erreur conversion grid_to_iso: {e}")
        return 0, 0

def iso_to_grid(iso_x, iso_y, tile_width=64, tile_height=64):
    """Convertit les coordonnées pixels en coordonnées grille via matrice inverse"""
    try:
        iso_coords = np.array([iso_x, iso_y], dtype=np.float64)
        inverse_matrix = _get_inverse_iso_transformation_matrix(tile_width, tile_height)
        grid_coords = inverse_matrix @ iso_coords
        return int(round(grid_coords[0])), int(round(grid_coords[1]))
    except Exception as e:
        print(f"[SETTINGS] Erreur conversion iso_to_grid: {e}")
        return 0, 0

def grid_to_iso_precise(x, y, tile_width=64, tile_height=64):
    """Version haute précision sans arrondi pour calculs intermédiaires"""
    try:
        grid_coords = np.array([x, y], dtype=np.float64)
        transform_matrix = _get_iso_transformation_matrix(tile_width, tile_height)
        iso_coords = transform_matrix @ grid_coords
        return float(iso_coords[0]), float(iso_coords[1])
    except Exception as e:
        print(f"[SETTINGS] Erreur conversion grid_to_iso_precise: {e}")
        return 0.0, 0.0

def iso_to_grid_precise(iso_x, iso_y, tile_width=64, tile_height=64):
    """Version haute précision sans arrondi pour calculs intermédiaires"""
    try:
        iso_coords = np.array([iso_x, iso_y], dtype=np.float64)
        inverse_matrix = _get_inverse_iso_transformation_matrix(tile_width, tile_height)
        grid_coords = inverse_matrix @ iso_coords
        return float(grid_coords[0]), float(grid_coords[1])
    except Exception as e:
        print(f"[SETTINGS] Erreur conversion iso_to_grid_precise: {e}")
        return 0.0, 0.0

TILE_INDEX = {
    0: "herbe_claire",
    1: "herbe_foncée",
    2: "chemin",
    3: "buisson",
    4: "rocher",
    5: "arbre",
    # ...
    114: "pierre_mystique"
}

# === FONCTIONS UTILITAIRES ===
def get_player_data_path(name):
    return os.path.join(DATA_DIR, f"{name.lower()}.json")

def get_player_bust_path(name):
    return os.path.join(DATA_DIR, f"{name.lower()}_bust.png")

def get_player_sprite_path(name):
    return os.path.join(DATA_DIR, f"{name.lower()}_iso.png")

def get_grimoire_path(name):
    return os.path.join(GRIMOIRES_DIR, f"{name.lower()}.py")
import os

# Pour accéder au sprite sheet des étoiles
def get_star_sprite_path():
    return os.path.join("assets", "other", "starbg.png")
