from pathlib import Path
import xml.etree.ElementTree as ET

from src.Enums import KeyWord, TokenType, Command, Segment
from src.Helpers import force_empty_newlines
from src.JackTokenizer import JackTokenizer
from src.SymbolTable import SymbolTable
from Enums import Kind
from src.VMWriter import VMWriter, get_arithmetic_command


class CompilationEngine:
    def __init__(self, path: Path):
        self.vm_writer = VMWriter(path)
        self.label_count = 0

        p = Path(path).with_suffix(".xml")
        self.out_file = open(p, "w")
        self.tokenizer = JackTokenizer(path)
        self.tree = ET.ElementTree(ET.Element("tokens"))
        self.class_symbol_table = SymbolTable()
        self.subroutine_symbol_table = SymbolTable()
        self.current_class_name = ""
        self.current_subroutine_name = ""
        self.is_compiling_constructor = False

        if self.tokenizer.has_more_tokens():
            self.tokenizer.advance()
            self.compile_class()
            ET.indent(self.tree, space="  ")
            force_empty_newlines(self.tree.getroot())
            self.tree.write(p, short_empty_elements=False)

    def compile_class(self):
        # 'class' className '{' classVarDec* subroutineDec* '}'
        class_el = ET.SubElement(self.tree.getroot(), "class")

        # class keyword
        ET.SubElement(class_el, "keyword").text = f" {self.tokenizer.current_token} "
        self.tokenizer.advance()

        # identifier - className
        self.current_class_name = self.tokenizer.current_token
        ET.SubElement(class_el, "identifier").text = f" {self.tokenizer.current_token} "
        self.tokenizer.advance()

        # symbol - '{'
        ET.SubElement(class_el, "symbol").text = f" {self.tokenizer.current_token} "
        self.tokenizer.advance()

        self.compile_class_var_dec(class_el)
        self.compile_subroutine(class_el)

        # symbol - '}'
        ET.SubElement(class_el, "symbol").text = f" {self.tokenizer.current_token} "

    def compile_class_var_dec(self, parent_el):
        # ('static' | 'field') type varName (',' varName)* ';'
        keyword = self.tokenizer.key_word()
        if keyword == KeyWord.STATIC or keyword == KeyWord.FIELD:
            class_var_dec_el = ET.SubElement(parent_el, "classVarDec")
        else:
            return

        kind = Kind.STATIC if keyword == KeyWord.STATIC else Kind.FIELD
        ET.SubElement(class_var_dec_el, "keyword").text = " static " if keyword == KeyWord.STATIC else " field "
        self.tokenizer.advance()

        # type - int (keyword), char (keyword), boolean (keyword), or className (identifier)
        type_of = self.tokenizer.current_token
        if self.tokenizer.token_type() == TokenType.IDENTIFIER:
            ET.SubElement(class_var_dec_el, "identifier").text = f" {self.tokenizer.current_token} "
        else:
            ET.SubElement(class_var_dec_el, "keyword").text = f" {self.tokenizer.current_token} "
        self.tokenizer.advance()

        # identifier - varName
        self.class_symbol_table.define(self.tokenizer.current_token, type_of, kind)
        ET.SubElement(class_var_dec_el, "identifier").text = f" {self.tokenizer.current_token} "
        self.tokenizer.advance()

        while self.tokenizer.current_token != ";":
            # symbol - ','
            ET.SubElement(class_var_dec_el, "symbol").text = f" {self.tokenizer.current_token} "
            self.tokenizer.advance()
            # identifier - varName
            self.class_symbol_table.define(self.tokenizer.current_token, type_of, kind)
            ET.SubElement(class_var_dec_el, "identifier").text = f" {self.tokenizer.current_token} "
            self.tokenizer.advance()

        # symbol - ';'
        ET.SubElement(class_var_dec_el, "symbol").text = f" {self.tokenizer.current_token} "
        self.tokenizer.advance()

        self.compile_class_var_dec(parent_el)

    def compile_subroutine(self, parent_el):
        # ('constructor' | 'function' | 'method') ('void' | type) subroutineName '(' parameterList ')' subroutineBody
        self.subroutine_symbol_table.start_subroutine()

        token_type = self.tokenizer.token_type()
        if token_type == TokenType.KEYWORD:
            class_var_dec_el = ET.SubElement(parent_el, "subroutineDec")
        else:
            return

        # keyword - constructor | function | method
        is_constructor = False
        if self.tokenizer.key_word() == KeyWord.METHOD:
            self.subroutine_symbol_table.define("this", self.current_class_name, Kind.ARG)

        if self.tokenizer.key_word() == KeyWord.CONSTRUCTOR:
            self.is_compiling_constructor = True
        else:
            self.is_compiling_constructor = False

        ET.SubElement(class_var_dec_el, "keyword").text = f" {self.tokenizer.current_token} "
        self.tokenizer.advance()

        # identifier | keyword - void (keyword) | type -> int (keyword), char (keyword), boolean (keyword), or className (identifier)
        if self.tokenizer.token_type() == TokenType.IDENTIFIER:
            ET.SubElement(class_var_dec_el, "identifier").text = f" {self.tokenizer.current_token} "
        else:
            ET.SubElement(class_var_dec_el, "keyword").text = f" {self.tokenizer.current_token} "
        self.tokenizer.advance()

        # identifier - subroutineName
        self.current_subroutine_name = self.tokenizer.current_token

        ET.SubElement(class_var_dec_el, "identifier").text = f" {self.tokenizer.current_token} "
        self.tokenizer.advance()

        # symbol - '('
        ET.SubElement(class_var_dec_el, "symbol").text = f" {self.tokenizer.current_token} "
        self.tokenizer.advance()

        # parameterList
        param_list_el = ET.SubElement(class_var_dec_el, "parameterList")
        self.compile_parameter_list(param_list_el)

        # symbol - ')'
        ET.SubElement(class_var_dec_el, "symbol").text = f" {self.tokenizer.current_token} "
        self.tokenizer.advance()

        # subroutineBody
        self.compile_subroutine_body(class_var_dec_el)

        self.compile_subroutine(parent_el)

    def compile_parameter_list(self, parent_el):
        if self.tokenizer.current_token == ")":
            return

        # type - int (keyword), char (keyword), boolean (keyword), or className (identifier)
        type_of = self.tokenizer.current_token

        if self.tokenizer.token_type() == TokenType.IDENTIFIER:
            ET.SubElement(parent_el, "identifier").text = f" {self.tokenizer.current_token} "
        else:
            ET.SubElement(parent_el, "keyword").text = f" {self.tokenizer.current_token} "

        self.tokenizer.advance()

        # identifier - varName
        self.subroutine_symbol_table.define(self.tokenizer.current_token, type_of, Kind.ARG)

        ET.SubElement(parent_el, "identifier").text = f" {self.tokenizer.current_token} "
        self.tokenizer.advance()

        # symbol - ','
        if self.tokenizer.current_token == ",":
            ET.SubElement(parent_el, "symbol").text = f" {self.tokenizer.current_token} "
            self.tokenizer.advance()

        self.compile_parameter_list(parent_el)

    def compile_subroutine_body(self, parent_el):
        # '{' varDec* statements '}'
        subroutine_body_el = ET.SubElement(parent_el, "subroutineBody")

        # symbol - '{'
        ET.SubElement(subroutine_body_el, "symbol").text = f" {self.tokenizer.current_token} "
        self.tokenizer.advance()

        # varDec*
        self.compile_var_dec(subroutine_body_el)

        self.vm_writer.write_function(f"{self.current_class_name}.{self.current_subroutine_name}",
                                      self.subroutine_symbol_table.var_count(Kind.VAR), 0)

        if self.is_compiling_constructor:
            self.vm_writer.write_push(Segment.CONST, self.class_symbol_table.var_count(Kind.FIELD), 1)
            self.vm_writer.write_call("Memory.alloc", 1, 1)
            self.vm_writer.write_pop(Segment.POINTER, 0, 1)

        # statements
        statements_el = ET.SubElement(subroutine_body_el, "statements")
        self.compile_statements(statements_el)

        # symbol - '}'
        ET.SubElement(subroutine_body_el, "symbol").text = f" {self.tokenizer.current_token} "
        self.tokenizer.advance()

    def compile_var_dec(self, parent_el):
        # 'var' type varName (',' varName)* ';'
        if self.tokenizer.key_word() != KeyWord.VAR:
            return

        var_dec_el = ET.SubElement(parent_el, "varDec")

        ET.SubElement(var_dec_el, "keyword").text = f" {self.tokenizer.current_token} "
        self.tokenizer.advance()

        # type - int (keyword), char (keyword), boolean (keyword), or className (identifier)
        type_of = self.tokenizer.current_token

        if self.tokenizer.token_type() == TokenType.IDENTIFIER:
            ET.SubElement(var_dec_el, "identifier").text = f" {self.tokenizer.current_token} "
        else:
            ET.SubElement(var_dec_el, "keyword").text = f" {self.tokenizer.current_token} "
        self.tokenizer.advance()

        # identifier - varName
        self.subroutine_symbol_table.define(self.tokenizer.current_token, type_of, Kind.VAR)

        ET.SubElement(var_dec_el, "identifier").text = f" {self.tokenizer.current_token} "
        self.tokenizer.advance()

        # (',' varName)*
        while self.tokenizer.current_token != ";":
            # symbol - ','
            ET.SubElement(var_dec_el, "symbol").text = f" {self.tokenizer.current_token} "
            self.tokenizer.advance()
            # identifier - varName
            self.subroutine_symbol_table.define(self.tokenizer.current_token, type_of, Kind.VAR)
            ET.SubElement(var_dec_el, "identifier").text = f" {self.tokenizer.current_token} "
            self.tokenizer.advance()

        # symbol ';'
        ET.SubElement(var_dec_el, "symbol").text = f" {self.tokenizer.current_token} "
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
            if self.is_compiling_constructor:
                self.vm_writer.write_push(Segment.POINTER, 0, 1)
            self.compile_return(parent_el)
            self.compile_statements(parent_el)
        else:
            return

    def compile_let(self, parent_el):
        # 'let' varName ('[' expression ']')? '=' expression ';'
        let_statement_el = ET.SubElement(parent_el, "letStatement")

        # keyword - let
        ET.SubElement(let_statement_el, "keyword").text = f" {self.tokenizer.current_token} "
        self.tokenizer.advance()

        # identifier - varName
        match = self.subroutine_symbol_table.table.get(self.tokenizer.current_token)
        if match is None:
            kind = self.class_symbol_table.kind_of(self.tokenizer.current_token)
            index = self.class_symbol_table.index_of(self.tokenizer.current_token)
        else:
            kind = self.subroutine_symbol_table.kind_of(self.tokenizer.current_token)
            index = self.subroutine_symbol_table.index_of(self.tokenizer.current_token)

        if kind == Kind.STATIC:
            segment = Segment.STATIC
        elif kind == Kind.FIELD:
            segment = Segment.THIS
        elif kind == Kind.ARG:
            segment = Segment.ARG
        else:
            segment = Segment.LOCAL

        ET.SubElement(let_statement_el, "identifier").text = f" {self.tokenizer.current_token} "
        self.tokenizer.advance()

        if self.tokenizer.current_token == "[":
            ET.SubElement(let_statement_el, "symbol").text = f" {self.tokenizer.current_token} " # '['
            self.tokenizer.advance()

            self.compile_expression(let_statement_el, False)

            ET.SubElement(let_statement_el, "symbol").text = f" {self.tokenizer.current_token} " # ']'
            self.tokenizer.advance()

        ET.SubElement(let_statement_el, "symbol").text = f" {self.tokenizer.current_token} "  # '='
        self.tokenizer.advance()

        self.compile_expression(let_statement_el, False)

        self.vm_writer.write_pop(segment, index, 1)

        ET.SubElement(let_statement_el, "symbol").text = f" {self.tokenizer.current_token} "  # ';'
        self.tokenizer.advance()

    def compile_if(self, parent_el):
        # 'if' '(' expression ')' '{' statements '}' ('else' '{' statements '}')?
        if_statement_el = ET.SubElement(parent_el, "ifStatement")

        ET.SubElement(if_statement_el, "keyword").text = f" {self.tokenizer.current_token} "  # 'if'
        self.tokenizer.advance()

        ET.SubElement(if_statement_el, "symbol").text = f" {self.tokenizer.current_token} "  # '('
        self.tokenizer.advance()

        self.compile_expression(if_statement_el, False)

        self.vm_writer.write_arithmetic(Command.NOT, 1)
        self.vm_writer.write_if(f"L{self.label_count}", 1) # if-goto L0

        ET.SubElement(if_statement_el, "symbol").text = f" {self.tokenizer.current_token} "  # ')'
        self.tokenizer.advance()

        ET.SubElement(if_statement_el, "symbol").text = f" {self.tokenizer.current_token} "  # '{'
        self.tokenizer.advance()

        statements_el = ET.SubElement(if_statement_el, "statements")
        self.compile_statements(statements_el)

        self.vm_writer.write_go_to(f"L{self.label_count + 1}", 1) # goto L1
        self.vm_writer.write_label(f"L{self.label_count}", 1) # label L0

        ET.SubElement(if_statement_el, "symbol").text = f" {self.tokenizer.current_token} "  # '}'
        self.tokenizer.advance()

        if self.tokenizer.key_word() == KeyWord.ELSE:
            ET.SubElement(if_statement_el, "keyword").text = f" {self.tokenizer.current_token} "  # 'else'
            self.tokenizer.advance()

            ET.SubElement(if_statement_el, "symbol").text = f" {self.tokenizer.current_token} "  # '{'
            self.tokenizer.advance()

            statements_el = ET.SubElement(if_statement_el, "statements")
            self.compile_statements(statements_el)

            ET.SubElement(if_statement_el, "symbol").text = f" {self.tokenizer.current_token} "  # '}'
            self.tokenizer.advance()

        self.vm_writer.write_label(f"L{self.label_count + 1}", 1)  # label L1
        self.label_count = self.label_count + 2

    def compile_while(self, parent_el):
        # 'while' '(' expression ')' '{' statements '}'
        self.vm_writer.write_label(f"L{self.label_count}", 1) # label L0

        while_statement_el = ET.SubElement(parent_el, "whileStatement")

        ET.SubElement(while_statement_el, "keyword").text = f" {self.tokenizer.current_token} "  # 'while'
        self.tokenizer.advance()

        ET.SubElement(while_statement_el, "symbol").text = f" {self.tokenizer.current_token} "  # '('
        self.tokenizer.advance()

        self.compile_expression(while_statement_el, False)

        self.vm_writer.write_arithmetic(Command.NOT, 1)
        self.vm_writer.write_if(f"L{self.label_count + 1}", 1) # if-goto L1

        ET.SubElement(while_statement_el, "symbol").text = f" {self.tokenizer.current_token} "  # ')'
        self.tokenizer.advance()

        ET.SubElement(while_statement_el, "symbol").text = f" {self.tokenizer.current_token} "  # '{'
        self.tokenizer.advance()

        statements_el = ET.SubElement(while_statement_el, "statements")
        self.compile_statements(statements_el)

        self.vm_writer.write_go_to(f"L{self.label_count + 1}", 1) # goto L0
        self.vm_writer.write_label(f"L{self.label_count}", 1)
        self.label_count = self.label_count + 2

        ET.SubElement(while_statement_el, "symbol").text = f" {self.tokenizer.current_token} "  # '}'
        self.tokenizer.advance()

    def compile_do(self, parent_el):
        # 'do' routineCall ';'
        do_statement_el = ET.SubElement(parent_el, "doStatement")

        ET.SubElement(do_statement_el, "keyword").text = f" {self.tokenizer.current_token} "  # 'do'
        self.tokenizer.advance()

        self.compile_expression(do_statement_el, True)

        ET.SubElement(do_statement_el, "symbol").text = f" {self.tokenizer.current_token} "  # ';'
        self.tokenizer.advance()

        self.vm_writer.write_pop(Segment.TEMP, 0, 1)

    def compile_return(self, parent_el):
        # 'return' expression? ';'
        return_statement_el = ET.SubElement(parent_el, "returnStatement")

        ET.SubElement(return_statement_el, "keyword").text = f" {self.tokenizer.current_token} "  # 'return'
        self.tokenizer.advance()

        if self.tokenizer.current_token != ";":
            self.compile_expression(return_statement_el, False)

        ET.SubElement(return_statement_el, "symbol").text = f" {self.tokenizer.current_token} "  # ';'
        self.tokenizer.advance()

        self.vm_writer.write_return(1)

    # defer
    def compile_expression(self, parent_el, is_do):
        # term (op term)*
        operators = ["+", "-", "*", "/", "&", "|", "<", ">", "="]

        el = ET.SubElement(parent_el, "expression") if not is_do else parent_el

        self.compile_term(el, is_do)

        while self.tokenizer.current_token in operators:
            is_mult = self.tokenizer.current_token == "*"
            command = get_arithmetic_command(self.tokenizer.current_token)

            ET.SubElement(el, "symbol").text = f" {self.tokenizer.current_token} "  # op
            self.tokenizer.advance()

            self.compile_term(el, is_do)

            if command is not None:
                self.vm_writer.write_arithmetic(command, 1)
            else:
                if is_mult:
                    self.vm_writer.write_call("Math.multiply", 2, 1)
                else:
                    self.vm_writer.write_call("Math.divide", 2, 1)

    def compile_term(self, parent_el, is_do):
        # integerConstant | stringConstant | keywordConstant | varName | varName '[' expression ']' | subroutineCall | '(' expression ')' | unaryOp term
        el = ET.SubElement(parent_el, "term") if not is_do else parent_el

        if self.tokenizer.token_type() == TokenType.IDENTIFIER:
            current_token = self.tokenizer.current_token
            self.tokenizer.advance() # now points to 1 ahead

            if self.tokenizer.current_token == "(" or self.tokenizer.current_token == ".":  # subroutineCall
                function_name = current_token
                ET.SubElement(el, "identifier").text = f" {current_token} "

                if self.tokenizer.current_token == ".":
                    ET.SubElement(el, "symbol").text = f" {self.tokenizer.current_token} "  # '.'
                    self.tokenizer.advance()
                    function_name += "." + self.tokenizer.current_token
                    ET.SubElement(el, "identifier").text = f" {self.tokenizer.current_token} "
                    self.tokenizer.advance()

                ET.SubElement(el, "symbol").text = f" {self.tokenizer.current_token} "  # '('
                self.tokenizer.advance()

                n_args = self.compile_expression_list(el)

                self.vm_writer.write_call(function_name, n_args, 1)
                ET.SubElement(el, "symbol").text = f" {self.tokenizer.current_token} "  # ')'
                self.tokenizer.advance()

                return
            elif self.tokenizer.current_token == "[": # varName '[' expression ']'
                ET.SubElement(el, "identifier").text = f" {current_token} "
                ET.SubElement(el, "symbol").text = f" {self.tokenizer.current_token} "
                self.tokenizer.advance()

                self.compile_expression(el, is_do)

                ET.SubElement(el, "symbol").text = f" {self.tokenizer.current_token} "  # ']'
                self.tokenizer.advance()

                return
            else:  # varName
                match = self.subroutine_symbol_table.table.get(current_token)
                if match is None:
                    kind = self.class_symbol_table.kind_of(current_token)
                    index = self.class_symbol_table.index_of(current_token)
                else:
                    kind = self.subroutine_symbol_table.kind_of(current_token)
                    index = self.subroutine_symbol_table.index_of(current_token)

                if kind == Kind.STATIC:
                    segment = Segment.STATIC
                elif kind == Kind.FIELD:
                    segment = Segment.THIS
                elif kind == Kind.ARG:
                    segment = Segment.ARG
                else:
                    segment = Segment.LOCAL

                self.vm_writer.write_push(segment, index, 1)
                ET.SubElement(el, "identifier").text = f" {current_token} "
                return

        token_type = self.tokenizer.token_type()
        if token_type == TokenType.INT_CONST: # integerConstant
            ET.SubElement(el, "integerConstant").text = f" {self.tokenizer.current_token} "
            self.vm_writer.write_push(Segment.CONST, int(self.tokenizer.current_token), 1)
            self.tokenizer.advance()
        elif token_type == TokenType.STRING_CONST: # stringConstant
            ET.SubElement(el, "stringConstant").text = f" {self.tokenizer.current_token[1:-1]} "
            self.tokenizer.advance()
        elif token_type == TokenType.KEYWORD: # keywordConstant
            ET.SubElement(el, "keyword").text = f" {self.tokenizer.current_token} "
            self.tokenizer.advance()
        elif self.tokenizer.current_token == "-" or self.tokenizer.current_token == "~": # unaryOp term
            command = Command.NEG if self.tokenizer.current_token == "-" else Command.NOT
            ET.SubElement(el, "symbol").text = f" {self.tokenizer.current_token} "
            self.tokenizer.advance()

            self.compile_term(el, is_do)
            self.vm_writer.write_arithmetic(command, 1)
        elif self.tokenizer.current_token == "(": # '(' expression ')'
            ET.SubElement(el, "symbol").text = f" {self.tokenizer.current_token} "
            self.tokenizer.advance()

            self.compile_expression(el, is_do)

            ET.SubElement(el, "symbol").text = f" {self.tokenizer.current_token} "  # ')'
            self.tokenizer.advance()

    def compile_expression_list(self, parent_el):
        # (expression (',' expression)*)?
        expression_list_el = ET.SubElement(parent_el, "expressionList")
        n_args = 0

        if self.tokenizer.current_token == ")":
            return n_args

        n_args = n_args + 1
        self.compile_expression(expression_list_el, False)

        while self.tokenizer.current_token == ",":
            # symbol - ','
            ET.SubElement(expression_list_el, "symbol").text = f" {self.tokenizer.current_token} "
            self.tokenizer.advance()

            n_args = n_args + 1
            self.compile_expression(expression_list_el, False)

        return n_args

    def close(self):
        self.vm_writer.close()