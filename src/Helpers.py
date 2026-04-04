from src.Enums import Kind, Segment

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

def convert_kind_to_segment(kind: Kind):
    if kind == Kind.STATIC:
        return Segment.STATIC
    elif kind == Kind.FIELD:
        return Segment.THIS
    elif kind == Kind.ARG:
        return Segment.ARG
    elif kind == Kind.VAR:
        return Segment.LOCAL
    else:
        raise Exception(f"Cannot convert kind: {kind} to segment")