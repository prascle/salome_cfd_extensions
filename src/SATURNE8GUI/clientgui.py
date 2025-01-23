# -*- coding: utf-8 -*-

import os
import logging
import traceback
import time

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMenu, QMessageBox, QDockWidget
from PyQt5.QtCore import Qt, QObject

import salome
from salome.smesh import smeshBuilder
# from qtsalome import QMenu

from code_saturne.base import cs_package


from .CLSMainWindow import CLSMainWindow
from .CLSMainWindow import getSalomePyQt
from .CLSMainWindow import col
from .utilstudy import DumpMesh
#from .SATURNE8_DataModel import SATURNE8_DataModel
from .CFDSTUDYGUI_Commons import CheckCFD_CodeEnv, CFD_Saturne
from .CFDSTUDYGUI_Message import cfdstudyMess
from .CFDSTUDYGUI_ActionsHandler import CFDSTUDYGUI_ActionsHandler

salome.salome_init()


_clientGui = None


def getClientGui():
    """
    access to the singleton instance of gui, created at first call
    """
    global _clientGui
    if _clientGui is None:
        logging.info("begin clientGui instanciate")
        _clientGui = ClientGui()
        logging.info("clientGui instanciated!")
    return _clientGui


def getSaturne8ViewType():
    return "Saturne8Workspace"


def BoundaryGroup():
    """
    Get a group name, its reference and type ("VOLUME", "FACE", "EDGE")
    """
    logging.debug("BoundaryGroup")
    # entry = getClientGui().getCurrentEntry()
    clsmainw = getClientGui().getCLSMainWindow()
    return clsmainw.getNameAndRef()


