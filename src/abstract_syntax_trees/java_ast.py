from antlr4 import *
from .generated.JavaLexer import JavaLexer
from .generated.JavaParser import JavaParser
from abc import ABC, abstractmethod
from .abstract_syntax_tree import AbstractSyntaxTree

# curl -O https://www.antlr.org/download/antlr-4.13.1-complete.jar
# sudo mv antlr-4.13.1-complete.jar /usr/local/lib/
# echo 'export CLASSPATH=".:/usr/local/lib/antlr-4.13.1-complete.jar:$CLASSPATH"' >> ~/.bashrc
# echo 'alias antlr4="java -jar /usr/local/lib/antlr-4.13.1-complete.jar"' >> ~/.bashrc
# source ~/.bashrc
# pip install --upgrade antlr4-python3-runtime
# antlr4 -Dlanguage=Python3 JavaLexer.g4 JavaParser.g4 -visitor -o generated

class JavaAST(AbstractSyntaxTree):
    def __init__(self, language):
        super().__init__(language)

    def create_ast(self, source_code) -> str:
        input_stream = InputStream(source_code)
        lexer = JavaLexer(input_stream)
        stream = CommonTokenStream(lexer)
        parser = JavaParser(stream)
        tree = parser.compilationUnit()

        return tree.toStringTree(recog=parser)

    def parse_ast(self):
        """Future implementation for AST traversal."""
        pass

