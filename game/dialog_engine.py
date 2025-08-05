import pygame
from core.quest import QUESTS
from core.analyze import analyser_script

class DialogEngine:
    """Gestionnaire des dialogues et des quêtes"""
    
    def __init__(self):
        self.active_quests = {}  # {quest_code: completed}
        self.completed_quests = set()
        
    def initialize_quests(self):
        """Initialise les 5 premières quêtes"""
        initial_quests = ['#Q1', '#Q2', '#Q3', '#Q4', '#Q5']
        for quest_code in initial_quests:
            self.active_quests[quest_code] = False
            
    def check_quest_completion(self, script_path):
        """Vérifie la complétion des quêtes actives"""
        completed = analyser_script(script_path)
        for quest_code in self.active_quests.keys():
            if quest_code in completed and not self.active_quests[quest_code]:
                self.active_quests[quest_code] = True
                self.completed_quests.add(quest_code)
                print(f"[QUEST] Quête {quest_code} complétée!")
                
    def get_quest_status(self):
        """Retourne l'état des quêtes actives"""
        status = []
        for quest_code, completed in self.active_quests.items():
            quest = next((q for q in QUESTS if q.code == quest_code), None)
            if quest:
                status.append({
                    'code': quest.code,
                    'name': quest.nom,
                    'description': quest.description,
                    'completed': completed,
                    'score': quest.score
                })
        return status
