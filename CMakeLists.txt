# ConstraintDesign workbench CMakeLists.txt

SET(ConstraintDesign_SRCS
    __init__.py
    Init.py
    InitGui.py
    locater.py
    DesignWorkbench.py
    PartContainer.py
    AssemblyContainer.py
)

SET(ConstraintDesign_Commands_SRCS
    Commands/CreatePartContainer.py
    Commands/CreateConstraintLink.py
    Commands/CreateExtrusion.py
    Commands/CreateLinearPattern.py
    Commands/CreatePartMirror.py
    Commands/CreateFillet.py
    Commands/CreateChamfer.py
    Commands/CreateCountersink.py
    Commands/CreateLoft.py
    Commands/CreateDerive.py
    Commands/CreateExposedGeo.py
    Commands/EditSketchPlacement.py
    Commands/MoveFeatureCommands.py
    Commands/CreateSketch.py
    Commands/CreateJoint.py
    Commands/AddVarset.py
    Commands/UpdateSketchVisibility.py
)

SET(ConstraintDesign_Entities_SRCS
    Entities/Entity.py
    Entities/Feature.py
    Entities/Extrusion.py
    Entities/PartMirror.py
    Entities/Pattern.py
    Entities/Loft.py
    Entities/Derive.py
    Entities/Dressup.py
    Entities/ExposedGeo.py
    Entities/Joint.py
    Entities/ConstraintSketch.py
    Entities/DatumPlane.py
    Entities/FeatureCopy.py
)

SET(ConstraintDesign_Utils_SRCS
    Utils/Utils.py
    Utils/GuiUtils.py
    Utils/GeometryUtils.py
    Utils/MojoUtils.py
    Utils/SketchUtils.py
    Utils/Constants.py
)

SET(ConstraintDesign_Grid_SRCS
    Grid/GridManager.py
)

SET(ConstraintDesign_Cache_SRCS
    Cache/DocumentCacheManager.py
)

# Icons - list explicitly without directory prefix for proper installation
SET(ConstraintDesign_Icons
    Chamfer.svg
    ConstraintDesignLogo.svg
    ConstraintLinkPart.svg
    ConstraintPart.svg
    Countersink.svg
    Derive.svg
    Down.svg
    ExposedGeo.svg
    Extrusion.svg
    FeatureMirror.svg
    Fillet.svg
    Joint.svg
    LinearPattern.svg
    LinkFeature.svg
    Loft.svg
    PartMirror.svg
    Sketch.svg
    Up.svg
)

SET(ConstraintDesign_All_SRCS
    ${ConstraintDesign_SRCS}
    ${ConstraintDesign_Commands_SRCS}
    ${ConstraintDesign_Entities_SRCS}
    ${ConstraintDesign_Utils_SRCS}
    ${ConstraintDesign_Grid_SRCS}
    ${ConstraintDesign_Cache_SRCS}
)

SOURCE_GROUP("" FILES ${ConstraintDesign_All_SRCS})

ADD_CUSTOM_TARGET(ConstraintDesign ALL
    SOURCES ${ConstraintDesign_All_SRCS}
)

fc_copy_sources(ConstraintDesign "${CMAKE_BINARY_DIR}/Mod/ConstraintDesign-wb" ${ConstraintDesign_All_SRCS})
# Copy icons separately to preserve directory structure
file(COPY ${CMAKE_CURRENT_SOURCE_DIR}/icons/
     DESTINATION ${CMAKE_BINARY_DIR}/Mod/ConstraintDesign-wb/icons
     FILES_MATCHING PATTERN "*.svg"
)

# Install main files
INSTALL(
    FILES
        ${ConstraintDesign_SRCS}
        package.xml
        LICENSE
        README.md
    DESTINATION Mod/ConstraintDesign-wb
)

# Install Commands
INSTALL(
    FILES ${ConstraintDesign_Commands_SRCS}
    DESTINATION Mod/ConstraintDesign-wb/Commands
)

# Install Entities
INSTALL(
    FILES ${ConstraintDesign_Entities_SRCS}
    DESTINATION Mod/ConstraintDesign-wb/Entities
)

# Install Utils
INSTALL(
    FILES ${ConstraintDesign_Utils_SRCS}
    DESTINATION Mod/ConstraintDesign-wb/Utils
)

# Install Grid
INSTALL(
    FILES ${ConstraintDesign_Grid_SRCS}
    DESTINATION Mod/ConstraintDesign-wb/Grid
)

# Install Cache
INSTALL(
    FILES ${ConstraintDesign_Cache_SRCS}
    DESTINATION Mod/ConstraintDesign-wb/Cache
)

# Install icons - specify full path from source directory
foreach(icon ${ConstraintDesign_Icons})
    INSTALL(
        FILES icons/${icon}
        DESTINATION Mod/ConstraintDesign-wb/icons
    )
endforeach()
