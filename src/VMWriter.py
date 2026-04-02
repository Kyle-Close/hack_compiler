from Enums import Segment, Command
from pathlib import Path

class VMWriter:
    def __init__(self, path: Path):
        out_file_path = Path(path).with_suffix(".vm")
        self.out_file = open(out_file_path, "w")

    def write_push(self, segment: Segment, index: int):
        self.out_file.write(f"push {segment.value} {index}\n")

    def write_pop(self, segment: Segment, index: int):
        self.out_file.write(f"pop {segment.value} {index}\n")

    def write_arithmetic(self, command: Command):
        self.out_file.write(f"{command.value}\n")

    def write_label(self, label: str):
        self.out_file.write(f"label {label}\n")

    def write_go_to(self, label: str):
        self.out_file.write(f"goto {label}\n")

    def write_if(self, label: str):
        self.out_file.write(f"if-goto {label}\n")

    def write_call(self, name: str, n_args: int):
        self.out_file.write(f"call {name} {n_args}\n")

    def write_function(self, name: str, n_locals: int):
        self.out_file.write(f"function {name} {n_locals}\n")

    def write_return(self):
        self.out_file.write("return\n")

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
        raise Exception("NOT IMPLEMENTED")