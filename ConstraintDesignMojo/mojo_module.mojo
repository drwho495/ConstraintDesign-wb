from python import PythonObject, Python
from python.bindings import PythonModuleBuilder
import math
from os import abort

@export
fn PyInit_mojo_module() -> PythonObject:
    try:
        var m = PythonModuleBuilder("mojo_module")
        m.def_function[testFreeCADLibraries]("testFreeCADLibraries", docstring="Compute n!")
        return m.finalize()
    except e:
        return abort[PythonObject](String("error creating Python Mojo module:", e))

fn testFreeCADLibraries() -> PythonObject:
    try:
        var App = Python.import_module("FreeCAD")
        print(App.ActiveDocument.Label)
        return True
    except:
        print("failed!")
        return False