# -*- coding: utf-8 -*-

import os
import logging

import SalomePyQt
from qtsalome import QMainWindow, QTreeWidgetItem, QAbstractItemView, QSize, Qt

from .mw_saturne8_ui import Ui_mw_Saturne

from .constants import col

_sgPyQt = None


def getSalomePyQt():
    global _sgPyQt
    if _sgPyQt is None:
        _sgPyQt = SalomePyQt.SalomePyQt()
    return _sgPyQt


class CLSMainWindow(QMainWindow):

    def __init__(self, parent):
        """
        Initialize the treeWidget for Saturne cases
        """
        QMainWindow.__init__(self, parent)
        logging.debug("__init__")
        self.ui = Ui_mw_Saturne()
        self.ui.setupUi(self)
        self.ui.tw_gauche.setColumnCount(5)
        self.ui.tw_gauche.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.saturneFolder = QTreeWidgetItem()
        self.saturneFolder.setText(col.name, "CFD Studies")
        self.saturneFolder.setText(col.ref, "REF")
        self.saturneFolder.setText(col.details, "details")
        self.saturneFolder.setText(col.entry, "entry")
        self.saturneFolder.setText(col.id, "id")
        self.ui.tw_gauche.hideColumn(col.ref)
        self.ui.tw_gauche.addTopLevelItem(self.saturneFolder)
        self.ui.tw_gauche.itemSelectionChanged.connect(
            self.treeSelectionChanged)
        self.saturneItems = {}       # Tree item from case path
        self.saturneCondMeshes = {}  # Tree item from conduction mesh file path
        self.saturneRayMeshes = {}   # Tree item from radiation mesh file path
        self.entryItems = {}         # Entry from tree item
        self.treeItemMenuMgr = None
        self.selectedEntry = None
        self.selectedItem = None
        self.selectedParent = None
    
    def setHSplitterSizes(self, l1, l2, l3):
        self.ui.splitter.setSizes([l1,l2,l3])
        
    def getSaturneFolder(self):
        return self.saturneFolder
    
    def getCurrentSelectedItem(self):
        return self.selectedItem
    
    def removeItem(self, item):
        logging.debug("removeItem %s",item.text(col.name))
        parent = item.parent()
        self.selectedParent = parent
        parent.removeChild(item)

    def initialSelection(self, item):
        """
        Useful when tree widget is first filled with a study and nothing was selected,
        to detect the current study from menu/toolbar
        """
        twiSelected = self.ui.tw_gauche.selectedItems()
        if self.ui.tw_gauche.selectedItems():
            logging.debug("initialSelection %s", twiSelected[0].text(col.details))
        logging.debug("set an initial selection on tree widget")
        self.ui.tw_gauche.setCurrentItem(item)
        self.treeSelectionChanged()
    
    def initContextMenus(self, treeItemMenuMgr):
        """
        The specific actions menus for each tree item are defined in clientgui.treeItemMenuMgr
        @see clientgui.activate
        """
        logging.debug("initContextMenus")
        self.treeItemMenuMgr = treeItemMenuMgr
        self.ui.tw_gauche.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.tw_gauche.customContextMenuRequested.connect(
            self.treeItemMenuMgr)

    # def addSaturneItem(self, CaseName, meshCond, meshRay):
    #     """
    #     Add a Case Item in the tree, with one or two children items 
    #     corresponding the conduction and radiation meshes

    #     :param string CaseName: the Saturne case name (file path)
    #     :param string meshCond: conduction mesh file path
    #     :param string meshRay: radiation mesh file path (empty if no radiation)
    #     """
    #     logging.debug("addSaturneItem %s %s %s", CaseName, meshCond, meshRay)
    #     saturneItem = None
    #     if CaseName in self.saturneItems.keys():
    #         saturneItem = self.saturneItems[CaseName]
    #     else:
    #         saturneItem = QTreeWidgetItem()
    #         saturneItem.setText(col.name, os.path.basename(CaseName))
    #         saturneItem.setText(col.details, os.path.dirname(CaseName))
    #         saturneItem.setToolTip(col.details, os.path.dirname(CaseName))
    #         self.saturneItems[CaseName] = saturneItem
    #         self.saturneFolder.addChild(saturneItem)
    #     # first case load or study reload
    #     if len(os.path.basename(meshCond)) > 0 and saturneItem.childCount() == 0:
    #         saturneCondMeshItem = QTreeWidgetItem()
    #         saturneCondMeshItem.setText(col.name, os.path.basename(meshCond))
    #         saturneCondMeshItem.setText(col.details, os.path.dirname(meshCond))
    #         saturneCondMeshItem.setToolTip(col.details, os.path.dirname(meshCond))
    #         self.saturneCondMeshes[meshCond] = saturneCondMeshItem
    #         saturneItem.addChild(saturneCondMeshItem)
    #     # first case load or study reload
    #     if len(os.path.basename(meshRay)) > 0 and saturneItem.childCount() == 1:
    #         saturneRayMeshItem = QTreeWidgetItem()
    #         saturneRayMeshItem.setText(col.name, os.path.basename(meshRay))
    #         saturneRayMeshItem.setText(col.details, os.path.dirname(meshRay))
    #         saturneRayMeshItem.setToolTip(col.details, os.path.dirname(meshRay))
    #         self.saturneRayMeshes[meshRay] = saturneRayMeshItem
    #         saturneItem.addChild(saturneRayMeshItem)
    #     self.ui.tw_gauche.setCurrentItem(saturneItem)
    #     self.ui.tw_gauche.expandItem(saturneItem)
    #     for i in range(4):
    #         self.ui.tw_gauche.resizeColumnToContents(i)

    # def readSyrDesc(self, medFile):
    #     """
    #     Transforms the .sysr_desc file in dictionaries giving Saturne references for each group.

    #     The first key is the type of group in ("faces", "nodes", "edges", "volumes"),
    #     the secong key is the name of the group.
    #     The .syr_desc file gives the Saturne references associated to the groups in the mesh.
    #     This file is produced at the same time as the .syr file,
    #     with the same name, when using convert2saturne with a med file.
    #     Some groups may be the concatenation of several other groups, for instance 2 groups of faces.
    #     These concatenation groups, present in the med file, are not visible when opening the med file in salome.
    #     Some groups of the med mesh may not have a reference in the .syr_desc file.

    #     :param string medFile: path of the med file.

    #     :return: dictionary giving Saturne reference from group type and name
    #     :rtype: dictionary
    #     """
    #     logging.debug("readSyrDesc %s", medFile)
    #     syrdesc = {}
    #     # --- The .syr_desc file is in the same directory as the med file
    #     syrdescFile = os.path.splitext(medFile)[0] + '.syr_desc'
    #     if not os.path.isfile(syrdescFile):
    #         return syrdesc
    #     # --- we look for groups of faces, edges, volumes, nodes
    #     groupTypes = ("faces", "nodes", "edges", "volumes")
    #     for aType in groupTypes:
    #         syrdesc[aType] = {}
    #     # --- iterate on the lines in .syr_desc file, containing
    #     #     groupType, reference, groupName
    #     with open(syrdescFile, encoding='utf-8') as f:
    #         for line in f:
    #             items = line.split()
    #             if len(items) > 2:
    #                 groupName = items[0]
    #                 ref = items[1]
    #                 name = items[2]
    #                 for aType in groupTypes:
    #                     if aType in groupName:
    #                         syrdesc[aType][name] = ref
    #     logging.debug("syrdesc %s", syrdesc)
    #     return syrdesc

    def detailsMeshGroups(self, medFile, meshItem, liste):
        """
        Generate tree items for each group in a mesh
        
        :param string medFile: path of the med file.
        :param QTreeWidgetItem meshItem: QTreeWidgetItem associated to the meshFile
        :param list liste: a list of (parent, entry, name, offset) for each child
                           of the mesh in SALOME study (@see utilsstudy.DumpMesh)
        """
        from .CFDSTUDYGUI_DataModel import dict_object
        logging.debug("detailsMeshGroups %s %s", medFile, liste)
        if meshItem is None:
            logging.debug("meshItem is None")
            return
        groupTypes = ("faces", "nodes", "edges", "volumes")
        parentItem = meshItem
        for (parent, entry, name, offset) in liste:
            # --- offset 0 gives the entry and name of the mesh in Salome Study
            if offset == 0:
                meshItem.setText(col.entry, entry)
                self.entryItems[entry] = meshItem
            # --- offset 1 gives the groupType entry and name in Salome Study
            elif offset == 1:
                groupTypeItem = QTreeWidgetItem()
                groupTypeItem.setText(col.name, name)
                groupTypeItem.setText(col.entry, entry)
                self.entryItems[entry] = groupTypeItem
                meshItem.addChild(groupTypeItem)
                parentItem = groupTypeItem
            # --- offset 2 gives groupType(parent), group entry and name in Salome Study.
            else:
                groupItem = QTreeWidgetItem()
                groupItem.setText(col.name, name)
                # groupItem.setText(col.ref, ref)
                groupItem.setText(col.entry, entry)
                groupItem.setText(col.id, str(dict_object["Display"]))
                self.entryItems[entry] = groupItem
                parentItem.addChild(groupItem)
        self.ui.tw_gauche.expandItem(meshItem)
        for i in range(4):
            self.ui.tw_gauche.resizeColumnToContents(i)

    def treeSelectionChanged(self):
        """
        Called when one or more items are selected in the tree
        """
        logging.debug("new tree selection")
        selectedItems = self.ui.tw_gauche.selectedItems()
        if selectedItems:
            self.selectedItem = selectedItems[0]
            self.selectedParent = self.selectedItem.parent()
        else:
            self.selectedItem = self.selectedParent
        listEntries = []
        for item in selectedItems:
            logging.debug("selection: %s %s", item.text(
                col.name), item.text(col.entry))
            self.selectedEntry = item.text(col.entry)
            listEntries.append(item.text(col.entry))
        getSalomePyQt().setSelection(listEntries)

    def externSelectionChanged(self, entryList):
        """
        Called when one or more items are selected outside the tree (in the view, for instance)
        """
        logging.debug("new extern selection: %s", entryList)
        for entry in entryList:
            self.selectedEntry = entry
            if entry in self.entryItems.keys():
                item = self.entryItems[entry]
                self.ui.tw_gauche.setCurrentItem(item)

    def getNameAndRef(self):
        """
        From selected item,
        return the group name, its reference and type ("VOLUME", "FACE", "EDGE")
        """
        entry = self.selectedEntry
        logging.debug("getNameAndRef %s", entry)
        name = ""
        ref = ""
        typeGroup = ""
        if entry in self.entryItems.keys():
            item = self.entryItems[entry]
            name = item.text(col.name)
            ref = item.text(col.ref)
            parent = item.parent()
            if "face" in parent.text(col.name):
                typeGroup = "FACE"
            elif "edge" in parent.text(col.name):
                typeGroup = "EDGE"
            elif "volume" in parent.text(col.name):
                typeGroup = "VOLUME"
        return (name, ref, typeGroup)
