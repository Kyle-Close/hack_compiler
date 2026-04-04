from pathlib import Path

from src.Enums import KeyWord, TokenType, Command, Segment, Kind
from src.JackTokenizer import JackTokenizer
from src.SymbolTable import SymbolTable
from src.VMWriter import VMWriter


class CompilationEngine:
    OPERATORS = frozenset(["+", "-", "*", "/", "&", "|", "<", ">", "="])

    def __init__(self, path: Path):
        self.tokenizer = JackTokenizer(path)
        self.vm_writer = VMWriter(path)
        self.class_symbol_table = SymbolTable()
        self.subroutine_symbol_table = SymbolTable()

        self.current_class_name = ""
        self.current_subroutine_name = ""
        self.label_count = 0

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
            # keyword - 'static' | 'field'
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
        while self.tokenizer.token_type() == TokenType.KEYWORD:
            self.subroutine_symbol_table.start_subroutine()

            # keyword - constructor | function | method
            keyword = self.tokenizer.key_word()
            is_method = keyword == KeyWord.METHOD
            is_constructor = keyword == KeyWord.CONSTRUCTOR

            if is_method:
                self.subroutine_symbol_table.define("this", self.current_class_name, Kind.ARG)

            self.tokenizer.advance()

            # void | type
            is_void = self.tokenizer.key_word() == KeyWord.VOID
            self.tokenizer.advance()

            # identifier - subroutineName
            self.current_subroutine_name = self.tokenizer.current_token
            self.tokenizer.advance()

            # symbol - '('
            self.tokenizer.advance()

            self.compile_parameter_list()

            # symbol - ')'
            self.tokenizer.advance()

            self.compile_subroutine_body(is_constructor, is_method, is_void)

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

    def compile_subroutine_body(self, is_constructor: bool, is_method: bool, is_void: bool):
        # '{' varDec* statements '}'

        # symbol - '{'
        self.tokenizer.advance()

        # varDec*
        self.compile_var_dec()

        self.vm_writer.write_function(f"{self.current_class_name}.{self.current_subroutine_name}",
                                      self.subroutine_symbol_table.var_count(Kind.VAR))

        if is_constructor:
            self.vm_writer.write_push(Segment.CONST, self.class_symbol_table.var_count(Kind.FIELD))
            self.vm_writer.write_call("Memory.alloc", 1)
            self.vm_writer.write_pop(Segment.POINTER, 0)
        elif is_method:
            self.vm_writer.write_push(Segment.ARG, 0)
            self.vm_writer.write_pop(Segment.POINTER, 0)

        # statements
        self.compile_statements(is_void)

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

    def compile_statements(self, is_void: bool):
        # statement*
        # letStatement | ifStatement | whileStatement | doStatement | returnStatement

        while True:
            keyword = self.tokenizer.key_word()
            if keyword == KeyWord.LET:
                self.compile_let()
            elif keyword == KeyWord.IF:
                self.compile_if(is_void)
            elif keyword == KeyWord.WHILE:
                self.compile_while(is_void)
            elif keyword == KeyWord.DO:
                self.compile_do()
            elif keyword == KeyWord.RETURN:
                self.compile_return(is_void)
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
            # symbol - '['
            self.tokenizer.advance()
            self.vm_writer.write_push(segment, index)
            self.compile_expression()
            self.vm_writer.write_arithmetic(Command.ADD)
            # symbol - ']'
            self.tokenizer.advance()

        # symbol - '='
        self.tokenizer.advance()
        self.compile_expression()

        if is_arr:
            self.vm_writer.write_pop(Segment.TEMP, 0)
            self.vm_writer.write_pop(Segment.POINTER, 1)
            self.vm_writer.write_push(Segment.TEMP, 0)
            self.vm_writer.write_pop(Segment.THAT, 0)
        else:
            self.vm_writer.write_pop(segment, index)

        # symbol - ';'
        self.tokenizer.advance()

    def compile_if(self, is_void: bool):
        # 'if' '(' expression ')' '{' statements '}' ('else' '{' statements '}')?
        start_label, end_label = self._new_label_pair()

        # keyword - 'if'
        self.tokenizer.advance()
        # symbol - '('
        self.tokenizer.advance()

        self.compile_expression()

        self.vm_writer.write_arithmetic(Command.NOT)
        self.vm_writer.write_if(start_label) # if-goto L0

        # symbol - ')'
        self.tokenizer.advance()
        # symbol - '{'
        self.tokenizer.advance()

        self.compile_statements(is_void)

        self.vm_writer.write_go_to(end_label) # goto L1
        self.vm_writer.write_label(start_label) # label L0

        # symbol - '}'
        self.tokenizer.advance()

        if self.tokenizer.key_word() == KeyWord.ELSE:
            # keyword - 'else'
            self.tokenizer.advance()
            # symbol - '{'
            self.tokenizer.advance()

            self.compile_statements(is_void)

            # symbol - '}'
            self.tokenizer.advance()

        self.vm_writer.write_label(end_label)  # label L1

    def compile_while(self, is_void: bool):
        # 'while' '(' expression ')' '{' statements '}'
        start_label, end_label = self._new_label_pair()

        self.vm_writer.write_label(start_label) # label L0

        # keyword - 'while'
        self.tokenizer.advance()
        # symbol - '('
        self.tokenizer.advance()

        self.compile_expression()

        self.vm_writer.write_arithmetic(Command.NOT)
        self.vm_writer.write_if(end_label) # if-goto L1

        # symbol - ')'
        self.tokenizer.advance()
        # symbol - '{'
        self.tokenizer.advance()

        self.compile_statements(is_void)

        self.vm_writer.write_go_to(start_label) # goto L0
        self.vm_writer.write_label(end_label)

        # symbol - '}'
        self.tokenizer.advance()

    def compile_do(self):
        # 'do' routineCall ';'
        # keyword - 'do'
        self.tokenizer.advance()

        self.compile_expression()

        # symbol - ';'
        self.tokenizer.advance()

        self.vm_writer.write_pop(Segment.TEMP, 0)

    def compile_return(self, is_void: bool):
        # 'return' expression? ';'
        # keyword - 'return'
        self.tokenizer.advance()

        if self.tokenizer.current_token != ";":
            self.compile_expression()

        # symbol - ';'
        self.tokenizer.advance()

        if is_void:
            self.vm_writer.write_push(Segment.CONST, 0)
        self.vm_writer.write_return()

    def compile_expression(self):
        # term (op term)*
        self.compile_term()

        while self.tokenizer.current_token in self.OPERATORS:
            is_mult = self.tokenizer.current_token == "*"
            command = Command.from_symbol(self.tokenizer.current_token)

            # symbol - op
            self.tokenizer.advance()

            self.compile_term()

            if command is not None:
                self.vm_writer.write_arithmetic(command)
            else:
                if is_mult:
                    self.vm_writer.write_call("Math.multiply", 2)
                else:
                    self.vm_writer.write_call("Math.divide", 2)

    def compile_term(self):
        if self.tokenizer.token_type() == TokenType.IDENTIFIER:
            current_token = self.tokenizer.current_token
            # identifier
            self.tokenizer.advance()

            if self.tokenizer.current_token == "(" or self.tokenizer.current_token == ".":
                self._compile_term_subroutine_call(current_token)
            elif self.tokenizer.current_token == "[":
                self._compile_term_array_access(current_token)
            else:
                segment, index = self._lookup_symbol(current_token)
                self.vm_writer.write_push(segment, index)
            return

        token_type = self.tokenizer.token_type()
        if token_type == TokenType.INT_CONST:
            self.vm_writer.write_push(Segment.CONST, int(self.tokenizer.current_token))
            # integer constant
            self.tokenizer.advance()
        elif token_type == TokenType.STRING_CONST:
            # push number of char needed to stack
            str_len = len(self.tokenizer.current_token[1:-1])
            self.vm_writer.write_push(Segment.CONST, str_len)
            self.vm_writer.write_call("String.new", 1)

            for char in self.tokenizer.current_token[1:-1]:
                self.vm_writer.write_push(Segment.CONST, ord(char))
                self.vm_writer.write_call("String.appendChar", 2)

            # string constant
            self.tokenizer.advance()
        elif token_type == TokenType.KEYWORD:
            self._compile_term_keyword_constant()
        elif self.tokenizer.current_token == "-" or self.tokenizer.current_token == "~":
            command = Command.NEG if self.tokenizer.current_token == "-" else Command.NOT
            # symbol - unary operator
            self.tokenizer.advance()
            self.compile_term()
            self.vm_writer.write_arithmetic(command)
        elif self.tokenizer.current_token == "(":
            # symbol - '('
            self.tokenizer.advance()
            self.compile_expression()
            # symbol - ')'
            self.tokenizer.advance()

    def compile_expression_list(self):
        # (expression (',' expression)*)?
        n_args = 0

        if self.tokenizer.current_token == ")":
            return n_args

        n_args += 1
        self.compile_expression()

        while self.tokenizer.current_token == ",":
            # symbol - ','
            self.tokenizer.advance()

            n_args += 1
            self.compile_expression()

        return n_args

    def close(self):
        self.vm_writer.close()

    def _new_label_pair(self) -> tuple[str, str]:
        start = f"L{self.label_count}"
        end = f"L{self.label_count + 1}"
        self.label_count += 2
        return start, end

    def _lookup_symbol(self, name):
        if self.subroutine_symbol_table.contains(name):
            kind = self.subroutine_symbol_table.kind_of(name)
            index = self.subroutine_symbol_table.index_of(name)
        else:
            kind = self.class_symbol_table.kind_of(name)
            index = self.class_symbol_table.index_of(name)

        return kind.to_segment(), index

    def _compile_term_subroutine_call(self, current_token):
        is_in_subroutine_table = self.subroutine_symbol_table.contains(current_token)
        is_in_class_table = self.class_symbol_table.contains(current_token)
        is_method = False

        if self.tokenizer.current_token == ".":
            # symbol - '.'
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

            # identifier - subroutineName
            self.tokenizer.advance()
        else:
            # Bare subroutine call like draw() — method on this
            is_method = True
            function_name = self.current_class_name + "." + current_token

        # symbol - '('
        self.tokenizer.advance()

        # Push object for method calls BEFORE compiling args
        if is_method:
            if is_in_subroutine_table or is_in_class_table:
                segment, index = self._lookup_symbol(current_token)
                self.vm_writer.write_push(segment, index)
            else:
                self.vm_writer.write_push(Segment.POINTER, 0)

        n_args = self.compile_expression_list()
        if is_method:
            n_args += 1

        self.vm_writer.write_call(function_name, n_args)
        # symbol - ')'
        self.tokenizer.advance()

    def _compile_term_array_access(self, current_token):
        segment, index = self._lookup_symbol(current_token)
        # symbol - '['
        self.tokenizer.advance()

        self.vm_writer.write_push(segment, index)

        self.compile_expression()

        self.vm_writer.write_arithmetic(Command.ADD)
        self.vm_writer.write_pop(Segment.POINTER, 1)
        self.vm_writer.write_push(Segment.THAT, 0)

        # symbol - ']'
        self.tokenizer.advance()

    def _compile_term_keyword_constant(self):
        keyword = self.tokenizer.key_word()
        if keyword == KeyWord.THIS:
            self.vm_writer.write_push(Segment.POINTER, 0)
        elif keyword == KeyWord.TRUE:
            self.vm_writer.write_push(Segment.CONST, 0)
            self.vm_writer.write_arithmetic(Command.NOT)
        elif keyword == KeyWord.FALSE or keyword == KeyWord.NULL:
            self.vm_writer.write_push(Segment.CONST, 0)
        # keyword - 'this' | 'true' | 'false' | 'null'
        self.tokenizer.advance()