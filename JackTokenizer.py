def clean_input_file(text):
    cleaned = ""
    in_comment = False

    line: str
    for line in text.splitlines():
        if in_comment:
            end_index = line.find("*/")
            if end_index != -1:
                line = line[end_index + 2:]
                in_comment = False
                if line.strip() != "":
                    cleaned += line.strip()
            else:
                continue

        index = line.find("//")
        if index != -1:
            line = line[:index]
            if line.strip() != "":
                cleaned += line.strip()
            else:
                continue

        index = line.find("/**")
        if index != -1:
            in_comment = True
            end_index = line.find("*/")

            if end_index != -1:
                line = line[:index] + line[end_index + 2:]
                in_comment = False
                if line.strip() != "":
                    cleaned += line.strip()
            else:
                continue

        line = line.strip()
        cleaned += line

    return cleaned

class JackTokenizer:
    def __init__(self, path):
        f = open(path)
        self.inFile = clean_input_file(f.read())

    def has_more_tokens(self):
        pass

    def advance(self):
        pass

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