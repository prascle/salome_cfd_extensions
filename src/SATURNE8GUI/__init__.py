"""
SALOME Saturne8 module implementation

The interface functions of the module are in SATURNE8GUI (outside the module, to be found by SALOME)
SATURNE8GUI instantiate a clientgui object at first call. 
All the interface functions call a method of same name in the clientgui object 

clientgui.py
The class clientgui implements all the interface methods of the SALOME Saturne8 module

CLSMainWindow.py
The class CLSMainWindow is derived from QMainWindow and deals with the Qt widgets of the SALOME Saturne8 module gui.
Main methods deals with: treewidget items, popup menus, selection synchronization between tree and VTK view (meshes)

initlog.py
Implements logging. The trace system is started and the trace level set in SATURNE8GUI 

__init__.py
This file: only the module documentation

mw_saturne_ui.py
Generated from the Qt designer file mw_saturne.ui : Qt widgets nature and geometry 

SATURNE8_DataModel.py
Implements the SATURNE8_DataModel, i.e. what is stored in the SALOME study and saved in the hdf study file.
Only the path of the Saturne8 case files (*.syd) are stored.

utilstudy.py
The DumpMesh function explore the SALOME study to find a loaded mesh and all its groups which have an entry in the study
"""
