import os
import FreeCAD as App
import FreeCADGui as Gui
import Part
from PySide import QtGui
from Utils.Utils import isType
from Utils.Constants import *
from Entities.ExposedGeo import makeExposedGeo
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # allow python to see ".."

def getIDDict(support, includeConstruction = True, includeExternalConstruction = False):
    # "ID": geometry
    idDict = {}
    if isType(support, "BoundarySketch"):
        for geoF in support.GeometryFacadeList:
            if not includeConstruction and geoF.Construction: continue

            idDict[f"g{str(geoF.Id)}"] = geoF.Geometry
        
        externalGeo = support.ExternalGeo.copy()

        if len(externalGeo) != 0:
            for geo in externalGeo:
                geoF = None
                externalGeoExt = None
                defining = False

                try:
                    geoF = geo.getExtensionOfType("Sketcher::SketchGeometryExtension")
                    externalGeoExt = geo.getExtensionOfType("Sketcher::ExternalGeometryExtension")
                except:
                    pass
                
                if externalGeoExt != None:
                    try:
                        defining = externalGeoExt.testFlag("Defining") # This needs to be checked seperately, because of older versions of FreeCAD
                    except:
                        pass
                
                if geoF != None and geoF.Id >= 1 and (includeExternalConstruction or defining):
                    idDict[f"eg{geoF.Id}"] = geo
    elif isType(support, "GearsWBPart"):
        shCopy = support.Shape.copy()
        shCopy.Placement = App.Placement()

        for i, edge in enumerate(shCopy.Edges):
            geometry = None

            if edge.Curve.TypeId == "Part::GeomLine":
                geometry = Part.LineSegment(edge.Vertexes[0].Point, edge.Vertexes[1].Point)
            elif edge.Curve.TypeId == "Part::GeomArcOfCircle":
                geometry = Part.Arc(edge.Curve.StartPoint, edge.Curve.MidPoint, edge.Curve.EndPoint)
            elif edge.Curve.TypeId == "Part::GeomBSplineCurve":
                points = 10

                if hasattr(support, "numpoints"):
                    points = support.numpoints

                geometry = Part.BSplineCurve(edge.discretize(points))
            
            if geometry != None:
                idDict[f"gg{i + 1}"] = geometry
        
        # create bounding box
        edgeLen = 10
        topLS = Part.LineSegment(App.Vector(-edgeLen/2, edgeLen/2), App.Vector(edgeLen/2, edgeLen/2))
        idDict[f"bbT"] = topLS

        rightLS = Part.LineSegment(App.Vector(edgeLen/2, edgeLen/2), App.Vector(edgeLen/2, -edgeLen/2))
        idDict[f"bbR"] = rightLS

        bottomLS = Part.LineSegment(App.Vector(edgeLen/2, -edgeLen/2), App.Vector(-edgeLen/2, -edgeLen/2))
        idDict[f"bbB"] = bottomLS

        leftLS = Part.LineSegment(App.Vector(-edgeLen/2, -edgeLen/2), App.Vector(-edgeLen/2, edgeLen/2))
        idDict[f"bbL"] = leftLS

    return idDict

def hasExternalGeometryBug():
    version = App.Version()

    return int(version[0]) == 1 and int(version[1]) >= 1