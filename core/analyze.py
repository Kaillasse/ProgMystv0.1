import ast
from core.quest import QUESTS

class QuestAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.reset()

    def reset(self):
        # Variables pour les 5 premières quêtes
        self.variables = set()
        self.has_affectation = False
        self.has_print = False
        self.has_input = False
        self.has_if = False
        # Variables pour les quêtes avancées
        self.has_if_else = False
        self.has_if_elif_else = False
        self.has_for = False
        self.has_while = False
        self.has_function = False
        self.has_function_args = False
        self.has_return = False
        self.comments = 0
        self.has_try = False
        self.has_list = False
        self.has_append = False
        self.has_remove = False
        self.has_list_comp = False
        self.has_bool = False
        self.has_docstring = False
        # Fonctionnalités Python standards
        self.has_sum = False
        self.has_len = False
        self.has_max = False
        self.has_min = False
        self.has_range = False
        # Quêtes avancées
        self.has_list_loop = False  # Q19
        self.has_list_filter = False  # Q20
        self.has_func_return = False  # Q21
        self.has_func_args2 = False  # Q22
    def visit_For(self, node):
        self.has_for = True
        # Q19: Parcours de liste
        if isinstance(node.iter, ast.Name):
            self.has_list_loop = True
        # Q20: Condition sur liste
        for stmt in ast.walk(node):
            if isinstance(stmt, ast.If):
                self.has_list_filter = True
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self.has_function = True
        if len(node.args.args) > 1:
            self.has_function_args = True
            self.has_func_args2 = True  # Q22
        if node.returns is not None:
            self.has_return = True
        if ast.get_docstring(node):
            self.has_docstring = True
        # Q21: Fonction avec return
        for stmt in ast.walk(node):
            if isinstance(stmt, ast.Return):
                self.has_func_return = True
        self.generic_visit(node)

    def visit_Assign(self, node):
        self.has_affectation = True
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.variables.add(target.id)
        self.generic_visit(node)

    def visit_AnnAssign(self, node):
        self.has_affectation = True
        if isinstance(node.target, ast.Name):
            self.variables.add(node.target.id)
        self.generic_visit(node)

    def visit_Expr(self, node):
        # Docstring
        if isinstance(node.value, ast.Str):
            self.has_docstring = True
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            if node.func.id == 'print':
                self.has_print = True
            if node.func.id == 'input':
                self.has_input = True
            if node.func.id == 'append':
                self.has_append = True
            if node.func.id in ('remove', 'pop'):
                self.has_remove = True
            if node.func.id == 'sum':
                self.has_sum = True
            if node.func.id == 'len':
                self.has_len = True
            if node.func.id == 'max':
                self.has_max = True
            if node.func.id == 'min':
                self.has_min = True
            if node.func.id == 'round':
                self.has_round = True
            if node.func.id == 'abs':
                self.has_abs = True
            if node.func.id == 'range':
                self.has_range = True
            if node.func.id == 'enumerate':
                self.has_enumerate = True
            if node.func.id == 'zip':
                self.has_zip = True
            if node.func.id == 'sorted':
                self.has_sorted = True
            if node.func.id == 'reversed':
                self.has_reversed = True
        self.generic_visit(node)

    def visit_If(self, node):
        self.has_if = True
        if node.orelse:
            if any(isinstance(stmt, ast.If) for stmt in node.orelse):
                self.has_if_elif_else = True
            else:
                self.has_if_else = True
        self.generic_visit(node)

    def visit_For(self, node):
        self.has_for = True
        self.generic_visit(node)

    def visit_While(self, node):
        self.has_while = True
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self.has_function = True
        if len(node.args.args) > 1:
            self.has_function_args = True
        if node.returns is not None:
            self.has_return = True
        if ast.get_docstring(node):
            self.has_docstring = True
        self.generic_visit(node)

    def visit_Return(self, node):
        self.has_return = True
        self.generic_visit(node)

    def visit_Try(self, node):
        self.has_try = True
        self.generic_visit(node)

    def visit_List(self, node):
        self.has_list = True
        self.generic_visit(node)

    def visit_ListComp(self, node):
        self.has_list_comp = True
        self.generic_visit(node)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Store) and node.id not in self.variables:
            self.variables.add(node.id)
        if node.id in ('True', 'False'):
            self.has_bool = True
        self.generic_visit(node)

    def analyze(self, code):
        """Analyse le code source du grimoire"""
        self.reset()
        try:
            tree = ast.parse(code)
            self.visit(tree)
        except SyntaxError:
            print("[ANALYZE] Erreur de syntaxe dans le grimoire")
            return []
        except Exception as e:
            print(f"[ANALYZE] Erreur lors de l'analyse du grimoire: {str(e)}")
            return []
        return self.get_quetes()

    def get_quetes(self):
        """Retourne la liste des quêtes complétées"""
        quetes = []
        # Quêtes principales (5 premières)
        if len(self.variables) >= 2:
            quetes.append('#Q1')  # Variables
        if self.has_affectation:
            quetes.append('#Q2')  # Affectation
        if self.has_print:
            quetes.append('#Q3')  # Print
        if self.has_input:
            quetes.append('#Q4')  # Input
        if self.has_if:
            quetes.append('#Q5')  # If
            
        # Quêtes avancées
        if self.has_if_else:
            quetes.append('#Q6')  # If/Else
        if self.has_if_elif_else:
            quetes.append('#Q7')  # If/Elif/Else
        if self.has_for:
            quetes.append('#Q8')  # For
        if self.has_while:
            quetes.append('#Q9')  # While
        if self.has_function:
            quetes.append('#Q10')  # Function
        if self.comments >= 3:
            quetes.append('#Q11')  # Comments
        if self.has_try:
            quetes.append('#Q13')  # Try/Except
            
        # Structures de données
        if self.has_list:
            quetes.append('#Q16')  # List
        if self.has_append:
            quetes.append('#Q17')  # Append
        if self.has_remove:
            quetes.append('#Q18')  # Remove
        if self.has_list_loop:
            quetes.append('#Q19')  # List loop
        if self.has_list_filter:
            quetes.append('#Q20')  # List filter
            
        # Fonctions avancées
        if self.has_func_return:
            quetes.append('#Q21')  # Return
        if self.has_func_args2:
            quetes.append('#Q22')  # Multiple args
        return quetes

def analyser_script(path):
    with open(path, 'r', encoding='utf-8') as f:
        code = f.read()
    analyzer = QuestAnalyzer()
    return analyzer.analyze(code)

if __name__ == "__main__":
    # Exemple d'utilisation
    script = input("Chemin du script à analyser (ex: grimoires/nom.py) : ")
    quetes = analyser_script(script)
    print("Quêtes détectées :", quetes)
