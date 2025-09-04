def animate():
    start = 0
    end = 75
    steps = 30
    updateStepDeg = (end - start) / steps
    retBack = True
    
    App.ActiveDocument.VarSet.RotationAmount = start

    for i in range(steps):
        App.ActiveDocument.VarSet.RotationAmount = (updateStepDeg * (i + 1))
        # App.ActiveDocument.recompute()
    App.ActiveDocument.VarSet.RotationAmount = end

    if retBack:
        for i in range(steps):
            App.ActiveDocument.VarSet.RotationAmount = end - (updateStepDeg * (i + 1))
            # App.ActiveDocument.recompute()
        App.ActiveDocument.VarSet.RotationAmount = start

animate()

