class Quest:
    """
    Classe représentant une quête pédagogique pour les élèves.
    Chaque quête a un code, un nom, une description et un score associé.
    """
    def __init__(self, code, nom, description):
        self.code = code
        self.nom = nom
        self.description = description

    def __repr__(self):
        return f"<Quest {self.code}: {self.nom} (+{self.score})>"

QUESTS = [
    Quest('#Q1', 'Affichage', "Utiliser print() pour afficher un message ou un résultat"),
    Quest('#Q2', 'Variables simples', "Utiliser au moins 2 variables (entier, réel ou chaîne)"),
    Quest('#Q3', 'Affectation', "Affecter une valeur à une variable avec ="),
    Quest('#Q4', 'Lecture utilisateur', "Utiliser input() pour récupérer une valeur"),
    Quest('#Q5', 'Condition simple', "Utiliser une instruction if"),
    Quest('#Q6', 'Condition double', "Utiliser if ... else"),
    Quest('#Q7', 'Condition imbriquée', "Utiliser if ... elif ... else"),
    Quest('#Q8', 'Boucle bornée', "Utiliser une boucle for"),
    Quest('#Q9', 'Boucle non bornée', "Utiliser une boucle while"),
    Quest('#Q10', 'Fonction simple', "Créer et appeler une fonction avec 0 ou 1 argument"),
    Quest('#Q11', 'Commentaires', "Ajouter au moins 3 commentaires pertinents dans le code"),
    Quest('#Q12', 'Structure claire', "Diviser le code en parties lisibles, nommer les variables clairement"),
    Quest('#Q13', 'Erreurs gérées', "Ajouter une gestion d’erreur simple avec try/except"),
    Quest('#Q14', 'Problème quotidien', "Résoudre un petit problème inspiré de la vie courante (recette, monnaie, météo...)"),
    Quest('#Q15', "Inspiration d'une autre matière", "Faire un prototype de programme utile en physique-chimie ou enseignement pro"),
    Quest('#Q16', 'Liste simple', "Créer une liste manuellement (ex : noms = ['A', 'B'])"),
    Quest('#Q17', "Ajout d'éléments", "Ajouter un élément avec .append()"),
    Quest('#Q18', "Suppression d’élément", "Supprimer un élément avec del, .remove() ou pop()"),
    Quest('#Q19', 'Parcours de liste', "Utiliser une boucle pour lire les éléments de la liste"),
    Quest('#Q20', 'Condition sur liste', "Filtrer les éléments (ex : if element > 10)"),
    Quest('#Q21', 'Fonction avec retour', "Créer une fonction qui retourne une valeur (return)"),
    Quest('#Q22', 'Fonction avec plusieurs arguments', "Définir une fonction avec au moins 2 paramètres"),
    Quest('#Q23', 'Modularité', "Organiser le code en plusieurs fonctions réutilisables"),
    Quest('#Q24', 'Liste en compréhension', "Créer une liste avec une compréhension (ex : [x for x in range(10)])"),
    Quest('#Q25', 'Liste conditionnelle', "Ajouter une condition dans une liste en compréhension"),
    Quest('#Q26', 'Structure logique claire', "Bien structurer les blocs conditionnels et boucles imbriquées"),
    Quest('#Q27', 'Docstring', "Ajouter une docstring à chaque fonction (\"\"\"Description\"\"\")"),
    Quest('#Q28', 'Variables booléennes', "Utiliser une variable de type bool"),
    Quest('#Q29', 'Calcul avec plusieurs variables', "Faire un calcul qui combine plusieurs types de données"),
    Quest('#Q30', 'Interface simple', "Ajouter une interaction avec une bibliothèque (tkinter, turtle ou autre)"),
]

# Quêtes secondaires (utilitaires, bonnes pratiques, outils du quotidien)
NEW_QUESTS = [
    Quest('#Q32', 'Somme avec sum()', "Utiliser sum() pour calculer une somme de valeurs dans une liste"),
    Quest('#Q33', 'Comptage avec len()', "Utiliser len() pour compter des éléments (ex : taille d’une liste)"),
    Quest('#Q34', 'Valeur max', "Utiliser max() pour déterminer la valeur maximale"),
    Quest('#Q35', 'Valeur min', "Utiliser min() pour déterminer la valeur minimale"),
    Quest('#Q36', 'Arrondi', "Utiliser round() pour arrondir un résultat"),
    Quest('#Q37', 'Valeur absolue', "Utiliser abs() dans un calcul"),
    Quest('#Q38', 'Génération avec range()', "Utiliser range() pour générer une séquence de nombres"),
    Quest('#Q39', 'Boucle avec enumerate()', "Utiliser enumerate() dans une boucle pour afficher l’index et la valeur"),
    Quest('#Q40', 'Associer deux listes avec zip()', "Utiliser zip() pour parcourir deux listes en parallèle"),
    Quest('#Q41', 'Trier une liste', "Utiliser sorted() pour trier des données"),
    Quest('#Q42', 'Inverser une liste', "Utiliser reversed() pour afficher une liste à l’envers")
]

# Quêtes secrètes (difficiles, cryptiques, pour les plus curieux et avancés)
SECRET_QUESTS = [
    Quest('#S1', 'L’ombre du Copilote', "Utiliser un outil d’IA comme Copilot pour générer du code (et le comprendre)"),
    Quest('#S2', 'Le portail 3D', "Importer et utiliser une librairie 3D comme ursina ou panda3d pour créer une scène"),
    Quest('#S3', 'Le voyageur du temps', "Créer un programme qui manipule des dates et heures avancées (datetime, calendrier)"),
    Quest('#S4', 'L’alchimiste', "Utiliser des modules externes (ex : requests, matplotlib, numpy) pour enrichir un projet"),
    Quest('#S5', 'Le codeur masqué', "Obfusquer une partie de son code ou utiliser des techniques avancées de sécurité"),
    Quest('#S6', 'L’architecte', "Créer un mini-jeu ou une interface graphique avancée (tkinter, turtle, pygame, etc.)"),
    Quest('#S7', 'L’énigme du décorateur', "Utiliser un décorateur Python (@) dans une fonction"),
    Quest('#S8', 'Le maître du multivers', "Créer un script qui interagit avec plusieurs fichiers ou API"),
    Quest('#S9', 'L’invocateur', "Créer et utiliser une classe personnalisée avancée"),
    Quest('#S10', 'L’ultime fusion', "Combiner plusieurs quêtes secrètes dans un même projet")
]
