# === core/quest_analyzer.py ===
import os
import re
from core.quest import QUESTS, NEW_QUESTS, SECRET_QUESTS
from core.settings import get_grimoire_path


class QuestAnalyzer:
    """
    Analyse le grimoire du joueur pour déterminer quelles quêtes sont accomplies.
    Une fois qu'une quête est marquée comme accomplie, elle reste validée même si 
    le contenu du grimoire est effacé.
    """
    
    def __init__(self, session):
        self.session = session
        self.all_quests = QUESTS + NEW_QUESTS + SECRET_QUESTS
        self.quest_patterns = self._create_quest_patterns()
    
    def _create_quest_patterns(self):
        """Crée les patterns de détection pour chaque quête"""
        patterns = {}
        
        # Patterns pour détecter les différentes quêtes dans le code
        quest_detection = {
            '#Q1': [r'print\s*\(', r'afficher'],  # Affichage
            '#Q2': [r'^\s*\w+\s*=', r'variable'],  # Variables simples
            '#Q3': [r'=\s*[^=]', r'affectation'],  # Affectation
            '#Q4': [r'input\s*\(', r'lecture'],  # Lecture utilisateur
            '#Q5': [r'\bif\b', r'condition'],  # Condition simple
            '#Q6': [r'\bif\b.*\belse\b', r'if.*else'],  # Condition double
            '#Q7': [r'\belif\b', r'condition.*imbriquée'],  # Condition imbriquée
            '#Q8': [r'\bfor\b.*\bin\b', r'boucle.*bornée'],  # Boucle bornée
            '#Q9': [r'\bwhile\b', r'boucle.*non.*bornée'],  # Boucle non bornée
            '#Q10': [r'\bdef\b\s+\w+\s*\(', r'fonction'],  # Fonction simple
            '#Q11': [r'#.*\w', r'commentaire'],  # Commentaires (3+ requis)
            '#Q12': [r'def\b', r'structure'],  # Structure claire
            '#Q13': [r'\btry\b.*\bexcept\b', r'gestion.*erreur'],  # Erreurs gérées
            '#Q14': [r'problème|quotidien|recette|monnaie|météo', r'vie.*courante'],  # Problème quotidien
            '#Q15': [r'physique|chimie|enseignement|pro', r'autre.*matière'],  # Inspiration autre matière
            '#Q16': [r'\[.*\]', r'liste'],  # Liste simple
            '#Q17': [r'\.append\s*\(', r'ajout.*élément'],  # Ajout d'éléments
            '#Q18': [r'\bdel\b|\.remove\s*\(|\.pop\s*\(', r'suppression.*élément'],  # Suppression d'élément
            '#Q19': [r'\bfor\b.*\bin\b.*\[', r'parcours.*liste'],  # Parcours de liste
            '#Q20': [r'\bif\b.*\bin\b', r'condition.*liste'],  # Condition sur liste
            '#Q21': [r'\breturn\b', r'fonction.*retour'],  # Fonction avec retour
            '#Q22': [r'\bdef\b.*\(.*,.*\)', r'fonction.*arguments'],  # Fonction avec plusieurs arguments
            '#Q23': [r'\bdef\b.*\n[\s\S]*\bdef\b', r'modularité'],  # Modularité
            '#Q24': [r'\[.*\bfor\b.*\bin\b.*\]', r'liste.*compréhension'],  # Liste en compréhension
            '#Q25': [r'\[.*\bfor\b.*\bif\b.*\]', r'liste.*conditionnelle'],  # Liste conditionnelle
            '#Q26': [r'if.*elif.*else', r'logique.*claire'],  # Structure logique claire
            '#Q27': [r'""".*"""', r'docstring'],  # Docstring
            '#Q28': [r'\b(True|False)\b|bool\s*\(', r'booléen'],  # Variables booléennes
            '#Q29': [r'[+\-*/].*[+\-*/]', r'calcul.*variables'],  # Calcul avec plusieurs variables
            '#Q30': [r'import.*tkinter|import.*turtle|import.*pygame', r'interface'],  # Interface simple
            
            # NEW_QUESTS
            '#Q32': [r'\bsum\s*\(', r'somme'],  # Somme avec sum()
            '#Q33': [r'\blen\s*\(', r'comptage'],  # Comptage avec len()
            '#Q34': [r'\bmax\s*\(', r'valeur.*max'],  # Valeur max
            '#Q35': [r'\bmin\s*\(', r'valeur.*min'],  # Valeur min
            '#Q36': [r'\bround\s*\(', r'arrondi'],  # Arrondi
            '#Q37': [r'\babs\s*\(', r'valeur.*absolue'],  # Valeur absolue
            '#Q38': [r'\brange\s*\(', r'génération'],  # Génération avec range()
            '#Q39': [r'\benumerate\s*\(', r'enumerate'],  # Boucle avec enumerate()
            '#Q40': [r'\bzip\s*\(', r'associer.*listes'],  # Associer deux listes avec zip()
            '#Q41': [r'\bsorted\s*\(', r'trier'],  # Trier une liste
            '#Q42': [r'\breversed\s*\(', r'inverser'],  # Inverser une liste
            
            # SECRET_QUESTS
            '#S1': [r'copilot|ia|ai|intelligence.*artificielle', r'copilote'],  # L'ombre du Copilote
            '#S2': [r'import.*ursina|import.*panda3d|3d', r'portail.*3d'],  # Le portail 3D
            '#S3': [r'import.*datetime|import.*calendar', r'voyageur.*temps'],  # Le voyageur du temps
            '#S4': [r'import.*requests|import.*matplotlib|import.*numpy', r'alchimiste'],  # L'alchimiste
            '#S5': [r'obfusqu|sécurité|cryptage|hash', r'codeur.*masqué'],  # Le codeur masqué
            '#S6': [r'mini.*jeu|interface.*graphique|pygame', r'architecte'],  # L'architecte
            '#S7': [r'@\w+|décorateur', r'énigme.*décorateur'],  # L'énigme du décorateur
            '#S8': [r'fichier|api|json|csv', r'maître.*multivers'],  # Le maître du multivers
            '#S9': [r'\bclass\b.*:', r'invocateur'],  # L'invocateur
            '#S10': [r'fusion|combinaison|projet.*avancé', r'ultime.*fusion']  # L'ultime fusion
        }
        
        return quest_detection
    
    def analyze_grimoire(self, force_recheck=False):
        """
        Analyse le grimoire et met à jour le statut des quêtes.
        
        Args:
            force_recheck: Si True, re-analyse même les quêtes déjà marquées comme accomplies
        """
        if not self.session:
            print("[QUEST_ANALYZER] Aucune session disponible")
            return
        
        grimoire_path = get_grimoire_path(self.session.name)
        
        if not os.path.exists(grimoire_path):
            print(f"[QUEST_ANALYZER] Grimoire non trouvé: {grimoire_path}")
            return
        
        # Charge le contenu du grimoire
        try:
            with open(grimoire_path, 'r', encoding='utf-8') as f:
                grimoire_content = f.read().lower()
        except Exception as e:
            print(f"[QUEST_ANALYZER] Erreur lecture grimoire: {e}")
            return
        
        # Assure que la section quests existe dans la session
        if 'quests' not in self.session.data:
            self.session.data['quests'] = {}
        
        quests_data = self.session.data['quests']
        newly_completed = []
        
        # Analyse chaque quête
        for quest in self.all_quests:
            quest_code = quest.code
            
            # Skip si déjà analysée et pas de force recheck
            if not force_recheck and quests_data.get(quest_code, {}).get('completed', False):
                continue
            
            # Vérifie si la quête est accomplie
            is_completed = self._check_quest_completion(quest_code, grimoire_content)
            
            # Met à jour les données de la quête
            if quest_code not in quests_data:
                quests_data[quest_code] = {
                    'given': False,
                    'completed': False,
                    'name': quest.nom,
                    'description': quest.description
                }
            
            # Marque comme accomplie si détectée
            if is_completed and not quests_data[quest_code]['completed']:
                quests_data[quest_code]['completed'] = True
                newly_completed.append(quest.nom)
                print(f"[QUEST_ANALYZER] Quête accomplie détectée: {quest_code} - {quest.nom}")
        
        # Sauvegarde les modifications
        if newly_completed:
            self.session.save_data()
            print(f"[QUEST_ANALYZER] {len(newly_completed)} nouvelles quêtes accomplies")
        
        return newly_completed
    
    def _check_quest_completion(self, quest_code, grimoire_content):
        """Vérifie si une quête spécifique est accomplie selon son code"""
        patterns = self.quest_patterns.get(quest_code, [])
        
        if not patterns:
            return False
        
        # Vérifie chaque pattern de la quête
        for pattern in patterns:
            if re.search(pattern, grimoire_content, re.IGNORECASE | re.MULTILINE):
                # Cas spécial pour les commentaires (Q11) - il faut au moins 3
                if quest_code == '#Q11':
                    comment_matches = re.findall(r'#.*\w', grimoire_content)
                    return len(comment_matches) >= 3
                
                return True
        
        return False
    
    def mark_quest_as_given(self, quest_code):
        """Marque une quête comme donnée par un PNJ"""
        if 'quests' not in self.session.data:
            self.session.data['quests'] = {}
        
        if quest_code not in self.session.data['quests']:
            # Trouve la quête correspondante
            quest_obj = None
            for quest in self.all_quests:
                if quest.code == quest_code:
                    quest_obj = quest
                    break
            
            if quest_obj:
                self.session.data['quests'][quest_code] = {
                    'given': True,
                    'completed': False,
                    'name': quest_obj.nom,
                    'description': quest_obj.description
                }
            else:
                self.session.data['quests'][quest_code] = {
                    'given': True,
                    'completed': False,
                    'name': quest_code,
                    'description': 'Quête inconnue'
                }
        else:
            self.session.data['quests'][quest_code]['given'] = True
        
        self.session.save_data()
        print(f"[QUEST_ANALYZER] Quête marquée comme donnée: {quest_code}")
    
    def get_quest_status(self, quest_code):
        """Retourne le statut d'une quête"""
        if 'quests' not in self.session.data:
            return {'given': False, 'completed': False}
        
        return self.session.data['quests'].get(quest_code, {'given': False, 'completed': False})
    
    def get_given_quests(self):
        """Retourne toutes les quêtes données"""
        if 'quests' not in self.session.data:
            return []
        
        given_quests = []
        for quest_code, quest_data in self.session.data['quests'].items():
            if quest_data.get('given', False):
                given_quests.append({
                    'code': quest_code,
                    'name': quest_data.get('name', quest_code),
                    'description': quest_data.get('description', ''),
                    'completed': quest_data.get('completed', False)
                })
        
        return given_quests
    
    def get_completed_quests(self):
        """Retourne toutes les quêtes accomplies"""
        if 'quests' not in self.session.data:
            return []
        
        completed_quests = []
        for quest_code, quest_data in self.session.data['quests'].items():
            if quest_data.get('completed', False):
                completed_quests.append({
                    'code': quest_code,
                    'name': quest_data.get('name', quest_code),
                    'description': quest_data.get('description', '')
                })
        
        return completed_quests