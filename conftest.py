import pytest
from magma import clear_cachedFunctions
import os


collect_ignore=["silica/_testing.py", "generate_notebooks.py", "examples/jtag_tap.py"]


@pytest.fixture(autouse=True)
def silica_test():
    import silica
    # silica.config.compile_dir = 'callee_file_dir'
    import magma
    # magma.config.set_compile_dir('callee_file_dir')
    clear_cachedFunctions()

    # os.system("rm -rf tests/build/*")
