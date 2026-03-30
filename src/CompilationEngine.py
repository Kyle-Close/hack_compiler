from pathlib import Path
import xml.etree.ElementTree as ET

from src.Enums import KeyWord, TokenType
from src.JackTokenizer import JackTokenizer


class CompilationEngine:
    def __init__(self, path: Path):
        p = Path(path).with_suffix(".xml")
        self.out_file = open(p, "w")
        self.tokenizer = JackTokenizer(path)
        self.tree = ET.ElementTree(ET.Element("tokens"))

        if self.tokenizer.has_more_tokens():
            self.tokenizer.advance()
            self.compile_class()
            ET.indent(self.tree, space="  ")
            self.tree.write(p)


    def compile_class(self):
        # 'class' className '{' classVarDec* subroutineDec* '}'
        class_el = ET.SubElement(self.tree.getroot(), "class")

        # class keyword
        ET.SubElement(class_el, "keyword").text = self.tokenizer.current_token
        self.tokenizer.advance()

        # identifier - className
        ET.SubElement(class_el, "identifier").text = self.tokenizer.current_token
        self.tokenizer.advance()

        # symbol - '{'
        ET.SubElement(class_el, "symbol").text = self.tokenizer.current_token
        self.tokenizer.advance()

        self.compile_class_var_dec(class_el)
        self.compile_subroutine(class_el)

        pass

    def compile_class_var_dec(self, parent_el):
        # ('static' | 'field') type varName (',' varName)* ';'
        keyword = self.tokenizer.key_word()
        if keyword == KeyWord.STATIC or keyword == KeyWord.FIELD:
            class_var_dec_el = ET.SubElement(parent_el, "classVarDec")
        else:
            return

        ET.SubElement(class_var_dec_el, "keyword").text = "static" if keyword == KeyWord.STATIC else "field"
        self.tokenizer.advance()

        # type - int (keyword), char (keyword), boolean (keyword), or className (identifier)
        if self.tokenizer.token_type() == TokenType.IDENTIFIER:
            ET.SubElement(class_var_dec_el, "identifier").text = self.tokenizer.current_token
        else:
            ET.SubElement(class_var_dec_el, "keyword").text = self.tokenizer.current_token
        self.tokenizer.advance()

        # identifier - varName
        ET.SubElement(class_var_dec_el, "identifier").text = self.tokenizer.current_token
        self.tokenizer.advance()

        while self.tokenizer.current_token != ";":
            # symbol - ','
            ET.SubElement(class_var_dec_el, "symbol").text = self.tokenizer.current_token
            self.tokenizer.advance()
            # identifier - varName
            ET.SubElement(class_var_dec_el, "identifier").text = self.tokenizer.current_token
            self.tokenizer.advance()

        # symbol - ';'
        ET.SubElement(class_var_dec_el, "symbol").text = self.tokenizer.current_token
        self.tokenizer.advance()

        self.compile_class_var_dec(parent_el)

    def compile_subroutine(self, parent_el):
        # ('constructor' | 'function' | 'method') ('void' | type) subroutineName '(' parameterList ')' subroutineBody
        token_type = self.tokenizer.token_type()
        if token_type == TokenType.KEYWORD:
            class_var_dec_el = ET.SubElement(parent_el, "subroutineDec")
        else:
            return

        # keyword - constructor | function | method
        ET.SubElement(class_var_dec_el, "keyword").text = self.tokenizer.current_token
        self.tokenizer.advance()

        # identifier | keyword - void (keyword) | type -> int (keyword), char (keyword), boolean (keyword), or className (identifier)
        if self.tokenizer.token_type() == TokenType.IDENTIFIER:
            ET.SubElement(class_var_dec_el, "identifier").text = self.tokenizer.current_token
        else:
            ET.SubElement(class_var_dec_el, "keyword").text = self.tokenizer.current_token
        self.tokenizer.advance()

        # identifier - subroutineName
        ET.SubElement(class_var_dec_el, "identifier").text = self.tokenizer.current_token
        self.tokenizer.advance()

        # symbol - '('
        ET.SubElement(class_var_dec_el, "symbol").text = self.tokenizer.current_token
        self.tokenizer.advance()

        if self.tokenizer.current_token != ")":
            param_list_el = ET.SubElement(class_var_dec_el, "parameterList")
            self.compile_parameter_list(param_list_el)

        # symbol - ')'
        ET.SubElement(class_var_dec_el, "symbol").text = self.tokenizer.current_token
        self.tokenizer.advance()

        # subroutineBody
        self.compile_subroutine_body()

    def compile_parameter_list(self, param_list_el):
        if self.tokenizer.current_token == ")":
            return

        # type - int (keyword), char (keyword), boolean (keyword), or className (identifier)
        if self.tokenizer.token_type() == TokenType.IDENTIFIER:
            ET.SubElement(param_list_el, "identifier").text = self.tokenizer.current_token
        else:
            ET.SubElement(param_list_el, "keyword").text = self.tokenizer.current_token

        self.tokenizer.advance()

        # identifier - varName
        ET.SubElement(param_list_el, "identifier").text = self.tokenizer.current_token
        self.tokenizer.advance()

        # symbol - ','
        if self.tokenizer.current_token == ",":
            ET.SubElement(param_list_el, "symbol").text = self.tokenizer.current_token
            self.tokenizer.advance()

        self.compile_parameter_list(param_list_el)

    def compile_subroutine_body(self):
        pass

    def compile_var_dec(self):
        pass

    def compile_statements(self):
        pass

    def compile_let(self):
        pass

    def compile_if(self):
        pass

    def compile_while(self):
        pass

    def compile_do(self):
        pass

    def compile_return(self):
        pass

    # defer
    def compile_expression(self):
        pass

    def compile_term(self):
        pass

    def compile_expression_list(self):
        pass