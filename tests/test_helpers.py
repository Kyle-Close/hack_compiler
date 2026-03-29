from src.Helpers import clean_text

def test_clean_input_file():
    file = open("../test_files/clean_text.jack")
    text = file.read()
    output: str = clean_text(text)

    assert "//" not in output
    assert "/**" not in output

    assert "This // something else" not in output
    assert "Initializes a new Square" not in output
    assert "Added for testing" not in output
    assert "???" not in output
    assert "* Implements the Square game." not in output

    assert "hello" in output
    assert "class Main {" in output
    assert "static boolean test;" in output