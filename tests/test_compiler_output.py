import difflib
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
GOLDEN_DIR = Path(__file__).parent / "golden"


def get_test_dirs():
    """Return subdirectories of golden/ that have .vm files (one per test case)."""
    return sorted(d.name for d in GOLDEN_DIR.iterdir() if d.is_dir())


@pytest.mark.parametrize("dir_name", get_test_dirs())
def test_compiler_output(tmp_path, dir_name):
    golden_dir = GOLDEN_DIR / dir_name

    # Copy only .jack files to a temp directory so the compiler never writes
    # into tests/golden/
    tmp_dir = tmp_path / dir_name
    tmp_dir.mkdir()
    for jack_file in golden_dir.glob("*.jack"):
        shutil.copy(jack_file, tmp_dir / jack_file.name)

    # Run the compiler on the temp directory
    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "src" / "JackAnalyzer.py"), str(tmp_dir)],
        env={**os.environ, "PYTHONPATH": str(PROJECT_ROOT)},
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"Compiler exited with code {result.returncode}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )

    # Compare each generated .vm file against the immutable golden copy
    golden_vms = sorted(golden_dir.glob("*.vm"))
    assert golden_vms, f"No golden .vm files found in {golden_dir}"

    for golden_vm in golden_vms:
        generated_vm = tmp_dir / golden_vm.name
        assert generated_vm.exists(), (
            f"Compiler did not produce {golden_vm.name} for {dir_name}"
        )

        golden_content = golden_vm.read_text()
        generated_content = generated_vm.read_text()
        if generated_content != golden_content:
            diff = difflib.unified_diff(
                golden_content.splitlines(keepends=True),
                generated_content.splitlines(keepends=True),
                fromfile=f"golden/{dir_name}/{golden_vm.name}",
                tofile=f"generated/{golden_vm.name}",
            )
            pytest.fail(f"Output mismatch for {dir_name}/{golden_vm.name}:\n{''.join(diff)}")