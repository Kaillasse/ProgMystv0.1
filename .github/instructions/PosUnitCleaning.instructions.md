Voici une stratégie de refactorisation pour unifier la logique d’affichage et de gestion des entités (Character et PNJ) sans créer de nouveaux fichiers et en supprimant le plus de redondances possible :

1. Centraliser la gestion des positions et conversions
Utilise toujours les méthodes de World pour :
Conversion tuile <-> pixel (get_entity_pixel_pos, tile_to_pixel, pixel_to_tile)
Récupération de la position grille (get_grid_position)
Supprime toute logique de conversion dupliquée dans Character et les PNJ.
Dans Character et PNJ, utilise uniquement self.world_manager ou self.world pour ces conversions.
2. Unifier la structure de données des entités
Assure-toi que Character et PNJ ont tous :
tile_pos (toujours [float, float])
combat_tile_x, combat_tile_y
name
Supprime tout code qui gère différemment la position (ex : plus de grid_x, grid_y séparés).
3. Unifier le rendu et l’animation
Impose la méthode get_current_frame() sur tous les PNJ (déjà fait pour Character).
Dans PNJManager, utilise toujours cette méthode pour le rendu.
Supprime la logique conditionnelle dans _get_npc_frame (tu peux garder un fallback debug pour les PNJ sans sprite).
4. Unifier la gestion du spawn et de la synchronisation
Utilise la méthode sync_combat_positions de World pour synchroniser toutes les entités (Character et PNJ) après le spawn ou le déplacement.
Supprime les synchronisations manuelles dupliquées dans Character et PNJManager.
5. Unifier le debug et l’affichage des infos
Utilise la méthode validate_entity_positions de World pour afficher les infos de debug pour toutes les entités.
Supprime les méthodes de debug dupliquées dans Character et PNJManager.
6. Gestion des entités dans les managers
Dans le code de jeu, manipule toutes les entités via leurs managers (PNJManager pour les PNJ, gestion directe pour le Character).
Si tu as besoin de traitements communs (update, draw, etc.), boucle sur [character] + pnj_manager.get_active_npcs().
7. Résumé des suppressions possibles
Supprime :
Toute conversion grille/pixel hors de World
Les synchronisations manuelles de positions de combat
Les méthodes de debug dupliquées
Les tests conditionnels pour le rendu des frames (toujours get_current_frame)
Garde :
Les méthodes utilitaires de World
Les attributs de position unifiés sur toutes les entités
Exemple d’utilisation unifiée (dans le jeu)
# Pour update/draw toutes les entités :
for entity in [character] + pnj_manager.get_active_npcs():
    entity.update(dt)
    entity.draw(screen, camera)
En résumé :

Utilise exclusivement les méthodes de World pour toutes les conversions et synchronisations.
Supprime toute logique dupliquée dans les entités.
Imposes une API minimale commune (tile_pos, get_current_frame, etc.).
Utilise les managers pour manipuler les groupes d’entités.
Cela te permettra d’avoir un code plus simple, cohérent, et facile à maintenir, sans ajouter de nouveaux fichiers ni complexifier la structure.