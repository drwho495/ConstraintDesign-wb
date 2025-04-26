class MyModule:
    def __init__(self):
        self.name = "Constraint Design FreeCAD Addon"
        self.version = "1.0.0"
        self.description = "A FreeCAD addon for constraint design."
        self.author = "@drwho495 on GitHub"
    
    def perform_action(self):
        print("Performing action in MyModule")
    
    def get_info(self):
        return f"{self.name} - This module provides core functionalities for the FreeCAD addon."