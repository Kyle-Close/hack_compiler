from pathlib import Path

from src.Enums import KeyWord, TokenType, Command, Segment
from src.Helpers import convert_kind_to_segment
from src.JackTokenizer import JackTokenizer
from src.SymbolTable import SymbolTable
from Enums import Kind
from src.VMWriter import VMWriter, get_arithmetic_command


class CompilationEngine:
    def __init__(self, path: Path):
        self.tokenizer = JackTokenizer(path)
        self.vm_writer = VMWriter(path)
        self.class_symbol_table = SymbolTable()
        self.subroutine_symbol_table = SymbolTable()
        self.label_count = 0

        self.current_class_name = ""
        self.current_subroutine_name = ""
        self.is_compiling_constructor = False
        self.is_compiling_method = False
        self.is_compiling_void = False

        if self.tokenizer.has_more_tokens():
            self.tokenizer.advance()
            self.compile_class()

    def compile_class(self):
        # 'class' className '{' classVarDec* subroutineDec* '}'

        # class keyword
        self.tokenizer.advance()

        # identifier - className
        self.current_class_name = self.tokenizer.current_token
        self.tokenizer.advance()

        # symbol - '{'
        self.tokenizer.advance()

        self.compile_class_var_dec()
        self.compile_subroutine()

    def compile_class_var_dec(self):
        # ('static' | 'field') type varName (',' varName)* ';'
        while True:
            keyword = self.tokenizer.key_word()
            if keyword != KeyWord.STATIC and keyword != KeyWord.FIELD:
                break

            kind = Kind.STATIC if keyword == KeyWord.STATIC else Kind.FIELD
            self.tokenizer.advance()

            # type - int (keyword), char (keyword), boolean (keyword), or className (identifier)
            type_of = self.tokenizer.current_token
            self.tokenizer.advance()

            # identifier - varName
            self.class_symbol_table.define(self.tokenizer.current_token, type_of, kind)
            self.tokenizer.advance()

            while self.tokenizer.current_token != ";":
                # symbol - ','
                self.tokenizer.advance()
                # identifier - varName
                self.class_symbol_table.define(self.tokenizer.current_token, type_of, kind)
                self.tokenizer.advance()

            # symbol - ';'
            self.tokenizer.advance()

    def compile_subroutine(self):
        # ('constructor' | 'function' | 'method') ('void' | type) subroutineName '(' parameterList ')' subroutineBody
        self.subroutine_symbol_table.start_subroutine()

        token_type = self.tokenizer.token_type()
        if token_type != TokenType.KEYWORD:
            return

        # keyword - constructor | function | method
        if self.tokenizer.key_word() == KeyWord.METHOD:
            self.is_compiling_method = True
            self.subroutine_symbol_table.define("this", self.current_class_name, Kind.ARG)
        else:
            self.is_compiling_method = False

        if self.tokenizer.key_word() == KeyWord.CONSTRUCTOR:
            self.is_compiling_constructor = True
        else:
            self.is_compiling_constructor = False

        self.tokenizer.advance()

        # identifier | keyword - void (keyword) | type -> int (keyword), char (keyword), boolean (keyword), or className (identifier)
        if self.tokenizer.token_type() == TokenType.IDENTIFIER:
            self.is_compiling_void = False
        else:
            if self.tokenizer.key_word() == KeyWord.VOID:
                self.is_compiling_void = True
            else:
                self.is_compiling_void = False
        self.tokenizer.advance()

        # identifier - subroutineName
        self.current_subroutine_name = self.tokenizer.current_token

        self.tokenizer.advance()

        # symbol - '('
        self.tokenizer.advance()

        # parameterList
        self.compile_parameter_list()

        # symbol - ')'
        self.tokenizer.advance()

        # subroutineBody
        self.compile_subroutine_body()

        self.compile_subroutine()

    def compile_parameter_list(self):
        if self.tokenizer.current_token == ")":
            return

        # type - int (keyword), char (keyword), boolean (keyword), or className (identifier)
        type_of = self.tokenizer.current_token
        self.tokenizer.advance()

        # identifier - varName
        self.subroutine_symbol_table.define(self.tokenizer.current_token, type_of, Kind.ARG)
        self.tokenizer.advance()

        while self.tokenizer.current_token == ",":
            # symbol - ','
            self.tokenizer.advance()
            # type
            type_of = self.tokenizer.current_token
            self.tokenizer.advance()
            # identifier - varName
            self.subroutine_symbol_table.define(self.tokenizer.current_token, type_of, Kind.ARG)
            self.tokenizer.advance()

    def compile_subroutine_body(self):
        # '{' varDec* statements '}'

        # symbol - '{'
        self.tokenizer.advance()

        # varDec*
        self.compile_var_dec()

        self.vm_writer.write_function(f"{self.current_class_name}.{self.current_subroutine_name}",
                                      self.subroutine_symbol_table.var_count(Kind.VAR), 0)

        if self.is_compiling_constructor:
            self.vm_writer.write_push(Segment.CONST, self.class_symbol_table.var_count(Kind.FIELD), 1)
            self.vm_writer.write_call("Memory.alloc", 1, 1)
            self.vm_writer.write_pop(Segment.POINTER, 0, 1)
        elif self.is_compiling_method:
            self.vm_writer.write_push(Segment.ARG, 0, 1)
            self.vm_writer.write_pop(Segment.POINTER, 0, 1)

        # statements
        self.compile_statements()

        # symbol - '}'
        self.tokenizer.advance()

    def compile_var_dec(self):
        # 'var' type varName (',' varName)* ';'
        while self.tokenizer.key_word() == KeyWord.VAR:
            # var
            self.tokenizer.advance()

            # type - int (keyword), char (keyword), boolean (keyword), or className (identifier)
            type_of = self.tokenizer.current_token
            self.tokenizer.advance()

            # identifier - varName
            self.subroutine_symbol_table.define(self.tokenizer.current_token, type_of, Kind.VAR)
            self.tokenizer.advance()

            # (',' varName)*
            while self.tokenizer.current_token != ";":
                # symbol - ','
                self.tokenizer.advance()
                # identifier - varName
                self.subroutine_symbol_table.define(self.tokenizer.current_token, type_of, Kind.VAR)
                self.tokenizer.advance()

            # symbol ';'
            self.tokenizer.advance()

    def compile_statements(self):
        # statement*
        # letStatement | ifStatement | whileStatement | doStatement | returnStatement

        while True:
            keyword = self.tokenizer.key_word()
            if keyword == KeyWord.LET:
                self.compile_let()
            elif keyword == KeyWord.IF:
                self.compile_if()
            elif keyword == KeyWord.WHILE:
                self.compile_while()
            elif keyword == KeyWord.DO:
                self.compile_do()
            elif keyword == KeyWord.RETURN:
                self.compile_return()
            else:
                break

    def compile_let(self):
        # 'let' varName ('[' expression ']')? '=' expression ';'

        # keyword - let
        self.tokenizer.advance()

        # identifier - varName
        segment, index = self._lookup_symbol(self.tokenizer.current_token)
        self.tokenizer.advance()

        is_arr = False
        if self.tokenizer.current_token == "[":
            is_arr = True
            self.tokenizer.advance()

            self.vm_writer.write_push(segment, index, 1)

            self.compile_expression(False)

            self.vm_writer.write_arithmetic(Command.ADD, 1)

            self.tokenizer.advance()

        self.tokenizer.advance()

        self.compile_expression(False)

        if is_arr:
            self.vm_writer.write_pop(Segment.TEMP, 0, 1)
            self.vm_writer.write_pop(Segment.POINTER, 1, 1)
            self.vm_writer.write_push(Segment.TEMP, 0, 1)
            self.vm_writer.write_pop(Segment.THAT, 0, 1)
        else:
            self.vm_writer.write_pop(segment, index, 1)

        self.tokenizer.advance()

    def compile_if(self):
        # 'if' '(' expression ')' '{' statements '}' ('else' '{' statements '}')?
        start_label = f"L{self.label_count}"
        end_label = f"L{self.label_count + 1}"
        self.label_count += 2

        self.tokenizer.advance()

        self.tokenizer.advance()

        self.compile_expression(False)

        self.vm_writer.write_arithmetic(Command.NOT, 1)
        self.vm_writer.write_if(start_label, 1) # if-goto L0

        self.tokenizer.advance()

        self.tokenizer.advance()

        self.compile_statements()

        self.vm_writer.write_go_to(end_label, 1) # goto L1
        self.vm_writer.write_label(start_label, 1) # label L0

        self.tokenizer.advance()

        if self.tokenizer.key_word() == KeyWord.ELSE:
            self.tokenizer.advance()
            self.tokenizer.advance()

            self.compile_statements()

            self.tokenizer.advance()

        self.vm_writer.write_label(end_label, 1)  # label L1

    def compile_while(self):
        # 'while' '(' expression ')' '{' statements '}'
        start_label = f"L{self.label_count}"
        end_label = f"L{self.label_count + 1}"
        self.label_count += 2

        self.vm_writer.write_label(start_label, 1) # label L0

        self.tokenizer.advance()

        self.tokenizer.advance()

        self.compile_expression(False)

        self.vm_writer.write_arithmetic(Command.NOT, 1)
        self.vm_writer.write_if(end_label, 1) # if-goto L1

        self.tokenizer.advance()
        self.tokenizer.advance()

        self.compile_statements()

        self.vm_writer.write_go_to(start_label, 1) # goto L0
        self.vm_writer.write_label(end_label, 1)

        self.tokenizer.advance()

    def compile_do(self):
        # 'do' routineCall ';'
        self.tokenizer.advance()

        self.compile_expression(True)

        self.tokenizer.advance()

        self.vm_writer.write_pop(Segment.TEMP, 0, 1)

    def compile_return(self):
        # 'return' expression? ';'
        self.tokenizer.advance()

        if self.tokenizer.current_token != ";":
            self.compile_expression(False)

        self.tokenizer.advance()

        if self.is_compiling_void:
            self.vm_writer.write_push(Segment.CONST, 0, 1)
        self.vm_writer.write_return(1)

    # defer
    def compile_expression(self, is_do):
        # term (op term)*
        operators = ["+", "-", "*", "/", "&", "|", "<", ">", "="]

        self.compile_term(is_do)

        while self.tokenizer.current_token in operators:
            is_mult = self.tokenizer.current_token == "*"
            command = get_arithmetic_command(self.tokenizer.current_token)

            self.tokenizer.advance()

            self.compile_term(is_do)

            if command is not None:
                self.vm_writer.write_arithmetic(command, 1)
            else:
                if is_mult:
                    self.vm_writer.write_call("Math.multiply", 2, 1)
                else:
                    self.vm_writer.write_call("Math.divide", 2, 1)

    def compile_term(self, is_do):
        if self.tokenizer.token_type() == TokenType.IDENTIFIER:
            current_token = self.tokenizer.current_token
            self.tokenizer.advance()

            if self.tokenizer.current_token == "(" or self.tokenizer.current_token == ".":
                self._compile_term_subroutine_call(current_token)
            elif self.tokenizer.current_token == "[":
                self._compile_term_array_access(current_token, is_do)
            else:
                segment, index = self._lookup_symbol(current_token)
                self.vm_writer.write_push(segment, index, 1)
            return

        token_type = self.tokenizer.token_type()
        if token_type == TokenType.INT_CONST:
            self.vm_writer.write_push(Segment.CONST, int(self.tokenizer.current_token), 1)
            self.tokenizer.advance()
        elif token_type == TokenType.STRING_CONST:
            # push number of char needed to stack
            str_len = len(self.tokenizer.current_token[1:-1])
            self.vm_writer.write_push(Segment.CONST, str_len, 1)
            self.vm_writer.write_call("String.new", 1, 1)

            for char in self.tokenizer.current_token[1:-1]:
                self.vm_writer.write_push(Segment.CONST, ord(char), 1)
                self.vm_writer.write_call("String.appendChar", 2, 1)

            self.tokenizer.advance()
        elif token_type == TokenType.KEYWORD:
            self._compile_term_keyword_constant()
        elif self.tokenizer.current_token == "-" or self.tokenizer.current_token == "~":
            command = Command.NEG if self.tokenizer.current_token == "-" else Command.NOT
            self.tokenizer.advance()
            self.compile_term(is_do)
            self.vm_writer.write_arithmetic(command, 1)
        elif self.tokenizer.current_token == "(":
            self.tokenizer.advance()
            self.compile_expression(is_do)
            self.tokenizer.advance()

    def compile_expression_list(self):
        # (expression (',' expression)*)?
        n_args = 0

        if self.tokenizer.current_token == ")":
            return n_args

        n_args = n_args + 1
        self.compile_expression(False)

        while self.tokenizer.current_token == ",":
            # symbol - ','
            self.tokenizer.advance()

            n_args = n_args + 1
            self.compile_expression(False)

        return n_args

    def close(self):
        self.vm_writer.close()

    def _lookup_symbol(self, name):
        match = self.subroutine_symbol_table.table.get(name)
        if match is not None:
            kind = self.subroutine_symbol_table.kind_of(name)
            index = self.subroutine_symbol_table.index_of(name)
        else:
            kind = self.class_symbol_table.kind_of(name)
            index = self.class_symbol_table.index_of(name)

        segment = convert_kind_to_segment(kind)
        return segment, index

    def _compile_term_subroutine_call(self, current_token):
        is_in_subroutine_table = self.subroutine_symbol_table.table.get(current_token) is not None
        is_in_class_table = self.class_symbol_table.table.get(current_token) is not None
        is_method = False

        if self.tokenizer.current_token == ".":
            self.tokenizer.advance()

            if is_in_subroutine_table or is_in_class_table:
                # Variable in symbol table — it's an object, so method call
                if is_in_subroutine_table:
                    class_name = self.subroutine_symbol_table.type_of(current_token)
                else:
                    class_name = self.class_symbol_table.type_of(current_token)
                function_name = class_name + "." + self.tokenizer.current_token
                if self.tokenizer.current_token != "new":
                    is_method = True
            else:
                # Not in symbol table — it's a class name, followed by function or constructor call
                function_name = current_token + "." + self.tokenizer.current_token

            self.tokenizer.advance()
        else:
            # Bare subroutine call like draw() — method on this
            is_method = True
            function_name = self.current_class_name + "." + current_token

        self.tokenizer.advance()

        # Push object for method calls BEFORE compiling args
        if is_method:
            if is_in_subroutine_table or is_in_class_table:
                segment, index = self._lookup_symbol(current_token)
                self.vm_writer.write_push(segment, index, 1)
            else:
                self.vm_writer.write_push(Segment.POINTER, 0, 1)

        n_args = self.compile_expression_list()
        if is_method:
            n_args = n_args + 1

        self.vm_writer.write_call(function_name, n_args, 1)
        self.tokenizer.advance()

    def _compile_term_array_access(self, current_token, is_do):
        segment, index = self._lookup_symbol(current_token)
        self.tokenizer.advance()

        self.vm_writer.write_push(segment, index, 1)

        self.compile_expression(is_do)

        self.vm_writer.write_arithmetic(Command.ADD, 1)
        self.vm_writer.write_pop(Segment.POINTER, 1, 1)
        self.vm_writer.write_push(Segment.THAT, 0, 1)

        self.tokenizer.advance()

    def _compile_term_keyword_constant(self):
        if self.tokenizer.key_word() == KeyWord.THIS:
            self.vm_writer.write_push(Segment.POINTER, 0, 1)
        elif self.tokenizer.key_word() == KeyWord.TRUE:
            self.vm_writer.write_push(Segment.CONST, 0, 1)
            self.vm_writer.write_arithmetic(Command.NOT, 1)
        elif self.tokenizer.key_word() == KeyWord.FALSE or self.tokenizer.key_word() == KeyWord.NULL:
            self.vm_writer.write_push(Segment.CONST, 0, 1)
        self.tokenizer.advance()