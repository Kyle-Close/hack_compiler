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

        # symbol - '}'
        ET.SubElement(class_el, "symbol").text = self.tokenizer.current_token

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
        self.compile_parameter_list(class_var_dec_el)

        # symbol - ')'
        ET.SubElement(class_var_dec_el, "symbol").text = self.tokenizer.current_token
        self.tokenizer.advance()

        # subroutineBody
        self.compile_subroutine_body(class_var_dec_el)

        self.compile_subroutine(parent_el)

    def compile_parameter_list(self, parent_el):
        param_list_el = ET.SubElement(parent_el, "parameterList")

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

        self.compile_parameter_list(parent_el)

    def compile_subroutine_body(self, parent_el):
        # '{' varDec* statements '}'
        subroutine_body_el = ET.SubElement(parent_el, "subroutineBody")

        # symbol - '{'
        ET.SubElement(subroutine_body_el, "symbol").text = self.tokenizer.current_token
        self.tokenizer.advance()

        # varDec*
        self.compile_var_dec(subroutine_body_el)

        # statements
        statements_el = ET.SubElement(subroutine_body_el, "statements")
        self.compile_statements(statements_el)

        # symbol - '}'
        ET.SubElement(subroutine_body_el, "symbol").text = self.tokenizer.current_token
        self.tokenizer.advance()

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

        keyword = self.tokenizer.key_word()
        if keyword == KeyWord.LET:
            self.compile_let(parent_el)
            self.compile_statements(parent_el)
        elif keyword == KeyWord.IF:
            self.compile_if(parent_el)
            self.compile_statements(parent_el)
        elif keyword == KeyWord.WHILE:
            self.compile_while(parent_el)
            self.compile_statements(parent_el)
        elif keyword == KeyWord.DO:
            self.compile_do(parent_el)
            self.compile_statements(parent_el)
        elif keyword == KeyWord.RETURN:
            self.compile_return(parent_el)
            self.compile_statements(parent_el)
        else:
            return

    def compile_let(self, parent_el):
        # 'let' varName ('[' expression ']')? '=' expression ';'
        let_statement_el = ET.SubElement(parent_el, "letStatement")

        # keyword - let
        ET.SubElement(let_statement_el, "keyword").text = self.tokenizer.current_token
        self.tokenizer.advance()

        # identifier - varName
        ET.SubElement(let_statement_el, "identifier").text = self.tokenizer.current_token
        self.tokenizer.advance()

        if self.tokenizer.current_token == "[":
            ET.SubElement(let_statement_el, "symbol").text = self.tokenizer.current_token # '['
            self.tokenizer.advance()

            self.compile_expression(let_statement_el)

            ET.SubElement(let_statement_el, "symbol").text = self.tokenizer.current_token # ']'
            self.tokenizer.advance()

        ET.SubElement(let_statement_el, "symbol").text = self.tokenizer.current_token  # '='
        self.tokenizer.advance()

        self.compile_expression(let_statement_el)

        ET.SubElement(let_statement_el, "symbol").text = self.tokenizer.current_token  # ';'
        self.tokenizer.advance()

    def compile_if(self, parent_el):
        # 'if' '(' expression ')' '{' statements '}' ('else' '{' statements '}')?
        if_statement_el = ET.SubElement(parent_el, "ifStatement")

        ET.SubElement(if_statement_el, "keyword").text = self.tokenizer.current_token  # 'if'
        self.tokenizer.advance()

        ET.SubElement(if_statement_el, "symbol").text = self.tokenizer.current_token  # '('
        self.tokenizer.advance()

        self.compile_expression(if_statement_el)

        ET.SubElement(if_statement_el, "symbol").text = self.tokenizer.current_token  # ')'
        self.tokenizer.advance()

        ET.SubElement(if_statement_el, "symbol").text = self.tokenizer.current_token  # '{'
        self.tokenizer.advance()

        self.compile_statements(if_statement_el)

        ET.SubElement(if_statement_el, "symbol").text = self.tokenizer.current_token  # '}'
        self.tokenizer.advance()

        if self.tokenizer.key_word() == KeyWord.ELSE:
            ET.SubElement(if_statement_el, "keyword").text = self.tokenizer.current_token  # 'else'
            self.tokenizer.advance()

            ET.SubElement(if_statement_el, "symbol").text = self.tokenizer.current_token  # '{'
            self.tokenizer.advance()

            self.compile_statements(if_statement_el)

            ET.SubElement(if_statement_el, "symbol").text = self.tokenizer.current_token  # '}'
            self.tokenizer.advance()

    def compile_while(self, parent_el):
        # 'while' '(' expression ')' '{' statements '}'
        while_statement_el = ET.SubElement(parent_el, "whileStatement")

        ET.SubElement(while_statement_el, "keyword").text = self.tokenizer.current_token  # 'while'
        self.tokenizer.advance()

        ET.SubElement(while_statement_el, "symbol").text = self.tokenizer.current_token  # '('
        self.tokenizer.advance()

        self.compile_expression(while_statement_el)

        ET.SubElement(while_statement_el, "symbol").text = self.tokenizer.current_token  # ')'
        self.tokenizer.advance()

        ET.SubElement(while_statement_el, "symbol").text = self.tokenizer.current_token  # '{'
        self.tokenizer.advance()

        self.compile_statements(while_statement_el)

        ET.SubElement(while_statement_el, "symbol").text = self.tokenizer.current_token  # '}'
        self.tokenizer.advance()

    def compile_do(self, parent_el):
        # 'do' routineCall
        do_statement_el = ET.SubElement(parent_el, "doStatement")

        ET.SubElement(do_statement_el, "keyword").text = self.tokenizer.current_token  # 'do'
        self.tokenizer.advance()

        self.compile_term(do_statement_el)

    def compile_return(self, parent_el):
        # 'return' expression? ';'
        return_statement_el = ET.SubElement(parent_el, "returnStatement")

        ET.SubElement(return_statement_el, "keyword").text = self.tokenizer.current_token  # 'return'
        self.tokenizer.advance()

        if self.tokenizer.current_token != ";":
            self.compile_expression(return_statement_el)

        ET.SubElement(return_statement_el, "symbol").text = self.tokenizer.current_token  # ';'
        self.tokenizer.advance()

    # defer
    def compile_expression(self, parent_el):
        # term (op term)*
        operators = ["+", "-", "*", "/", "&", "|", "<", ">", "="]
        expression_el = ET.SubElement(parent_el, "expression")

        self.compile_term(expression_el)

        while self.tokenizer.current_token in operators:
            ET.SubElement(parent_el, "symbol").text = self.tokenizer.current_token  # op
            self.tokenizer.advance()
            self.compile_term(expression_el)

    def compile_term(self, parent_el):
        # integerConstant | stringConstant | keywordConstant | varName | varName '[' expression ']' | subroutineCall | '(' expression ')' | unaryOp term
        if self.tokenizer.token_type() == TokenType.IDENTIFIER:
            current_token = self.tokenizer.current_token
            self.tokenizer.advance() # now points to 1 ahead

            if self.tokenizer.current_token == "(":  # subroutineCall
                ET.SubElement(parent_el, "identifier").text = current_token #subroutineName
                ET.SubElement(parent_el, "symbol").text = self.tokenizer.current_token  # '('
                self.compile_expression_list(parent_el)
                ET.SubElement(parent_el, "symbol").text = self.tokenizer.current_token  # ')'
                self.tokenizer.advance()
                ET.SubElement(parent_el, "symbol").text = self.tokenizer.current_token  # ';'
                self.tokenizer.advance()
                return
            elif self.tokenizer.current_token == ".": # subroutineCall
                ET.SubElement(parent_el, "identifier").text = current_token
                ET.SubElement(parent_el, "symbol").text = self.tokenizer.current_token # '.'
                self.tokenizer.advance()
                ET.SubElement(parent_el, "identifier").text = self.tokenizer.current_token
                self.tokenizer.advance()
                ET.SubElement(parent_el, "symbol").text = self.tokenizer.current_token # '('
                self.tokenizer.advance()
                self.compile_expression_list(parent_el)
                ET.SubElement(parent_el, "symbol").text = self.tokenizer.current_token # ')'
                self.tokenizer.advance()
                ET.SubElement(parent_el, "symbol").text = self.tokenizer.current_token  # ';'
                self.tokenizer.advance()
                return
            elif self.tokenizer.current_token == "[": # varName '[' expression ']'
                ET.SubElement(parent_el, "identifier").text = current_token
                ET.SubElement(parent_el, "symbol").text = self.tokenizer.current_token
                self.tokenizer.advance()
                self.compile_expression(parent_el)
                return

        term_el = ET.SubElement(parent_el, "term")

        token_type = self.tokenizer.token_type()
        if token_type == TokenType.INT_CONST: # integerConstant
            ET.SubElement(term_el, "integerConstant").text = self.tokenizer.current_token
        elif token_type == TokenType.STRING_CONST: # stringConstant
            ET.SubElement(term_el, "stringConstant").text = self.tokenizer.current_token
        elif token_type == TokenType.KEYWORD: # keywordConstant
            ET.SubElement(term_el, "keywordConstant").text = self.tokenizer.current_token
        elif self.tokenizer.current_token == "-" or self.tokenizer.current_token == "~": # unaryOp term
            unary_op_term_el = ET.SubElement(term_el, "symbol").text = self.tokenizer.current_token
            self.compile_term(unary_op_term_el)
        elif self.tokenizer.current_token == "(": # '(' expression ')'
            ET.SubElement(term_el, "symbol").text = self.tokenizer.current_token
            self.compile_expression(term_el)
        else: # varName
            ET.SubElement(term_el, "identifier").text = self.tokenizer.current_token
            return

    def compile_expression_list(self, parent_el):
        # (expression (',' expression)*)?
        expression_list_el = ET.SubElement(parent_el, "expressionList")

        if self.tokenizer.current_token == ")":
            return

        self.compile_expression(expression_list_el)

        while self.tokenizer.current_token == ",":
            # symbol - ','
            ET.SubElement(expression_list_el, "symbol").text = self.tokenizer.current_token
            self.tokenizer.advance()

            self.compile_expression(expression_list_el)