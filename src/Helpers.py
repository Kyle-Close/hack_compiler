import unittest

def clean_text(text):
    cleaned = ""
    in_comment = False

    line: str
    for line in text.splitlines():
        if line.strip() == "":
            continue

        if in_comment:
            end_index = line.find("*/")
            if end_index != -1:
                line = line[end_index + 2:]
                in_comment = False
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
            else:
                continue

        index = line.find("//")
        if index != -1:
            line = line[:index]
            if line.strip() != "":
                cleaned += line.strip()
                continue
            else:
                continue

        line = line.strip()
        cleaned += line

    return cleaned

def force_empty_newlines(element, space="  ", level=0):
    for child in element:
        if len(child) == 0 and not child.text:
            child.text = "\n" + space * (level + 1)
        force_empty_newlines(child, space, level + 1)