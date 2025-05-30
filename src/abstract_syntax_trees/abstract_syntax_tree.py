from abc import ABC, abstractmethod


class AbstractSyntaxTree:
    def __init__(self, language):
        self.language = language    

    @abstractmethod
    def create_ast(self, source_code):
        pass

    @abstractmethod
    def parse_ast(self):
        """
        Implement later based on how we decide to use the AST.
        """
        pass