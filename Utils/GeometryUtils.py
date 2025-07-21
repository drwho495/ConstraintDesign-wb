import json
import FreeCAD as App
import FreeCADGui as Gui
import random
import string
import Part
from Utils.Constants import *
from Utils.Utils import getP2PDistanceAlongNormal

# this will eventually have generic boundary generation code -- like stuff to make boundaries and points from sections

def getIntersectingFaces(prevShape, individualShape, sketchCenter, normal):
    shape2BB = individualShape.BoundBox
    faces = {}

    for face in prevShape.Faces:
        if not face.BoundBox.intersect(shape2BB):
            continue

        distanceStart = getP2PDistanceAlongNormal(sketchCenter, face.CenterOfMass, normal)

        common = face.common(individualShape)
        if not common.isNull() and not common.ShapeType == "Compound":
            faces[distanceStart] = face

    return list(dict(sorted(faces.items())).values())