class ClientGui():
    """
    SATURNE8 GUI SALOME Module
    """

    def __init__(self):
        """
        """
        logging.debug("__init__")
        self.smesh = None
        self.widget = None
        self.aboutToClose = False
        self._OCCViewer = 0
        self._VTKViewer = 0
        self._PVViewer = 0
        # self._dataModel = None
        self.ah = None

        self.mainWindow = None
        self.clsmainw = None
        self.view = None

        self.currentEntry = ""
        self.currentFile = ""
        self.selectedItem = None

        self.meshNames = {}  # mesh name from entry (without path and ext)
        self.meshPaths = {}  # entry from mesh path
        self.nbMesh = 0

        self.casesToReload = []

    def getVTKViewer(self):
        return self._VTKViewer

    def getActionsHandler(self):
        return self.ah

    def initialize(self):
        """
        """
        logging.debug("initialize")

        # ObjectTR is a convenient object for traduction purpose

        self.ObjectTR = QObject()
        DEFAULT_EDITOR_NAME = self.ObjectTR.tr("CFDSTUDY_PREF_EDITOR")
        DEFAULT_READER_NAME = self.ObjectTR.tr("CFDSTUDY_PREF_READER")
        DEFAULT_DISPLAY_VIEWER_NAME = self.ObjectTR.tr(
            "CFDSTUDY_PREF_DISPLAY_VIEWER")
        if not getSalomePyQt().hasSetting("SATURNE8", "ExternalEditor"):
            getSalomePyQt().addSetting("SATURNE8", "ExternalEditor", DEFAULT_EDITOR_NAME)
        if not getSalomePyQt().hasSetting("SATURNE8", "ExternalReader"):
            getSalomePyQt().addSetting("SATURNE8", "ExternalReader", DEFAULT_READER_NAME)
        if not getSalomePyQt().hasSetting("SATURNE8", "ExternalDisplay"):
            getSalomePyQt().addSetting("SATURNE8", "ExternalDisplay", DEFAULT_DISPLAY_VIEWER_NAME)

        # preload code_saturne package to handle configuration file

        cs_root_dir = os.getenv('CS_ROOT_DIR')
        if cs_root_dir == None:
            try:
                import inspect
                p = inspect.getfile(cs_package)
                d = os.path.split(p)
                while d[1] != 'lib':
                    d = os.path.split(d[0])
                    cs_root_dir = d[0]
            except Exception:
                pass

        if cs_root_dir != None:
            config_file = (os.path.join(cs_root_dir,
                                        'lib',
                                        'code_saturne_build.cfg'))
            try:
                pkg = cs_package.package(config_file=config_file)
            except Exception:   # for compatibility with older versions
                pass

        pass

    def initSmesh(self):
        logging.debug("initSmesh")
        if self.smesh is None:
            logging.debug("init smesh: get a smeshBuilder instance")
            self.smesh = smeshBuilder.New()
        if not self._VTKViewer:
            logging.debug("init VTK Viewer %s", self._VTKViewer)
            self.clsmainw.ui.tw_central.setCurrentIndex(2)
            self._VTKViewer = getSalomePyQt().createView("VTKViewer", True, 0, 0, True)
            logging.debug("VTK Viewer: %s", self._VTKViewer)
            vtkwidget = getSalomePyQt().getViewWidget(self._VTKViewer)
            self.clsmainw.ui.gl_mesh.removeWidget(
                self.clsmainw.ui.wd_viewSmesh)
            self.clsmainw.ui.gl_mesh.addWidget(vtkwidget, 0, 0, 1, 1)
            self.clsmainw.ui.tw_central.setCurrentIndex(1)

    def activate(self):
        """
        """
        logging.debug("activate")
        views = getSalomePyQt().findViews(getSaturne8ViewType())
        if views:
            logging.debug("views found %s", views)
            getSalomePyQt().setViewVisible(views[0], True)
            view = views[0]
        else:
            self.mainWindow = getSalomePyQt().getDesktop()
            self.clsmainw = CLSMainWindow(self.mainWindow)
            view = getSalomePyQt().createView(getSaturne8ViewType(),
                                              self.clsmainw)
            logging.debug("create view %s", view)
            getSalomePyQt().setViewClosable(view, False)
            getSalomePyQt().setViewTitle(view, "Saturne workspace")
            self.clsmainw.initContextMenus(self.treeItemMenuMgr)
        logging.debug("activate view: %s", view)
        getSalomePyQt().activateView(view)
        self.clsmainw.setVisible(True)
        self.view = view
        self.clsmainw.ui.tw_central.setCurrentIndex(1)
        if self._VTKViewer:
            logging.debug(
                "activateViewManagerAndView VTK Viewer: %s", self._VTKViewer)
            getSalomePyQt().activateViewManagerAndView(self._VTKViewer)
        getSalomePyQt().enableSelector()
        # self.clsmainw.ui.pb_createLoadCase.clicked.connect(
        #     self.createOrLoadCase)
        self.initSmesh()
        if self.ah is None:
            self.ah = CFDSTUDYGUI_ActionsHandler()
            self.ah.createActions()
        # if self._dataModel is None:
        #     self._dataModel = SATURNE8_DataModel()
        # self._dataModel.findOrCreateObject("une entree bidon")
        # values = self._dataModel.getSaturne8Studies()
        # logging.debug(values)

        # if len(self.casesToReload) and self.widget is None:  # when reload study
        #     # self.createOrLoadCase(True)
        #     i = 0
        #     for case in self.casesToReload:
        #         if i == 0:
        #             self.reloadCase(case)
        #             i += 1
        #         else:
        #             self.publishCase(case, "", "")
        #     self.casesToReload = []

        env_saturne, msg = CheckCFD_CodeEnv(CFD_Saturne)
        logging.debug("activate -> env_saturne = %s" % env_saturne)
        if not env_saturne:
            QMessageBox.critical(getSalomePyQt().getDesktop(),
                                 "Error", msg, QMessageBox.Ok, 0)
            return False

        if msg != "":
            mess = cfdstudyMess.trMessage(self.ObjectTR.tr(
                "CFDSTUDY_INVALID_ENV"), []) + " ; " + msg
            cfdstudyMess.aboutMessage(msg)
            return False
        else:
            self.ah.DialogCollector.InfoDialog.setCode(env_saturne)
        self.ah.setSolverParentWidget(self.clsmainw.ui.tw_case)
        self.ah._SalomeSelection.currentSelectionChanged.connect(
            self.ah.updateActions)
        self.ah.connectSolverGUI()

        return True

    def closeStudy(self):
        self.aboutToClose = True

    def isAboutToClose(self):
        return self.aboutToClose

    def deactivate(self):
        """
        """
        global _clientGui
        logging.debug("deactivate")
        view = getSalomePyQt().findViews(getSaturne8ViewType())
        if view:
            getSalomePyQt().setViewVisible(view[0], False)
        getSalomePyQt().disableSelector()
        if self.isAboutToClose():
            _clientGui = None

    def save(self):
        """
        """
        logging.debug("save")

    def load(self):
        """
        """
        logging.debug("load")

    def close(self):
        """
        """
        logging.debug("close")

    def OnGUIEvent(self, commandID):
        """
        """
        logging.debug("OnGUIEvent: %s", commandID)

    def onSelectionUpdated(self, entryList):
        """
        """
        logging.debug("onSelectionUpdated %s", entryList)
        self.clsmainw.externSelectionChanged(entryList)

    # def loadfile(self):
    #     """
    #     """
    #     logging.debug("loadfile")

    # def savefile(self):
    #     """
    #     """
    #     logging.debug("savefile")

    def saveFiles(self, directory, url):
        logging.debug("saveFiles %s %s", directory, url)
        from .CFDSTUDYGUI_DataModel import getCFDTW
        filename = os.path.join(directory, os.path.splitext(
            os.path.basename(url))[0]) + "_SATURNE8.txt"
        getCFDTW().saveFile(filename)
        return os.path.basename(filename)

    def openFiles(self, files, url):
        logging.debug("openFiles %s %s", files, url)
        filename = os.path.join(*files)
        self.loadFile(filename)
        return True

    def loadFile(self, filename):
        '''
        Read text file and publish it.
        '''
        logging.debug("loadFile %s", filename)
        with open(filename,  mode='r', encoding='utf-8') as f:
            for line in f:
                case = line.split()[0]
                logging.debug("case: %s", case)
                self.casesToReload.append(case)
        return True

    # def updateSaturneTitle(self):
    #     logging.debug("updateSaturneTitle")
    #     if self.widget is not None:
    #         aTitle = self.widget.windowTitle()
    #         self.clsmainw.ui.lbl_droite.setText(aTitle)

    # def publishCase(self, CaseName, meshCond, meshRay):
    #     """
    #     """
    #     logging.debug("publishCase: %s %s %s", CaseName, meshCond, meshRay)
    #     self.clsmainw.addSaturneItem(CaseName, meshCond, meshRay)
    #     entry = self._dataModel.findOrCreateObject(CaseName)
    #     logging.debug("entry %s", entry)

    # def closeWelcomeDialog(self):
    #     """
    #     check use case utility of this
    #     """
    #     logging.debug("closeWelcomeDialog")
    #     if self.widget is not None:
    #         self.widget.close()

    # def unloadCase(self, caseName):
    #     """
    #     """
    #     logging.debug("unloadCase %s", caseName)
    #     if self.widget is not None:
    #         identik = self.widget.SavingCompare()
    #         if identik == False:
    #             reply = QtWidgets.QMessageBox.question(self, 'Message', "Do you want to save the current data file ?",
    #                                                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No |
    #                                                    QtWidgets.QMessageBox.Cancel)
    #             if reply == QtWidgets.QMessageBox.Yes:
    #                 self.widget.SavingFile()
    #             elif reply == QtWidgets.QMessageBox.Cancel:
    #                 return
    #         self.widget.New_File()

    # def reloadCase(self, caseName):
    #     """
    #     """
    #     logging.debug("reloadCase %s", caseName)
    #     if self.widget is not None:
    #         logging.debug("OpeningFile %s", caseName)
    #         self.widget.OpeningFile(caseName, getSalomePyQt().getDesktop())

    def importMedMesh(self, fileMed):
        """
        Import a mesh from a med file into SMESH and display the mesh,
        or just display the mesh if the med file is already loaded

        :param path fileMed: med file path

        :return: mesh entry in study
        :rtype: string
        """
        logging.debug("importMedMesh %s", fileMed)
        if not fileMed:
            return ""
        entryMesh = ""
        # --- if the mesh entry is already known, do nothing
        if fileMed in self.meshPaths.keys():
            entryMesh = self.meshPaths[fileMed]
        else:
            name = os.path.splitext(os.path.basename(fileMed))[0]
            # --- when reopening a study, the mesh is maybe already loaded
            found = False
            lso = salome.myStudy.FindObjectByName(name, "MESH")
            for sobject in lso:
                medFileInfo = sobject.GetObject().GetMesh().GetMEDFileInfo()
                existingFileMed = medFileInfo.fileName
                logging.debug("Med file already in study %s", existingFileMed)
                if existingFileMed == fileMed:
                    found = True
            if found:
                logging.debug("mesh already in study: %s", name)
                entryMesh = sobject.GetID()
            else:
                self.initSmesh()
                ([aMesh], status) = self.smesh.CreateMeshesFromMED(fileMed)
                medFileInfo = aMesh.GetMesh().GetMEDFileInfo()
                logging.debug("medFileInfo %s", medFileInfo)
                self.smesh.SetName(aMesh.GetMesh(), name)
            self.clsmainw.ui.tw_central.setCurrentIndex(1)
            liste = DumpMesh(name, fileMed)
            logging.debug("mesh published %s", liste)
            entryMesh = liste[0][1]
            logging.debug("entryMesh %s", entryMesh)
            self.meshPaths[fileMed] = entryMesh
            self.meshNames[entryMesh] = name
            self.clsmainw.detailsMeshGroups(fileMed, self.selectedItem, liste)
        logging.debug("entryMesh %s", entryMesh)
        return entryMesh

    # def currentViewType(self):
    #     cv = getSalomePyQt().getActiveView()
    #     vtype = getSalomePyQt().getViewType(cv)
    #     logging.debug("view id and type: %s %s", cv, vtype)
    #     return vtype

    # def actUnloadCase(self):
    #     """
    #     """
    #     logging.debug("menu unload case %s", self.currentFile)
    #     self.unloadCase(self.currentFile)

    # def actReloadCase(self):
    #     """
    #     """
    #     logging.debug("menu reload case %s", self.currentFile)
    #     self.reloadCase(self.currentFile)

    # def actLoadMesh(self):
    #     """
    #     """
    #     logging.debug("actLoadMesh %s", self.currentFile)
    #     self.importMedMesh(self.currentFile)

    # def actShow(self):
    #     """
    #     """
    #     logging.debug("menu show %s %s", self.currentEntry, self.currentFile)
    #     entry = self.currentEntry
    #     fileMed = self.currentFile
    #     getSalomePyQt().activateViewManagerAndView(self._VTKViewer)
    #     if fileMed:
    #         entryMesh = self.importMedMesh(fileMed)
    #         salome.sg.Display(entryMesh)
    #     elif entry:
    #         salome.sg.Display(entry)
    #     salome.sg.FitAll()

    # def actShowOnly(self):
    #     """
    #     """
    #     logging.debug("menu show only%s %s",
    #                   self.currentEntry, self.currentFile)
    #     entry = self.currentEntry
    #     fileMed = self.currentFile
    #     getSalomePyQt().activateViewManagerAndView(self._VTKViewer)
    #     if fileMed:
    #         entryMesh = self.importMedMesh(fileMed)
    #         salome.sg.DisplayOnly(entryMesh)
    #     if entry:
    #         salome.sg.DisplayOnly(entry)
    #     salome.sg.FitAll()

    # def actHide(self):
    #     """
    #     """
    #     logging.debug("menu hide %s", self.currentEntry)
    #     entry = self.currentEntry
    #     if entry:
    #         isVisible = salome.sg.IsInCurrentView(entry)
    #         logging.debug("isInCurrentView %s, %s", entry, isVisible)
    #         logging.debug(" hide mesh %s", entry)
    #         salome.sg.Erase(entry)

    # def actFitAll(self):
    #     logging.debug("menu FitAll %s", self.currentEntry)
    #     salome.sg.FitAll()

    # def actResetView(self):
    #     logging.debug("menu ResetView %s", self.currentEntry)
    #     salome.sg.ResetView()

    def getTWSelectedItems(self):
        return self.clsmainw.ui.tw_gauche.selectedItems()

    def treeItemMenuMgr(self, position):
        """
        Defines all the specific actions related to each item of the tree
        """
        logging.debug("treeItemMenuMgr")
        menu = QMenu()
        self.currentEntry = ""
        self.currentFile = ""
        self.selectedItem = None
        items = self.clsmainw.ui.tw_gauche.selectedItems()
        if len(items) > 0:
            item = items[0]
            self.selectedItem = item
            self.ah.customPopup(item, menu)
        menu.exec_(self.clsmainw.ui.tw_gauche.viewport().mapToGlobal(position))

    # def getCurrentEntry(self):
    #     return self.currentEntry

    def getCLSMainWindow(self):
        return self.clsmainw
