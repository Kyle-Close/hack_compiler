from src.Helpers import clean_text
from src.Enums import TokenType, KeyWord

class JackTokenizer:
    SYMBOLS = {"{", "}", "(", ")", "[", "]", ".", ",", ";", "+", "-", "*", "/", "&", "|", "<", ">", "=", "~"}
    DIGITS = {"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"}
    KEYWORD_MAP = {
        "class": KeyWord.CLASS, "constructor": KeyWord.CONSTRUCTOR, "function": KeyWord.FUNCTION,
        "method": KeyWord.METHOD, "field": KeyWord.FIELD, "static": KeyWord.STATIC,
        "var": KeyWord.VAR, "int": KeyWord.INT, "char": KeyWord.CHAR, "boolean": KeyWord.BOOLEAN,
        "void": KeyWord.VOID, "true": KeyWord.TRUE, "false": KeyWord.FALSE, "null": KeyWord.NULL,
        "this": KeyWord.THIS, "let": KeyWord.LET, "do": KeyWord.DO, "if": KeyWord.IF,
        "else": KeyWord.ELSE, "while": KeyWord.WHILE, "return": KeyWord.RETURN,
    }

    def __init__(self, path):
        with open(path) as f:
            self.input = clean_text(f.read())
        self.current_token = ""

    def has_more_tokens(self):
        return bool(self.input.strip())

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
        if self.current_token in self.KEYWORD_MAP:
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
        return self.KEYWORD_MAP.get(self.current_token)

    def symbol(self):
        return self.current_token

    def identifier(self):
        return self.current_token

    def int_val(self):
        return int(self.current_token)

    def string_val(self):
        return self.current_token[1:-1]