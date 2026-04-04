from Enums import Segment, Command
from pathlib import Path

class VMWriter:
    def __init__(self, path: Path):
        out_file_path = Path(path).with_suffix(".vm")
        self.out_file = open(out_file_path, "w")

    def write_push(self, segment: Segment, index: int):
        self._write_instruction(f"push {segment.value} {index}")

    def write_pop(self, segment: Segment, index: int):
        self._write_instruction(f"pop {segment.value} {index}")

    def write_arithmetic(self, command: Command):
        self._write_instruction(f"{command.value}")

    def write_label(self, label: str):
        self._write_instruction(f"label {label}")

    def write_go_to(self, label: str):
        self._write_instruction(f"goto {label}")

    def write_if(self, label: str):
        self._write_instruction(f"if-goto {label}")

    def write_call(self, name: str, n_args: int):
        self._write_instruction(f"call {name} {n_args}")

    def write_function(self, name: str, n_locals: int):
        self.out_file.write(f"function {name} {n_locals}\n")

    def write_return(self):
        self._write_instruction("return")

    def _write_instruction(self, content):
        self.out_file.write(f"\t{content}\n")

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