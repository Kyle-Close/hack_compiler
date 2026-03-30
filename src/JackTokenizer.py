from Helpers import clean_text
from src.Enums import TokenType, KeyWord

class JackTokenizer:
    SYMBOLS = {"{", "}", "(", ")", "[", "]", ".", ",", ";", "+", "-", "*", "/", "&", "|", "<", ">", "=", "~"}
    DIGITS = {"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"}
    KEYWORDS = {"class", "constructor", "function", "method", "field", "static", "var", "int", "char", "boolean",
                "void", "true", "false", "null", "this", "let", "do", "if", "else", "while", "return"}

    def __init__(self, path):
        f = open(path)
        self.input = clean_text(f.read())
        self.current_token = ""

    def has_more_tokens(self):
        if self.input.strip() == "":
            return False
        else:
            return True

    def advance(self):
        next_char = self.input[0]

        while next_char == " ":
            self.input = self.input[1:]
            next_char = self.input[0]

        # symbol
        if next_char in self.SYMBOLS:
            self.current_token = next_char
            self.input = self.input[1:]
            return

        # integer constant
        if next_char in self.DIGITS:
            self.current_token = ""
            while next_char in self.DIGITS:
                self.current_token += next_char
                self.input = self.input[1:]

                if len(self.input) > 0:
                    next_char = self.input[0]
                    if next_char not in self.DIGITS:
                        return
                else:
                    return

        # string constant
        if next_char == '"':
            self.input = self.input[1:]
            index = self.input.find('"')
            self.current_token = '"' + self.input[:index] + '"'
            self.input = self.input[index + 1:]
            return

        # keyword or identifier
        self.current_token = ""
        while len(self.input) > 0 and self.input[0] not in self.SYMBOLS and self.input[0] != " ":
            self.current_token += self.input[0]
            self.input = self.input[1:]

    def token_type(self):
        if self.current_token in self.KEYWORDS:
            return TokenType.KEYWORD
        elif self.current_token in self.SYMBOLS:
            return TokenType.SYMBOL
        elif self.current_token.isdigit():
            return TokenType.INT_CONST
        elif '"' in self.current_token:
            return TokenType.STRING_CONST
        else:
            return TokenType.IDENTIFIER

    def key_word(self):
        if self.current_token == "class":
            return KeyWord.CLASS
        if self.current_token == "constructor":
            return KeyWord.CONSTRUCTOR
        if self.current_token == "function":
            return KeyWord.FUNCTION
        if self.current_token == "method":
            return KeyWord.METHOD
        if self.current_token == "field":
            return KeyWord.FIELD
        if self.current_token == "static":
            return KeyWord.STATIC
        if self.current_token == "var":
            return KeyWord.VAR
        if self.current_token == "int":
            return KeyWord.INT
        if self.current_token == "char":
            return KeyWord.CHAR
        if self.current_token == "boolean":
            return KeyWord.BOOLEAN
        if self.current_token == "void":
            return KeyWord.VOID
        if self.current_token == "true":
            return KeyWord.TRUE
        if self.current_token == "false":
            return KeyWord.FALSE
        if self.current_token == "null":
            return KeyWord.NULL
        if self.current_token == "this":
            return KeyWord.THIS
        if self.current_token == "let":
            return KeyWord.LET
        if self.current_token == "do":
            return KeyWord.DO
        if self.current_token == "if":
            return KeyWord.IF
        if self.current_token == "else":
            return KeyWord.ELSE
        if self.current_token == "while":
            return KeyWord.WHILE
        if self.current_token == "return":
            return KeyWord.RETURN
        return None

    def symbol(self):
        return self.current_token

    def identifier(self):
        return self.current_token

    def int_val(self):
        return int(self.current_token)

    def string_val(self):
        return self.current_token[1:-1]