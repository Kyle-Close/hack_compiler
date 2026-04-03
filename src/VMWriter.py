from Enums import Segment, Command
from pathlib import Path

class VMWriter:
    def __init__(self, path: Path):
        out_file_path = Path(path).with_suffix(".vm")
        self.out_file = open(out_file_path, "w")

    def write_push(self, segment: Segment, index: int, tab_count: int):
        self._write(f"push {segment.value} {index}", tab_count)

    def write_pop(self, segment: Segment, index: int, tab_count: int):
        self._write(f"pop {segment.value} {index}", tab_count)

    def write_arithmetic(self, command: Command, tab_count: int):
        self._write(f"{command.value}", tab_count)

    def write_label(self, label: str, tab_count: int):
        self._write(f"label {label}", tab_count)

    def write_go_to(self, label: str, tab_count: int):
        self._write(f"goto {label}", tab_count)

    def write_if(self, label: str, tab_count: int):
        self._write(f"if-goto {label}", tab_count)

    def write_call(self, name: str, n_args: int, tab_count: int):
        self._write(f"call {name} {n_args}", tab_count)

    def write_function(self, name: str, n_locals: int, tab_count: int):
        self._write(f"function {name} {n_locals}", tab_count)

    def write_return(self, tab_count: int):
        self._write("return", tab_count)

    def _write(self, content, tab_count):
        self.out_file.write(f"{"\t" * tab_count}{content}\n")

    def close(self):
        self.out_file.close()

def get_arithmetic_command(val):
    if val == "+":
        return Command.ADD
    elif val == "-":
        return Command.SUB
    elif val == "&":
        return Command.AND
    elif val == "|":
        return Command.OR
    elif val == "<":
        return Command.LT
    elif val == ">":
        return Command.GT
    elif val == "=":
        return Command.EQ
    else:
        return None