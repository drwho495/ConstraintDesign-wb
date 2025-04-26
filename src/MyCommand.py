import FreeCAD

class MyCommand:
    """A sample command for the Constraint Design Workbench"""
    def GetResources(self):
        return {
            'Pixmap': ':/icons/constraint_design_icon.svg',  # Replace with your icon path
            'MenuText': 'My Command',
            'ToolTip': 'This is a sample command for the Constraint Design Workbench'
        }

    def Activated(self):
        print("MyCommand activated")
        FreeCAD.Console.PrintMessage("MyCommand executed\n")

    def IsActive(self):
        return True

# Register the command
FreeCADGui.addCommand('MyCommand', MyCommand())