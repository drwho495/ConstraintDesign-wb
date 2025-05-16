import FreeCAD as App

class Plane:
    def __init__(self, center = App.Vector(0, 0, 0), orientation = App.Rotation()):
        self.center = center
        self.orientation = orientation

        self.updateNormal()

    def updateNormal(self):
        self.normal = self.orientation.multVec(App.Vector(0, 0, 1))

    def getQuaternion(self):
        return self.orientation
    
    def getCenter(self):
        return self.center
    
    def getNormal(self):
        return self.normal