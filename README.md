# Constraint Design FreeCAD Workbench.

![image](https://github.com/user-attachments/assets/ca713e83-d071-4174-9162-bc58b7d7f4c6)
###### The grid is including in the addon, and enabled by default.


## What is this workbench?
Constraint Design is an addon for FreeCAD that aims to implement a more stable alternative to the integrated Part Design workbench. One of the most important new features that you can use with this new workbench is the custom element selector, which are not directly tied to OpenCascade elements. This means that you will encounter less [Topological Naming Problems](https://wiki.freecad.org/Topological_naming_problem) when compared to other solutions built into FreeCAD.

## Why should I use this?
The main benefit of this addon is the lack of Topological Naming Problems, as stated earlier. When making changes to parts, it is much less likely that you will have bizzare errors or changes that you wouldn't expect. You can also use the Assembly 4.1 workbench with Constraint Design out of the box (changes to implement are not yet merged into upstream). This integration gives you tools to create assemblies, variant parts, basic animations, BOMs and much more. Many of the tools you see in Part Design (Extrude, Part Mirror, Loft, Fillets, Chamfers, Countersinks, Sweeps [not yet\], Revolves [not yet\], Linear Patterns, Circular Patterns [not yet\], Feature Mirror [not yet\] and many more) are also implemented into this workbench. There are also some new features, like the Part Mirror or Derive tool, which you do not seem in Part Design.

## How does it work?
The only thing you select when working with ConstraintDesign Parts are boundaries generated every time you recompute the part. Each edge and most vertexes (loft is missing support still) have an entry into an ElementMap which contain a persistent name that does not change every time you recompute the part. The selection system looks into the map to find the most up to date OpenCascade element name which can be used safely. These element names will change every time something is added or removed from a previous sketch, but the map will update with the correct name so that there are few TNPs.

## The problems.
### Some toponaming edgecases
Nothing is perfect, especially not this workbench. Here are some examples of small edgecases with the Toponaming system:
 * Lofts do not have perfect checks, and some renames do not work properly. I've mitigated most of the areas failure points so far, but it's not perfect.
 * Sketch trimming can cause renames of geometry, which can cause some unwanted changes. I have no current plans to implement more complex checks to fix this, as it would take a long time and be rather unreliable in my opinion.
 * Weird ID naming.

### Speed
The speed of regeneration of these parts can take significantly longer than if the part was created in another workbench. I am working on this issue actively, since there have been some large improvements since before releasing 1.0.0 of the addon. I was able to decrease the time of generation of boundaries, for example, from 1.9 seconds or so to about 100 milliseconds. Dressups take a lot longer because they check the geometry of the OpenCascade generated shape for the right edges.

### Bugs
There are a LOT of bugs currently, please report them in the issues tab of this addon!
