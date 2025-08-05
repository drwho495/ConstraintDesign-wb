from importlib.util import spec_from_file_location, module_from_spec
import sys

# moduleName: module
modulesCache = {}

def importMojoModule(linkedFileLocation: str = "", moduleName: str = ""):
    if (moduleName not in modulesCache) or linkedFileLocation != "":
        moduleSpec = spec_from_file_location(moduleName, linkedFileLocation)
        module = module_from_spec(moduleSpec)
        moduleSpec.loader.exec_module(module)

        modulesCache[moduleName] = module

        return module
    else:
        if moduleName not in modulesCache: raise Exception("Module could not be found in the cache! Please report!")
        return modulesCache[moduleName]

if __name__ == "__main__":
    mojo_module = importMojoModule(
        "/home/hypocritical/.local/share/FreeCAD/Mod/ConstraintDesign-wb/ConstraintDesignMojo/test.so",
        "mojo_module"
    )
    mojo_module = importMojoModule(
        moduleName="mojo_module"
    )

    print(mojo_module.testFreeCADLibraries())