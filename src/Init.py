import FreeCAD

# Define the module name
module_name = "ConstraintDesign"

# Register the module with FreeCAD
def init():
    FreeCAD.Console.PrintMessage(f"Initializing {module_name} module\n")

# Call the init function to register the module
init()