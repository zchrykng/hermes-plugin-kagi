"""Import root entry point under an explicit test-only package identity.

The checkout can have any basename; Hermes uses its own runtime module name.
No Hermes modules are replaced and relative provider imports remain real.
"""
import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_NAME = "hermes_test_kagi"
if PACKAGE_NAME not in sys.modules:
    spec = importlib.util.spec_from_file_location(
        PACKAGE_NAME, ROOT / "__init__.py", submodule_search_locations=[str(ROOT)]
    )
    package = importlib.util.module_from_spec(spec)
    sys.modules[PACKAGE_NAME] = package
    try:
        spec.loader.exec_module(package)
    except BaseException:
        sys.modules.pop(PACKAGE_NAME, None)
        raise
package = sys.modules[PACKAGE_NAME]
provider = sys.modules[PACKAGE_NAME + ".provider"]
KagiWebSearchProvider = provider.KagiWebSearchProvider
