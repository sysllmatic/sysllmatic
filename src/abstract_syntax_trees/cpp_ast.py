from abstract_syntax_trees.abstract_syntax_tree import AbstractSyntaxTree
import subprocess
import re

class CPPAST(AbstractSyntaxTree):
    def __init__(self, language):
        super().__init__(language)

    def create_ast(self, source_code_path, entry_point) -> str:
        command = f"clang++ -Xclang -ast-dump -fsyntax-only {source_code_path} | grep -A 150 {entry_point}"
        ast = subprocess.run(command, shell=True, capture_output=True, text=True)
        ast_output = ast.stdout
        # If the AST output is more than 150 lines, return empty string
        if len(ast_output.splitlines()) > 150:
            return ""  # Return empty string if AST output exceeds 150 lines
        return self.clean_ast(ast_output)
    
    def clean_ast(self, ast_text):
        # Remove memory addresses (0x followed by hex digits)
        ast_text = re.sub(r'0x[0-9a-fA-F]+', '', ast_text)
        
        # Remove file path and location info inside <>
        ast_text = re.sub(r'<[^>]+>', '', ast_text)
        
        # Remove line and column markers (e.g., line:4:5, col:19)
        ast_text = re.sub(r'\b(line|col):\d+(:\d+)?', '', ast_text)

        # Remove excessive spaces from cleaned lines while keeping line breaks
        ast_text = '\n'.join(line.strip() for line in ast_text.splitlines())
        
        return ast_text   
    
    def parse_ast(self):
        """
        Implement later based on how we decide to use the AST.
        """
        pass