import os

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
    # Tu pourras ajouter d'autres fonts ici plus tard
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

# === FONCTIONS UTILITAIRES COORDONNÉES ===
def grid_to_iso(x, y, tile_width=64, tile_height=64):
    """Convertit les coordonnées grille en coordonnées isométriques pixels"""
    iso_x = (x - y) * (tile_width // 2)
    iso_y = (x + y) * (tile_height // 4)
    return iso_x, iso_y

def iso_to_grid(iso_x, iso_y, tile_width=64, tile_height=64):
    """Convertit les coordonnées pixels en coordonnées grille"""
    try:
        iso_x = float(iso_x)
        iso_y = float(iso_y)
        tw = int(tile_width)
        th = int(tile_height)
    except Exception as e:
        print(f"[SETTINGS] Erreur conversion iso_to_grid: {e}")
        return 0, 0

    half_width = tw / 2
    quarter_height = th / 4

    x = (iso_y / quarter_height + iso_x / half_width) / 2
    y = (iso_y / quarter_height - iso_x / half_width) / 2
    return int(round(x)), int(round(y))

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
