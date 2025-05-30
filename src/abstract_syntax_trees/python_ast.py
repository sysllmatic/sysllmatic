from .abstract_syntax_tree import AbstractSyntaxTree
import ast


class PythonAST(AbstractSyntaxTree):
    def __init__(self, language):
        super().__init__(language)

    def create_ast(self, source_code_path) -> str:
        code_file = open(source_code_path, "r")
        source_code = code_file.read()
        parsed_ast = ast.parse(source_code)

        return ast.dump(parsed_ast, indent=4)
        
    def parse_ast(self):
        """
        Implement later based on how we decide to use the AST.
        """
        pass