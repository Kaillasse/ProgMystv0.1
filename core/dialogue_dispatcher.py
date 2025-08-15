# === core/dialogue_dispatcher.py ===
import re
import json
import os


class DialogueDispatcher:
    """
    Dispatche les dialogues depuis un fichier .twee vers le système d'interaction.
    Reconnaît les entrées D1, N0, J0, L0 etc. et retourne le dialogue approprié
    basé sur la progression sauvegardée dans la session.
    """
    
    def __init__(self, twee_path="data/Progmyst.twee"):
        self.twee_path = twee_path
        self.dialogue_data = {}
        self.character_mapping = {
            'D': 'DameIndenta',
            'N': 'Neuill', 
            'J': 'JSON',
            'L': 'Loopfang'
        }
        self.quest_mapping = self._load_quest_mapping()
        self._parse_twee_file()
    
    def _load_quest_mapping(self):
        """Charge le mapping des codes de quête vers les noms"""
        from core.quest import QUESTS, NEW_QUESTS, SECRET_QUESTS
        
        mapping = {}
        for quest in QUESTS + NEW_QUESTS + SECRET_QUESTS:
            mapping[quest.code] = quest.nom
        
        return mapping
    
    def _passage_to_quest_code(self, passage_name):
        """Convertit un nom de passage en code de quête"""
        # Q1 -> #Q1, Q11 -> #Q11, etc.
        if passage_name.startswith('Q') and passage_name[1:].isdigit():
            return f"#{passage_name}"
        return None
    
    def _parse_twee_file(self):
        """Parse le fichier .twee et extrait tous les dialogues."""
        if not os.path.exists(self.twee_path):
            print(f"[DIALOGUE_DISPATCHER] Fichier .twee introuvable: {self.twee_path}")
            return
            
        try:
            with open(self.twee_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Divise le contenu en sections par "::"
            sections = content.split('::')[1:]  # Ignore la première section vide
            
            for section in sections:
                lines = section.strip().split('\n')
                if not lines:
                    continue
                    
                # Parse la première ligne pour le nom et les tags
                header = lines[0].strip()
                
                # Extrait le nom du passage
                if ' [' in header:
                    passage_name = header.split(' [')[0].strip()
                    tags_part = header.split(' [')[1].split(']')[0] if ']' in header else ""
                    tags = [tag.strip() for tag in tags_part.split(',') if tag.strip()]
                elif ' {' in header:
                    passage_name = header.split(' {')[0].strip()
                    tags = []
                else:
                    passage_name = header.strip()
                    tags = []
                
                # Skip les passages système
                if passage_name in ['StoryTitle', 'StoryData']:
                    continue
                
                # Récupère le contenu (lignes 1 et suivantes)
                passage_content = '\n'.join(lines[1:]).strip()
                
                # Parse les liens [[label|target]] ou [[target]]
                links = re.findall(r'\[\[([^\]]*)\]\]', passage_content)
                
                # Retire les liens du texte pour garder seulement le contenu textuel
                text_content = re.sub(r'\[\[([^\]]*)\]\]', '', passage_content).strip()
                
                # Si pas de texte spécifique, utilise le nom du passage
                if not text_content or text_content == '':
                    # Vérifie si c'est un code de quête
                    quest_code = self._passage_to_quest_code(passage_name)
                    if quest_code and quest_code in self.quest_mapping:
                        text_content = self.quest_mapping[quest_code]
                    else:
                        text_content = passage_name
                
                # Parse les réponses à partir des liens
                responses = []
                for link in links:
                    if '|' in link:
                        label, target = link.split('|', 1)
                    else:
                        label = link
                        target = link
                    
                    responses.append({
                        "label": label,
                        "next": target
                    })
                
                # Ajoute automatiquement "+d'info" pour les quêtes
                quest_code = self._passage_to_quest_code(passage_name)
                if quest_code and quest_code in self.quest_mapping:
                    responses.append({
                        "label": "+d'info",
                        "quest_info": quest_code,  # Code de la quête pour récupérer la description
                        "action": "quest_info"
                    })
                
                # Structure le dialogue
                dialogue_entry = {
                    "text": text_content,
                    "responses": responses,
                    "tags": tags,
                    "raw_content": passage_content
                }
                
                self.dialogue_data[passage_name] = dialogue_entry
            
            print(f"[DIALOGUE_DISPATCHER] Chargé {len(self.dialogue_data)} passages depuis {self.twee_path}")
            
        except Exception as e:
            print(f"[DIALOGUE_DISPATCHER] Erreur lors du parsing: {e}")
    
    def get_dialogue_tree_for_npc(self, npc_name, session=None):
        """
        Retourne l'arbre de dialogue pour un PNJ donné en fonction de sa progression.
        """
        # Trouve le code caractère pour ce PNJ
        npc_code = None
        for code, name in self.character_mapping.items():
            if name == npc_name:
                npc_code = code
                break
        
        if not npc_code:
            return self._get_fallback_dialogue(npc_name)
        
        # Détermine le point d'entrée basé sur la progression
        entry_point = self._determine_entry_point(npc_code, session)
        
        # Convertit les données .twee en format d'arbre de dialogue
        return self._build_dialogue_tree(entry_point, npc_code, session)
    
    def _determine_entry_point(self, npc_code, session):
        """
        Détermine le bon point d'entrée pour un PNJ basé sur la progression de la session.
        
        Analyse les quêtes atteignables depuis chaque start et progresse selon:
        - D1 -> D1' (quand toutes les quêtes de D1 sont données)
        - D1' -> D2 (quand toutes les quêtes de D1 sont accomplies)
        - N0 -> N1 (quand Dame Indenta a accompli ses premières quêtes)
        """
        if not session:
            # Points d'entrée par défaut
            default_entries = {'D': 'D1', 'N': 'N0', 'J': 'J0', 'L': 'L0'}
            return default_entries.get(npc_code, f"{npc_code}0")
        
        # Mapping code PNJ -> nom complet
        npc_names = {'D': 'DameIndenta', 'N': 'Neuill', 'J': 'JSON', 'L': 'Loopfang'}
        npc_name = npc_names.get(npc_code)
        
        if not npc_name:
            print(f"[DIALOGUE_DISPATCHER] Code PNJ inconnu: {npc_code}")
            return f"{npc_code}0"
        
        # Logique de progression pour Dame Indenta
        if npc_code == 'D':
            return self._get_dame_indenta_entry_point(session)
        
        # Logique de progression pour autres PNJs (débloqués par Dame Indenta)
        elif npc_code in ['N', 'J', 'L']:
            return self._get_other_npc_entry_point(npc_code, session)
        
        # Fallback
        return f"{npc_code}0"
    
    def _build_dialogue_tree(self, entry_point, npc_code, session=None):
        """
        Construit un arbre de dialogue à partir du point d'entrée.
        """
        if entry_point not in self.dialogue_data:
            print(f"[DIALOGUE_DISPATCHER] Point d'entrée introuvable: {entry_point}")
            return self._get_fallback_dialogue()
        
        tree = {}
        visited = set()
        
        def process_passage(passage_name, tree_key="start"):
            if passage_name in visited or passage_name not in self.dialogue_data:
                return
            
            visited.add(passage_name)
            passage = self.dialogue_data[passage_name]
            
            # Traite les réponses
            responses = []
            for response in passage["responses"]:
                # Vérifier si c'est une action ou un passage suivant
                if "action" in response:
                    # C'est déjà une action (quest_info, end, etc.)
                    responses.append(response.copy())
                    continue
                
                if "next" not in response:
                    # Réponse malformée, ignorer
                    print(f"[DIALOGUE_DISPATCHER] Réponse malformée dans {passage_name}: {response}")
                    continue
                
                next_passage = response["next"]
                
                # Actions spéciales
                if next_passage == "COMBAT":
                    responses.append({
                        "label": response["label"],
                        "action": "start_combat"
                    })
                elif next_passage.startswith("Retour") or next_passage in ["end", "fin"]:
                    responses.append({
                        "label": response["label"],
                        "action": "end"
                    })
                else:
                    # Lien vers un autre passage
                    responses.append({
                        "label": response["label"],
                        "next": next_passage
                    })
                    
                    # Traite récursivement le passage suivant
                    if next_passage in self.dialogue_data:
                        process_passage(next_passage, next_passage)
            
            # Si pas de réponses, ajoute une option de fin
            if not responses:
                responses.append({
                    "label": "Au revoir",
                    "action": "end"
                })
            
            tree[tree_key] = {
                "text": passage["text"],
                "responses": responses
            }
        
        # Lance le processus depuis le point d'entrée
        process_passage(entry_point, "start")
        
        # Donne automatiquement les quêtes découvertes dans l'arbre
        if session:
            self._give_quests_from_tree(tree, session)
            # Met à jour l'état du dialogue après interaction
            self._update_dialogue_state(entry_point, npc_code, session)
        
        return tree
    
    def _give_quests_from_tree(self, tree, session):
        """Donne automatiquement toutes les quêtes trouvées dans l'arbre de dialogue"""
        if not session:
            return
        
        for node_name, node_data in tree.items():
            # Vérifie si le texte correspond à une quête
            for quest_code in self.quest_mapping:
                if node_data.get("text") == self.quest_mapping[quest_code]:
                    # Cette quête a été mentionnée, la donner au joueur
                    if not session.is_quest_given(quest_code):
                        session.give_quest(quest_code)
                        print(f"[DIALOGUE_DISPATCHER] Quête donnée automatiquement: {quest_code}")
                    break
            
            # Vérifie aussi par le nom du node (par exemple Q11)
            quest_code = self._passage_to_quest_code(node_name)
            if quest_code and quest_code in self.quest_mapping:
                if not session.is_quest_given(quest_code):
                    session.give_quest(quest_code)
                    print(f"[DIALOGUE_DISPATCHER] Quête donnée automatiquement via passage: {quest_code}")
    
    def _get_fallback_dialogue(self, npc_name="PNJ"):
        """Dialogue de secours si aucun dialogue spécifique n'est trouvé."""
        return {
            "start": {
                "text": f"{npc_name} vous salue silencieusement.",
                "responses": [
                    {"label": "Saluer", "next": "greeting"},
                    {"label": "Au revoir", "action": "end"}
                ]
            },
            "greeting": {
                "text": f"{npc_name} hoche la tête.",
                "responses": [
                    {"label": "Au revoir", "action": "end"}
                ]
            }
        }
    
    def list_available_dialogues(self, npc_code=None):
        """Liste tous les dialogues disponibles, optionnellement filtrés par code PNJ."""
        if npc_code:
            return [name for name in self.dialogue_data.keys() if name.startswith(npc_code)]
        return list(self.dialogue_data.keys())
    
    def get_passage_info(self, passage_name):
        """Retourne les informations détaillées d'un passage."""
        return self.dialogue_data.get(passage_name, None)
    
    def _get_dame_indenta_entry_point(self, session):
        """Logique de progression pour Dame Indenta: D1 -> D1' -> D2 -> D2' -> D3"""
        # Analyse les quêtes atteignables depuis D1
        d1_quests = self._get_quests_reachable_from_start('D1')
        
        # Vérifie si toutes les quêtes D1 sont accomplies -> D2
        if d1_quests and all(session.is_quest_completed(q) for q in d1_quests):
            # Vérifier si on peut aller plus loin (D2' ou D3)
            d2_quests = self._get_quests_reachable_from_start('D2')
            if d2_quests and all(session.is_quest_completed(q) for q in d2_quests):
                return 'D3'  # Toutes les quêtes D2 accomplies
            return 'D2'  # Quêtes D1 accomplies, passé à D2
        
        # Vérifie si toutes les quêtes D1 sont données -> D1'
        elif d1_quests and all(session.is_quest_given(q) for q in d1_quests):
            return 'D1\''
        
        # État initial
        return 'D1'
    
    def _get_other_npc_entry_point(self, npc_code, session):
        """Logique de progression pour autres PNJs (débloqués par Dame Indenta)"""
        # Vérifie si Dame Indenta a accompli ses premières quêtes (déblocage)
        d1_quests = self._get_quests_reachable_from_start('D1')
        if not d1_quests or not all(session.is_quest_completed(q) for q in d1_quests):
            # Dame Indenta n'a pas encore accompli ses quêtes, autres PNJs restent bloqués
            return f"{npc_code}0"
        
        # Dame Indenta a accompli ses quêtes D1, déblocage vers N1/J1/L1
        start_1 = f"{npc_code}1"
        
        # Analyse les quêtes de ce PNJ depuis son niveau 1
        npc_quests_1 = self._get_quests_reachable_from_start(start_1)
        
        if npc_quests_1 and all(session.is_quest_completed(q) for q in npc_quests_1):
            return f"{npc_code}2"  # Quêtes niveau 1 accomplies -> niveau 2
        elif npc_quests_1 and all(session.is_quest_given(q) for q in npc_quests_1):
            return start_1  # Quêtes données -> reste niveau 1
        
        return start_1  # État initial débloqué -> N1/J1/L1
    
    def _get_quests_reachable_from_start(self, start_passage):
        """Analyse et retourne toutes les quêtes atteignables depuis un point de départ"""
        if start_passage not in self.dialogue_data:
            return []
        
        visited = set()
        quests = set()
        
        def explore_passage(passage_name):
            if passage_name in visited or passage_name not in self.dialogue_data:
                return
            
            visited.add(passage_name)
            passage = self.dialogue_data[passage_name]
            
            # Vérifie si ce passage est une quête
            quest_code = self._passage_to_quest_code(passage_name)
            if quest_code and quest_code in self.quest_mapping:
                quests.add(quest_code)
            
            # Explore les liens récursivement
            for response in passage.get('responses', []):
                if 'next' in response:
                    next_passage = response['next']
                    # Évite les retours et fins
                    if not (next_passage.startswith('Retour') or 
                           next_passage in ['end', 'fin', 'COMBAT']):
                        explore_passage(next_passage)
        
        explore_passage(start_passage)
        return list(quests)
    
    def _update_dialogue_state(self, entry_point, npc_code, session):
        """Met à jour l'état du dialogue après interaction"""
        # Mapping code -> nom complet
        npc_names = {'D': 'DameIndenta', 'N': 'Neuill', 'J': 'JSON', 'L': 'Loopfang'}
        npc_name = npc_names.get(npc_code)
        
        if not npc_name:
            return
        
        # Sauvegarde l'état actuel du dialogue
        session.set_dialogue_state(npc_name, entry_point)
        print(f"[DIALOGUE_DISPATCHER] État sauvegardé: {npc_name} -> {entry_point}")