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