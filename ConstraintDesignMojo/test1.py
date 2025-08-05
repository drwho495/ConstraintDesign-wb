# import max.mojo.importer
from importlib.util import spec_from_file_location
import sys

class test:
    def find_spec(
        self,
        name,
        import_path,
        target,
    ):
        return spec_from_file_location("mojo_module", "/home/hypocritical/.local/share/FreeCAD/Mod/ConstraintDesign-wb/ConstraintDesignMojo/__mojocache__/mojo_module.hash-140c5abddf507670.so")

sys.meta_path.append(test())
sys.path.insert(0, "")


import mojo_module

print(mojo_module.factorial(5))
