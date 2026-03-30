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

        # parameterList
        if self.tokenizer.current_token != ")":
            param_list_el = ET.SubElement(class_var_dec_el, "parameterList")
            self.compile_parameter_list(param_list_el)

        # symbol - ')'
        ET.SubElement(class_var_dec_el, "symbol").text = self.tokenizer.current_token
        self.tokenizer.advance()

        # subroutineBody
        self.compile_subroutine_body(class_var_dec_el)

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

    def compile_subroutine_body(self, parent_el):
        # '{' varDec* statements '}'
        subroutine_body_el = ET.SubElement(parent_el, "subroutineBody")

        # symbol - '{'
        ET.SubElement(subroutine_body_el, "symbol").text = self.tokenizer.current_token
        self.tokenizer.advance()

        # varDec*
        self.compile_var_dec(subroutine_body_el)

        # statements
        self.compile_statements(subroutine_body_el)

    def compile_var_dec(self, parent_el):
        if self.tokenizer.key_word() != KeyWord.VAR:
            return

        var_dec_el = ET.SubElement(parent_el, "varDec")

        # 'var' type varName (',' varName)* ';'
        ET.SubElement(var_dec_el, "keyword").text = self.tokenizer.current_token
        self.tokenizer.advance()

        # type - int (keyword), char (keyword), boolean (keyword), or className (identifier)
        if self.tokenizer.token_type() == TokenType.IDENTIFIER:
            ET.SubElement(var_dec_el, "identifier").text = self.tokenizer.current_token
        else:
            ET.SubElement(var_dec_el, "keyword").text = self.tokenizer.current_token
        self.tokenizer.advance()

        # identifier - varName
        ET.SubElement(var_dec_el, "identifier").text = self.tokenizer.current_token
        self.tokenizer.advance()

        # (',' varName)*
        while self.tokenizer.current_token != ";":
            # symbol - ','
            ET.SubElement(var_dec_el, "symbol").text = self.tokenizer.current_token
            self.tokenizer.advance()
            # identifier - varName
            ET.SubElement(var_dec_el, "identifier").text = self.tokenizer.current_token
            self.tokenizer.advance()

        # symbol ';'
        ET.SubElement(var_dec_el, "symbol").text = self.tokenizer.current_token
        self.tokenizer.advance()

        self.compile_var_dec(parent_el)

    def compile_statements(self, parent_el):
        # statement*
        # letStatement | ifStatement | whileStatement | doStatement | returnStatement
        pass

    def compile_let(self, parent_el):
        # 'let' varName ('[' expression ']')? '=' expression ';'
        let_statement_el = ET.SubElement(parent_el, "letStatement")

        # keyword - let
        ET.SubElement(let_statement_el, "keyword").text = self.tokenizer.current_token
        self.tokenizer.advance()

        # identifier - varName
        ET.SubElement(let_statement_el, "identifier").text = self.tokenizer.current_token
        self.tokenizer.advance()

        # TODO: handle expression

        # symbol - '='
        ET.SubElement(let_statement_el, "symbol").text = self.tokenizer.current_token
        self.tokenizer.advance()

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
    def compile_expression(self, parent_el):
        # term (op term)*
        self.compile_term(parent_el)
        pass

    def compile_term(self, parent_el):
        # integerConstant | stringConstant | keywordConstant | varName | varName '[' expression ']' | subroutineCall | '(' expression ')' | unaryOp term
        term_el = ET.SubElement(parent_el, "term")
        current_token = self.tokenizer.current_token
        self.tokenizer.advance() # now points to 1 ahead

        token_type = self.tokenizer.token_type()
        if token_type == TokenType.INT_CONST: # integerConstant
            ET.SubElement(term_el, "integerConstant").text = current_token
        elif token_type == TokenType.STRING_CONST: # stringConstant
            ET.SubElement(term_el, "stringConstant").text = current_token
        elif token_type == TokenType.KEYWORD: # keywordConstant
            ET.SubElement(term_el, "keywordConstant").text = current_token
        elif current_token == "-" or current_token == "~": # unaryOp term
            unary_op_term_el = ET.SubElement(term_el, "symbol").text = self.tokenizer.current_token
            self.compile_term(unary_op_term_el)
        elif current_token == "(": # '(' expression ')'
            ET.SubElement(term_el, "symbol").text = current_token
            self.compile_expression(term_el)
        elif self.tokenizer.current_token == "[": # varName '[' expression ']'
            ET.SubElement(term_el, "identifier").text = current_token
            ET.SubElement(term_el, "symbol").text = self.tokenizer.current_token
            self.tokenizer.advance()
            self.compile_expression(term_el)
        elif self.tokenizer.current_token == "(":  # subroutineCall
            ET.SubElement(term_el, "identifier").text = current_token #subroutineName
            ET.SubElement(term_el, "symbol").text = self.tokenizer.current_token  # (
            self.compile_expression_list(term_el)
            ET.SubElement(term_el, "symbol").text = self.tokenizer.current_token  # )
        elif self.tokenizer.current_token == ".": # subroutineCall
            ET.SubElement(term_el, "identifier").text = current_token
            ET.SubElement(term_el, "symbol").text = self.tokenizer.current_token # .
            self.tokenizer.advance()
            ET.SubElement(term_el, "identifier").text = self.tokenizer.current_token
            self.tokenizer.advance()
            ET.SubElement(term_el, "symbol").text = self.tokenizer.current_token # (
            self.compile_expression_list(term_el)
            ET.SubElement(term_el, "symbol").text = self.tokenizer.current_token # )
        else: # varName
            ET.SubElement(term_el, "identifier").text = current_token
            return

    def compile_expression_list(self, parent_el):
        ET.SubElement(parent_el, "expressionList")
        self.compile_expression()