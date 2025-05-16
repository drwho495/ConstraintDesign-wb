class PointOnPoint:
    def __init__(self):
        pass
    
    def generateLambdas(self):
        eq1 = lambda x1, x2: x1-x2
        eq2 = lambda y1, y2: y1-y2
        eq3 = lambda z1, z2: z1-z2

        return [eq1, eq2, eq3]