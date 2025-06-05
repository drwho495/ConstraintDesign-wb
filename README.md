# Constraint Design FreeCAD Workbench.
### What is the point of this addon?
This addon implements an ecosystem for designing and (not yet implemented) assembling parts without needing to worry about any Topological naming problems. The design workbench is designed to work like the integrated Part Design workbench. The assembly portion of this addon will work like the Assembly workbench, and will be developed with speed in mind.

### Why is there less TNP problems?
This addon uses boundaries generated from the sketches used to create features, like extrusions, it then uses a value of 8 random characters to represent each edge or vertex. Then other features like fillets reference those values to get the OpenCascade element to use. If that element name changes because of a feature added then the random element string will change and use the new correct name.

### What about the Assembly workbench in this addon?
It will be designed to have a similar look and feel to the integrated Assembly WB, the main difference is that it will not use a solver. A solverless assembly should run much faster in theory, but it will be less powerful and can be harder to get a part exactly where it needs to be in some situations. It is also much easier to implement, which is the main reason that a solverless system will be used. I also plan on making it easier to implement a solver later on in case it is needed.
