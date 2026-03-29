from Helpers import clean_text

class JackTokenizer:
    def __init__(self, path):
        f = open(path)
        self.input = clean_text(f.read())
        self.current_token = ""

    def has_more_tokens(self):
        pass

    def advance(self):
        symbols = ["{", "}", "(", ")", "[", "]", ".", ",", ";", "+", "-", "*", "/", "&", "|", "<", ">", "=", "~"]
        digits = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
        keywords = ["class", "constructor", "function", "method", "field", "static", "var", "int", "char", "boolean", "void", "true", "false", "null", "this", "let", "do", "if", "else", "while", "return"]

        next_char = self.input[0]

        while next_char == " ":
            self.input = self.input[1:]
            next_char = self.input[0]

        # symbol
        if next_char in symbols:
            self.current_token = next_char
            self.input = self.input[1:]
            return

        # integer constant
        while next_char in digits:
            self.current_token += next_char
            self.input = self.input[1:]
            if len(self.input) > 0:
                next_char = self.input[0]
                if next_char not in digits:
                    return
            else:
                return

        # string constant
        if next_char == '"':
            self.input = self.input[1:]
            index = self.input.find('"')
            self.current_token = self.input[:index]
            self.input = self.input[index + 1:]
            return

        # keyword or identifier
        self.current_token = ""
        while len(self.input) > 0 and self.input[0] not in symbols and self.input[0] != " ":
            self.current_token += self.input[0]
            self.input = self.input[1:]

    def token_type(self):
        pass

    def key_word(self):
        pass

    def symbol(self):
        pass

    def identifier(self):
        pass

    def int_val(self):
        pass

    def string_val(self):
        pass