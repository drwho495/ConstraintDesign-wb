import os
import sys
import locater
from Commands.CreatePartContainer import CreatePartContainer  # Add this import
from Commands.CreateExtrusion import CreateExtrusion
from Commands.CreatePartMirror import CreatePartMirror
from Commands.CreateFillet import CreateFillet
from Commands.CreateChamfer import CreateChamfer
from Commands.CreateCountersink import CreateCountersink
from Commands.CreateDerive import CreateDerive
from Commands.CreateExposedGeo import CreateExposedGeo
from Commands.MoveFeatureCommands import MoveDesignObject
from Commands.CreateSketch import CreateConstraintSketch
from Utils.GuiUtils import SelectorWidget
import Utils.MojoUtils as MojoUtils
import Grid.GridManager as GridManager
from DesignWorkbench import ConstraintDesign

directory = os.path.dirname(os.path.abspath(locater.__file__))

sys.path.append(os.path.dirname(directory)) # allow python to see ".."

### this is where mojo files are loaded ###
# MojoUtils.importMojoModule(os.path.join(directory, "ConstraintDesignMojo", "test.so"), "mojo_module")
###

__dirname__ = os.path.dirname(locater.__file__)

if sys.version_info[0] == 3 and sys.version_info[1] >= 11:
    # only works with 0.21.2 and above

    FC_MAJOR_VER_REQUIRED = 0
    FC_MINOR_VER_REQUIRED = 21
    FC_PATCH_VER_REQUIRED = 2
    FC_COMMIT_REQUIRED = 33772

    # Check FreeCAD version
    App.Console.PrintLog(App.Qt.translate("Log", "Checking FreeCAD version\n"))
    ver = App.Version()
    major_ver = int(ver[0])
    minor_ver = int(ver[1])
    patch_ver = int(ver[2])
    gitver = ver[3].split()
    if gitver:
        gitver = gitver[0]
    if gitver and gitver != "Unknown":
        gitver = int(gitver)
    else:
        # If we don't have the git version, assume it's OK.
        gitver = FC_COMMIT_REQUIRED

    if major_ver < FC_MAJOR_VER_REQUIRED or (
        major_ver == FC_MAJOR_VER_REQUIRED
        and (
            minor_ver < FC_MINOR_VER_REQUIRED
            or (
                minor_ver == FC_MINOR_VER_REQUIRED
                and (
                    patch_ver < FC_PATCH_VER_REQUIRED
                    or (
                        patch_ver == FC_PATCH_VER_REQUIRED
                        and gitver < FC_COMMIT_REQUIRED
                    )
                )
            )
        )
    ):
        App.Console.PrintWarning(
            App.Qt.translate(
                "Log",
                "FreeCAD version (currently {}.{}.{} ({})) must be at least {}.{}.{} ({}) in order to work with Python 3.11 and above\n",
            ).format(
                int(ver[0]),
                minor_ver,
                patch_ver,
                gitver,
                FC_MAJOR_VER_REQUIRED,
                FC_MINOR_VER_REQUIRED,
                FC_PATCH_VER_REQUIRED,
                FC_COMMIT_REQUIRED,
            )
        )



Gui.addWorkbench(ConstraintDesign())