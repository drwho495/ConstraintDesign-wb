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
from Commands.SketchUtils import CreateSketch, CreateExternalGeo

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(locater.__file__)))) # allow python to see ".."

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

class ConstraintDesign(Workbench):
    global __dirname__

    MenuText = App.Qt.translate("Workbench", "Constraint Design")
    ToolTip = App.Qt.translate("Workbench", "Constraint Design Workbench")
    Icon = os.path.join(__dirname__, "icons", "ConstraintPart.svg")

    App.Console.PrintLog(Icon)

    commands = [
    ]

    def GetClassName(self):
        return "Gui::PythonWorkbench"

    def Initialize(self):
        """
        Initialize the workbench commands
        """
        # List the commands to be added to the workbench
        mainCommands = [
            'CreatePartContainer'
        ]

        featureCommands = [
            'CreateExtrusion',
            'CreatePartMirror',
            'CreateDerive',
        ]

        dressupCommands = [
            'CreateFillet',
            'CreateChamfer',
            'CreateCountersink'
        ]

        treeCommands = [
            "MoveDesignObjectUp",
            "MoveDesignObjectDown"
        ]

        sketchUtils = [
            'CreateExternalGeo',
            'CreateSketch'
        ]

        datumCommands = [
            'CreateExposedGeo'
        ]
        
        # Register the commands
        self.appendToolbar("Part Container", mainCommands)
        self.appendMenu("Part Container", mainCommands)

        self.appendToolbar("Features", featureCommands)
        self.appendMenu("Features", featureCommands)

        self.appendToolbar("Dressups", dressupCommands)
        self.appendMenu("Dressups", dressupCommands)

        self.appendToolbar("Tree Commands", treeCommands)
        self.appendMenu("Tree Commands", treeCommands)

        self.appendToolbar("Sketcher Utilities", sketchUtils)
        self.appendMenu("Sketcher Utilities", sketchUtils)

        self.appendToolbar("Datum Commands", datumCommands)
        self.appendMenu("Datum Commands", datumCommands)

    def Activated(self):
        pass

    def Deactivated(self):
        pass

Gui.addWorkbench(ConstraintDesign())