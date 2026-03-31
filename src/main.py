import sys
from pathlib import Path

from JackTokenizer import JackTokenizer
from Enums import TokenType
from src.CompilationEngine import CompilationEngine

if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(f"Expected 2 arguments but got {len(sys.argv)}.")

    path = Path(sys.argv[1])

    if path.is_file():
        if path.suffix != ".jack":
            sys.exit(f"The file provided is not a jack program: {path}")
        engine = CompilationEngine(path)

    elif path.is_dir():
        for child in path.iterdir():
            if child.suffix != ".jack":
                continue

            engine = CompilationEngine(child)

    else:
        sys.exit(f"Path to file or directory is invalid: {path}")