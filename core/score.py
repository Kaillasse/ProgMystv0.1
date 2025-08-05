import json
from core.quest import QUESTS, NEW_QUESTS, SECRET_QUESTS
from core.analyze import analyser_script
import os

ELEVE_FILE = 'data/eleves.json'

class ScoreManager:
    """
    Gère le calcul et la mise à jour des scores des élèves selon les quêtes réalisées.
    """
    def __init__(self, eleve_file=ELEVE_FILE):
        self.eleve_file = eleve_file
        self.eleves = self.charger_eleves()

    def charger_eleves(self):
        if not os.path.exists(self.eleve_file):
            return []
        with open(self.eleve_file, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []

    def sauvegarder_eleves(self):
        with open(self.eleve_file, 'w', encoding='utf-8') as f:
            json.dump(self.eleves, f, indent=4, ensure_ascii=False)

    def calculer_score(self, quetes_realisees):
        """
        quetes_realisees : liste de codes de quêtes (ex: ['#Q1', '#Q3'])
        Retourne le score total.
        """
        score = 0
        for code in quetes_realisees:
            quest = self.get_quest_by_code(code)
            if quest and quest.score:
                score += quest.score
        return score

    def get_quest_by_code(self, code):
        for q in QUESTS + NEW_QUESTS + SECRET_QUESTS:
            if q.code == code:
                return q
        return None

    def generer_grimoire(self, quetes_realisees, code_extraits=None):
        """
        Génère la liste des pages de grimoire débloquées (une par quête).
        code_extraits : dict optionnel {code_quete: extrait de code}
        """
        grimoire = []
        for code in quetes_realisees:
            quest = self.get_quest_by_code(code)
            if quest:
                page = {
                    'code': quest.code,
                    'titre': quest.nom,
                    'description': quest.description,
                    'competence': quest.nom,
                    'extrait': code_extraits.get(code) if code_extraits else None
                }
                grimoire.append(page)
        return grimoire

    def generer_succes(self, quetes_realisees):
        """
        Génère la liste des succès/médailles débloqués.
        """
        succes = []
        # Succès quêtes principales
        nb_principales = len([q for q in quetes_realisees if q.startswith('#Q') and int(q[2:]) <= 31])
        for i in range(1, nb_principales//5 + 1):
            succes.append(f"Médaille Quêtes principales {i*5}")
        # Succès quêtes secondaires
        nb_secondaires = len([q for q in quetes_realisees if q.startswith('#Q') and int(q[2:]) >= 32])
        for i in range(1, nb_secondaires//5 + 1):
            succes.append(f"Médaille Quêtes secondaires {i*5}")
        # Succès quêtes secrètes
        for code in quetes_realisees:
            if code.startswith('#S'):
                succes.append(f"Succès secret {code}")
        return succes

    def maj_score_eleve(self, nom_eleve, quetes_realisees, code_extraits=None):
        """
        Met à jour le score, les pages de grimoire et les succès d'un élève selon les quêtes réalisées.
        """
        for eleve in self.eleves:
            if eleve.get('nom') == nom_eleve:
                eleve['score'] = self.calculer_score(quetes_realisees)
                eleve['quetes_realisees'] = list(quetes_realisees)
                eleve['grimoire'] = self.generer_grimoire(quetes_realisees, code_extraits)
                eleve['succes'] = self.generer_succes(quetes_realisees)
                self.sauvegarder_eleves()
                return eleve['score']
        return None

    def maj_score_auto(self, nom_eleve, script_path):
        """
        Analyse automatiquement le script de l'élève et met à jour son score, grimoire et succès.
        """
        quetes_realisees = analyser_script(script_path)
        # TODO: extraire les extraits de code pour chaque quête (optionnel)
        code_extraits = {}  # À implémenter plus tard
        return self.maj_score_eleve(nom_eleve, quetes_realisees, code_extraits)

if __name__ == "__main__":
    # Exemple d'utilisation automatique
    manager = ScoreManager()
    # Met à jour le score de Rafaelle en analysant son script dans grimoires/
    score = manager.maj_score_auto('Rafaelle', 'grimoires/rafaelle.py')
    print(f"Nouveau score de Rafaelle (auto) : {score}")
