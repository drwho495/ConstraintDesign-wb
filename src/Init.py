import FreeCAD
import FreeCADGui

# Define the module name
module_name = "ConstraintDesign"

# Register the module with FreeCAD
def init():
    FreeCAD.Console.PrintMessage("Initializing " + module_name + "\n")
    FreeCADGui.addModule(module_name)

# Call the init function to register the module
init()