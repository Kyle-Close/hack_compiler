from enum import Enum

class TokenType(Enum):
    KEYWORD = 1
    SYMBOL = 2
    IDENTIFIER = 3
    INT_CONST = 4
    STRING_CONST = 5

class KeyWord(Enum):
    CLASS = 1
    METHOD = 2
    FUNCTION = 3
    CONSTRUCTOR = 4
    INT = 5
    BOOLEAN = 6
    CHAR = 7
    VOID = 8
    VAR = 9
    STATIC = 10
    FIELD = 11
    LET = 12
    DO = 13
    IF = 14
    ELSE = 15
    WHILE = 16
    RETURN = 17
    TRUE = 18
    FALSE = 19
    NULL = 20
    THIS = 21

class Kind(Enum):
    STATIC = "static"
    FIELD = "this"
    ARG = "argument"
    VAR = "local"
    NONE = "none"

    def to_segment(self):
        segment = _KIND_TO_SEGMENT.get(self)
        if segment is None:
            raise Exception(f"Cannot convert kind: {self} to segment")
        return segment

class Segment(Enum):
    CONST = "constant"
    ARG = "argument"
    LOCAL = "local"
    STATIC = "static"
    THIS = "this"
    THAT = "that"
    POINTER = "pointer"
    TEMP = "temp"

_KIND_TO_SEGMENT = {
    Kind.STATIC: Segment.STATIC,
    Kind.FIELD:  Segment.THIS,
    Kind.ARG:    Segment.ARG,
    Kind.VAR:    Segment.LOCAL,
}

class Command(Enum):
    ADD = "add"
    SUB = "sub"
    NEG = "neg"
    EQ = "eq"
    GT = "gt"
    LT = "lt"
    AND = "and"
    OR = "or"
    NOT = "not"

    _SYMBOL_MAP = {
        "+": "ADD", "-": "SUB", "&": "AND", "|": "OR",
        "<": "LT",  ">": "GT",  "=": "EQ",
    }

    @classmethod
    def from_symbol(cls, symbol: str):
        name = cls._SYMBOL_MAP.value.get(symbol)
        return cls[name] if name else None