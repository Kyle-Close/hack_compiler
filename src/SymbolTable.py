from typing import Dict
from dataclasses import dataclass

from Enums import Kind

@dataclass
class SymbolTableRow:
    type_of: str
    kind: Kind
    index: int

class SymbolTable:
    def __init__(self):
        self.table: Dict[str, SymbolTableRow] = {}

    def start_subroutine(self):
        self.table = {}

    def define(self, name: str, type_of: str, kind: Kind):
        index = self.var_count(kind)
        self.table[name] = SymbolTableRow(type_of, kind, index)

    def var_count(self, kind):
        return sum(1 for row in self.table.values() if row.kind == kind)

    def kind_of(self, name):
        return self.table[name].kind

    def type_of(self, name):
        return self.table[name].type_of

    def index_of(self, name):
        return self.table[name].index