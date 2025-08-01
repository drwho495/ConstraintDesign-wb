# SPDX-License: LGPL-2.1-or-later

from __future__ import annotations
from typing import TYPE_CHECKING
from Utils.Utils import getP2PDistanceAlongNormal

if TYPE_CHECKING:
    import Part  # type: ignore
    import FreeCAD as App  # type: ignore


# this will eventually have generic boundary generation code
# -- like stuff to make boundaries and points from sections


def getIntersectingFaces(
    prevShape: Part.Shape,
    individualShape: Part.Shape,
    sketchCenter: App.Vector,
    normal: App.Vector,
) -> list[Part.Face]:
    """
    Get a list of faces from the previous shape that intersect with the individual shape.
    The faces are sorted by their distance from the sketch center along the normal vector.
    """

    shape2BB = individualShape.BoundBox

    intersecting = (
        (face, face.common(individualShape))
        for face in prevShape.Faces
        if shape2BB.intersect(face.BoundBox)
    )

    faces = {
        getP2PDistanceAlongNormal(sketchCenter, face.CenterOfMass, normal): face
        for face, common in intersecting
        if not common.isNull() and not common.ShapeType == "Compound"
    }

    return [face for _dist, face in sorted(faces.items())]
