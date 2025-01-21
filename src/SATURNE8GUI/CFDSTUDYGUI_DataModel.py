# -*- coding: utf-8 -*-

#-------------------------------------------------------------------------------

# This file is part of Code_Saturne, a general-purpose CFD tool.
#
# Copyright (C) 1998-2022 EDF S.A.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51 Franklin
# Street, Fifth Floor, Boston, MA 02110-1301, USA.

#-------------------------------------------------------------------------------

"""
Data Model
==========
Definitions of the function that allow to represent the CFC studies in a
tree representation.

SALOME data structure
---------------------
SALOMEDS (SALOME data structure) is a library that provides support for a multi-component
document of SALOME platform. Components can use SALOMEDS to publish their data inside a SALOMEDS
document (Study object). Publishing the data in a common document gives the following advantages
for a custom component:

 - the data becomes available for other components (for processing, visualization, etc.),
   it can accessed using SALOMEDS tools and services;

 - the data becomes automatically persistent (can be saved and restored), as persistence is
   already implemented in SALOMEDS library.

SALOMEDS also provides the mechanism of data persistence for components that do not publish
their data in a common SALOMEDS data structure. This mechanism is described in Implementing
persistence section of the tutorial. Briefly, SALOMEDS provides the following: a component
saves its data in arbitiary format to an external file and returns the name of this file
to SALOMEDS. SALOMEDS serializes this file into a binary stream and includes it into the common
Study file on save operation. When the data must be restored, exactly the same file is created
by SALOMEDS for the component, and the component itself is responsible for loading it.

SALOME Study
------------

A SALOME platform document that contains data of multiple components. The data is organized in
a tree-like structure within the Study. SALOMEDS library supports persistence of Study.
Every branch of the tree is represented by an SObject.

WARNING: a SALOME Study should not be confused with a CFD study.
"""

#-------------------------------------------------------------------------------
# Standard modules
#-------------------------------------------------------------------------------
import os
import re
import string
import logging
import subprocess

#-------------------------------------------------------------------------------
# Third-party modules
#-------------------------------------------------------------------------------

from code_saturne.gui.base.QtCore    import *
from code_saturne.gui.base.QtWidgets import *
from PyQt5.QtGui import QIcon

from omniORB import CORBA

#-------------------------------------------------------------------------------
# Salome modules
#-------------------------------------------------------------------------------
from omniORB import CORBA
from LifeCycleCORBA import LifeCycleCORBA
import SALOMEDS
import SALOMEDS_Attributes_idl

import SMESH
import salome

#-------------------------------------------------------------------------------
# Application modules
#-------------------------------------------------------------------------------

from .CFDSTUDYGUI_Commons import CFD_Code, BinCode, Trace, sg
from .CFDSTUDYGUI_Commons import CaseInProcessStart, CaseInProcessEnd
from .CFDSTUDYGUI_Commons import CFD_Saturne, CFD_Neptune
from . import CFDSTUDYGUI_SolverGUI
from . import CFDSTUDYGUI_Commons
from .CFDSTUDYGUI_CommandMgr import runCommand
from .CFDSTUDYGUI_Message import cfdstudyMess
from .constants import col
from code_saturne.base.cs_exec_environment import separate_args

#-------------------------------------------------------------------------------
# Module name. Attribut "AttributeName" for the related SObject.
#-------------------------------------------------------------------------------

__MODULE_NAME__ = "SATURNE8"
__MODULE_ID__   = 10000
__OBJECT_ID__   = 10010

#-------------------------------------------------------------------------------
# Definition of the type of objects for representation in the Object Browser.
# Attribut "AttributeLocalID" for the related SObject.
#-------------------------------------------------------------------------------

dict_object = {}

dict_object["CFDSTUDY"]      = 101000
dict_object["OtherFile"]     = 100000
dict_object["OtherFolder"]   = 100001
dict_object["Study"]         = 100002
dict_object["Case"]          = 100003
dict_object["CaseInProcess"] = 100004

dict_object["DATAFolder"]             = 100010
dict_object["REFERENCEDATAFolder"]    = 100011
dict_object["REFERENCEDATAFile"]      = 100012
dict_object["DATAFile"]               = 100013
dict_object["DRAFTFolder"]            = 100014
dict_object["DATADRAFTFile"]          = 100015
dict_object["DATAPyFile"]             = 100016

dict_object["DATARunConf"]            = 100017
dict_object["DATALaunch"]             = 100018
dict_object["DATAfileXML"]            = 100019

dict_object["SRCFolder"]          = 100020
dict_object["SRCFile"]            = 100021
dict_object["SRCDRAFTFile"]       = 100022
dict_object["LOGSRCFile"]         = 100023
dict_object["USERSFolder"]        = 100024
dict_object["USRSRCFile"]         = 100025

dict_object["RESUSubErrFolder"]  = 100029
dict_object["RESUFolder"]     = 100030
dict_object["RESUFile"]       = 100031
dict_object["RESUSubFolder"]  = 100032
dict_object["RESSRCFolder"]   = 100033
dict_object["RESSRCFile"]     = 100034
dict_object["HISTFolder"]     = 100035
dict_object["HISTFile"]       = 100036
dict_object["PRETFolder"]     = 100037
dict_object["SUITEFolder"]    = 100038
dict_object["RESMEDFile"]     = 100039
dict_object["RESXMLFile"]     = 100040
dict_object["POSTPROFolder"]  = 100041
dict_object["RESENSIGHTFile"] = 100042
dict_object["RESUPNGFile"]    = 100043

dict_object["MESHFolder"]     = 100070
dict_object["MEDFile"]        = 100071
dict_object["DESFile"]        = 100072
dict_object["MESHFile"]       = 100073
dict_object["DATFile"]        = 100074
dict_object["CGNSFile"]       = 100075
dict_object["CcmFile"]        = 100076
dict_object["CaseFile"]       = 100077
dict_object["NeuFile"]        = 100078
dict_object["MSHFile"]        = 100079
dict_object["HexFile"]        = 100080
dict_object["UnvFile"]        = 100081
dict_object["SYRMESHFile"]    = 100082

dict_object["POSTFolder"]     = 100090
dict_object["POSTFile"]       = 100091

#Model objects for COUPLING with SYRTHES CODE
dict_object["CouplingFilePy"]           = 100100
dict_object["RESU_COUPLINGFolder"]      = 100101
dict_object["SYRCaseFolder"]            = 100102
dict_object["SyrthesFile"]              = 100103
dict_object["SyrthesSydFile"]           = 100104
dict_object["CouplingLauncher"]         = 100105
dict_object["RESU_COUPLINGSubFolder"]   = 100106
dict_object["RESUSubFolderSYR"]         = 100107
dict_object["SRCSYRFolder"]             = 100108
dict_object["USRSRCSYRFile"]            = 100109
dict_object["CouplingStudy"]            = 100110
dict_object["OpenSyrthesCaseFile"]      = 100111

dict_object["Display"]   = 100200
dict_object["Show"]      = 100201
dict_object["ShowOnly"]  = 100202
dict_object["Hide"]      = 100203
dict_object["FitAll"]    = 100204

d_dirMesh      = {}
MESHSubFolder = "MESHSubFolder"
MESHSubFolder_int = 200000

#-------------------------------------------------------------------------------
# Definition of the icon of objects to represent in the Object Browser.
# Attribut "AttributePixMap" for the related SObject.
#-------------------------------------------------------------------------------

icon_collection = {}

icon_collection[dict_object["CFDSTUDY"]]      = "CFDSTUDY_ICON"

icon_collection[dict_object["OtherFile"]]      = "CFDSTUDY_UNKNOWN_OBJ_ICON"
icon_collection[dict_object["OtherFolder"]]    = "CFDSTUDY_FOLDER_OBJ_ICON"
icon_collection[dict_object["Study"]]          = "CFDSTUDY_STUDY_OBJ_ICON"
icon_collection[dict_object["Case"]]           = "CFDSTUDY_CASE_OBJ_ICON"
icon_collection[dict_object["CaseInProcess"]]  = "CFDSTUDY_CASE_IN_PROC_OBJ_ICON"

icon_collection[dict_object["DATAFolder"]]     = "CFDSTUDY_FOLDER_OBJ_ICON"
icon_collection[dict_object["DATAFile"]]       = "CFDSTUDY_EDIT_DOCUMENT_OBJ_ICON"
icon_collection[dict_object["DATAPyFile"]]       = "CFDSTUDY_EDIT_DOCUMENT_OBJ_ICON"
icon_collection[dict_object["DRAFTFolder"]]    = "CFDSTUDY_FOLDER_OBJ_ICON"
icon_collection[dict_object["REFERENCEDATAFolder"]] = "CFDSTUDY_FOLDER_OBJ_ICON"

icon_collection[dict_object["DATADRAFTFile"]]  = "CFDSTUDY_EDIT_DOCUMENT_OBJ_ICON"

icon_collection[dict_object["REFERENCEDATAFile"]] = "CFDSTUDY_DOCUMENT_OBJ_ICON"

icon_collection[dict_object["DATARunConf"]]    = "CFDSTUDY_EDIT_DOCUMENT_OBJ_ICON"
icon_collection[dict_object["DATALaunch"]]     = "CFDSTUDY_EXECUTABLE_OBJ_ICON"
icon_collection[dict_object["DATAfileXML"]]    = "CFDSTUDY_DATA_XML_FILE_OBJ_ICON"

icon_collection[dict_object["SRCFolder"]]      = "CFDSTUDY_FOLDER_OBJ_ICON"
icon_collection[dict_object["SRCFile"]]        = "CFDSTUDY_EDIT_DOCUMENT_OBJ_ICON"
icon_collection[dict_object["SRCDRAFTFile"]]   = "CFDSTUDY_EDIT_DOCUMENT_OBJ_ICON"
icon_collection[dict_object["LOGSRCFile"]]     = "CFDSTUDY_DOCUMENT_OBJ_ICON"
icon_collection[dict_object["USERSFolder"]]    = "CFDSTUDY_FOLDER_OBJ_ICON"
icon_collection[dict_object["USRSRCFile"]]     = "CFDSTUDY_EDIT_DOCUMENT_OBJ_ICON"

icon_collection[dict_object["RESUFolder"]]     = "CFDSTUDY_FOLDER_OBJ_ICON"
icon_collection[dict_object["RESUFile"]]       = "CFDSTUDY_DOCUMENT_OBJ_ICON"
icon_collection[dict_object["RESUSubFolder"]]  = "CFDSTUDY_FOLDER_OBJ_ICON"
icon_collection[dict_object["RESUSubErrFolder"]]  = "CFDSTUDY_FOLDER_RED_OBJ_ICON"
icon_collection[dict_object["RESSRCFolder"]]   = "CFDSTUDY_FOLDER_OBJ_ICON"
icon_collection[dict_object["RESSRCFile"]]     = "CFDSTUDY_DOCUMENT_OBJ_ICON"
icon_collection[dict_object["HISTFolder"]]     = "CFDSTUDY_FOLDER_OBJ_ICON"
icon_collection[dict_object["HISTFile"]]       = "POST_FILE_ICON"
icon_collection[dict_object["PRETFolder"]]     = "CFDSTUDY_FOLDER_OBJ_ICON"
icon_collection[dict_object["SUITEFolder"]]    = "CFDSTUDY_FOLDER_OBJ_ICON"
icon_collection[dict_object["RESMEDFile"]]     = "VISU_OBJ_ICON"
icon_collection[dict_object["RESXMLFile"]]     = "CFDSTUDY_EXECUTABLE_OBJ_ICON"
icon_collection[dict_object["POSTPROFolder"]]  = "CFDSTUDY_FOLDER_OBJ_ICON"
icon_collection[dict_object["RESENSIGHTFile"]] = "VISU_OBJ_ICON"
icon_collection[dict_object["RESUPNGFile"]]    = "VIEW_ACTION_ICON"

icon_collection[dict_object["MESHFolder"]]     = "CFDSTUDY_FOLDER_OBJ_ICON"
icon_collection[dict_object["MEDFile"]]        = "MESH_OBJ_ICON"
icon_collection[dict_object["MESHFile"]]       = "CFDSTUDY_DOCUMENT_OBJ_ICON"
icon_collection[dict_object["DESFile"]]        = "MESH_OBJ_ICON"
icon_collection[dict_object["DATFile"]]        = "CFDSTUDY_EDIT_DOCUMENT_OBJ_ICON"
icon_collection[dict_object["CGNSFile"]]       = "MESH_OBJ_ICON"
icon_collection[dict_object["CcmFile"]]       = "MESH_OBJ_ICON"
icon_collection[dict_object["CaseFile"]]       = "MESH_OBJ_ICON"
icon_collection[dict_object["NeuFile"]]        = "MESH_OBJ_ICON"
icon_collection[dict_object["MSHFile"]]        = "MESH_OBJ_ICON"
icon_collection[dict_object["HexFile"]]        = "MESH_OBJ_ICON"
icon_collection[dict_object["UnvFile"]]        = "MESH_OBJ_ICON"
icon_collection[dict_object["SYRMESHFile"]]    = "MESH_OBJ_ICON"

icon_collection[dict_object["POSTFolder"]]     = "CFDSTUDY_FOLDER_OBJ_ICON"
icon_collection[dict_object["POSTFile"]]       = "CFDSTUDY_DOCUMENT_OBJ_ICON"

#Icons for coupling with SYRTHES CODE
icon_collection[dict_object["SYRCaseFolder"]]         = "SYRTHES_CASE_ICON"
icon_collection[dict_object["SyrthesFile"]]           = "CFDSTUDY_EDIT_DOCUMENT_OBJ_ICON"
icon_collection[dict_object["SyrthesSydFile"]]        = "CFDSTUDY_EDIT_DOCUMENT_OBJ_ICON"
icon_collection[dict_object["CouplingFilePy"]]        = "CFDSTUDY_EDIT_DOCUMENT_OBJ_ICON"
icon_collection[dict_object["CouplingLauncher"]]      = "CFDSTUDY_EDIT_DOCUMENT_OBJ_ICON"
icon_collection[dict_object["RESU_COUPLINGFolder"]]   = "CFDSTUDY_FOLDER_OBJ_ICON"
icon_collection[dict_object["RESU_COUPLINGSubFolder"]]= "CFDSTUDY_FOLDER_OBJ_ICON"
icon_collection[dict_object["RESUSubFolderSYR"]]      = "CFDSTUDY_FOLDER_OBJ_ICON"
icon_collection[dict_object["SRCSYRFolder"]]          = "CFDSTUDY_FOLDER_OBJ_ICON"
icon_collection[dict_object["USRSRCSYRFile"]]         = "CFDSTUDY_EDIT_DOCUMENT_OBJ_ICON"
icon_collection[dict_object["CouplingStudy"]]         = "CFDSTUDY_STUDY_OBJ_ICON"

_CFDTreeWidget = None

    
#-------------------------------------------------------------------------------
# ObjectTR is a convenient object for traduction purpose
#-------------------------------------------------------------------------------

ObjectTR = QObject()

#-------------------------------------------------------------------------------
# Internal methods
#-------------------------------------------------------------------------------

###
# Get ORB reference
###
__orb__ = None
def getORB():
    global __orb__
    if __orb__ is None:
        __orb__ = CORBA.ORB_init( [''], CORBA.ORB_ID )
        pass
    return __orb__

#--------------------------------------------------------------------------
###
# Get naming service instance
###
def getNS():
    import salome
    return salome.naming_service

#--------------------------------------------------------------------------
##
# Get life cycle CORBA instance
##
__lcc__ = None
def getLCC():
    global __lcc__
    if __lcc__ is None:
        __lcc__ = LifeCycleCORBA( getORB() )
        pass
    return __lcc__


#--------------------------------------------------------------------------
##
# Get study
###
__study__ = None
def _getStudy():
    global __study__
    if __study__ is None:
        obj = getNS().Resolve( '/Study' )
        __study__ = obj._narrow( SALOMEDS.Study )
        pass
    return __study__

#--------------------------------------------------------------------------
# __engine__ = None
# def _getEngine():
#     global __engine__
#     if __engine__ is None:
#         __engine__ = getLCC().FindOrLoadComponent( "FactoryServerPy", __MODULE_NAME__ )
#         pass
#     return __engine__


def _getNewBuilder():
    study   = _getStudy()
    builder = study.NewBuilder()
    return builder


def _getComponent():
    """
    Returns the component object if CFDSTUDY is active.

    @return: component object if CFDSTUDY is active.
    @rtype: C{Component} or C{None}
    """
    study = _getStudy()
    return study.FindComponent(__MODULE_NAME__)


# def _hasChildren(sobj):
#     """
#     Returns 1 if object has children.

#     @type sobj: C{SObject}
#     @param sobj: branch of the tree
#     @return: 1 if I{sobj} has children, 0 if not.
#     @rtype: C{int}
#     """
#     if sobj:
#         study = _getStudy()
#         iter  = study.NewChildIterator(sobj)
#         while iter.More():
#             name = iter.Value().GetName()
#             if name:
#                 return 1
#             iter.Next()
#     return 0


def _findOrCreateComponent():
    """
    Finds or creates component object, i.e. root of the tree.

    @return: the root C{SObject} for the Object browser representation.
    @rtype: C{SObject}
    """
    logging.debug("_findOrCreateComponent")
    study = _getStudy()
    father = study.FindComponent(__MODULE_NAME__)
    if father is None:
        builder = study.NewBuilder()
        father = builder.NewComponent(__MODULE_NAME__)
        attr = builder.FindOrCreateAttribute(father, "AttributeName")
        attr.SetValue(__MODULE_NAME__)
        attr = builder.FindOrCreateAttribute(father, "AttributeLocalID")
        attr.SetValue(__MODULE_ID__)
        attr = builder.FindOrCreateAttribute(father, "AttributePixMap")
        attr.SetPixMap("CFDSTUDY.png")

        # try:
        #     builder.DefineComponentInstance(father, _getEngine())
        # except:
        #     pass
    return father

def getCFDTW():
    global _CFDTreeWidget
    if _CFDTreeWidget is None:
        _CFDTreeWidget = CFDTreeWidget()
    return _CFDTreeWidget

def getQIcon(category):
    id = dict_object[category]
    iconPath = os.path.join(os.getenv("SATURNE8_ROOT_DIR"), 
                            "share/salome/resources/saturne8", 
                            ObjectTR.tr(icon_collection[id]))
    logging.debug("icon: %s %s", category, iconPath)
    return QIcon(iconPath)

def getTWIid(category):
    return dict_object[category]

class CFDTreeWidget():
    
    def __init__(self):
        from .clientgui import getClientGui
        from .CLSMainWindow import getSalomePyQt
        self.getClientGui = getClientGui
        self.getSalomePyQt = getSalomePyQt
        self.moduleFolder = self.getClientGui().getCLSMainWindow().getSaturneFolder()
        self.moduleFolder.setIcon(col.name, getQIcon("CFDSTUDY"))
        self.pathToTwi = {}
        self.entryToTwi = {}
        self.entryToSO = {}
        
    def getObjFromTwi(self, twItem):
        entry = twItem.text(col.entry)
        if entry in self.entryToSO:
            return self.entryToSO[entry]
        return None
    
    def getTwiFromEntry(self, entry):
        if entry in self.entryToTwi:
            return self.entryToTwi[entry]
        else:
            return None
        
    def getObjFromEntry(self, entry):
        if entry in self.entryToSO:
            return self.entryToSO[entry]
        else:
            return None

    def getTwiFromPath(self, path):
        twi = None
        if path in self.pathToTwi:
            twi = self.pathToTwi[path]
        return twi
    
    def removeObjFromTwi(self, baseTwi):
        """
        remove Salome Study object (CFD study, case, mesh folder)
        to be done before removeTwiWithChildren
        """
        baseEntry = baseTwi.text(col.entry)
        basePath = baseTwi.text(col.details)
        logging.debug("baseEntry %s %s", baseEntry, basePath)
        entriesToRemove = []
        if baseEntry:
            baseObj = self.getObjFromEntry(baseEntry)
            if baseObj:
                # "recursive" clean of entryToTwi and entryToSO before recursive remove of obj
                for entry in self.entryToSO:
                    logging.debug("entry %s", entry)
                    twi = self.getTwiFromEntry(entry)
                    path = twi.text(col.details)
                    if basePath in path:
                        entriesToRemove.append(entry)
                                      
            for entry in entriesToRemove:
                self.removeObject(entry)
            
    def removeTwiWithChildren(self, twItem):
        """
        recursive remove of Tree Widget Items
        to be done after removeObjFromTwi
        """
        basePath = twItem.text(col.details)
        logging.debug("removeTwiWithChildren %s", basePath)
        pathsToRemove = []
        for path in self.pathToTwi:
            # all the path to remove begin with basePath
            if basePath in path:
                pathsToRemove.append(path)
        for path in pathsToRemove:
            self.pathToTwi.pop(path)        
        parentTwi = twItem.parent()
        parentTwi.removeChild(twItem)

    def setIdAndIcon(self, twItem, category):
        """
        Fill the tree widget column id with the widget category
        (see dict_widget) and set the appropriate icon
    """
        twItem.setIcon(col.name, getQIcon(category))
        twItem.setText(col.id, str(getTWIid(category)))

    def getSaturne8Studies(self):
        '''
        Return the list of CFD Studies cases:
        Salome Study entries that are direct children of the module.
        '''
        # === Only with light Study objects (texts) ===
        logging.debug("get Module children in Salome Study (CFD Studies)")
        children = self.getSalomePyQt().getChildren()
        for child in children:
            logging.debug("child: %s", child)
        logging.debug("done")
        return children
        
    def findCFDStudyInSalomeStudy(self, text):
        logging.debug("findCFDStudyInSalomeStudy %s", text)
        studyEntries = self.getSaturne8Studies()
        for entry in studyEntries:
            if entry not in self.entryToSO:
                logging.critical(
                    "inconsistency: entry in SALOME study, under the Saturne8 module, not known")
                return ""
            studyObj = self.entryToSO[entry]
            studyPath = studyObj.getPath()
            logging.debug("entry: %s case: %s", entry, studyPath)
            if text == studyPath:
                return entry
        return ""

    def ScanChildrenObj(self, theObject, theRegExp):
        """
        Returns a list of children data from a parent branch data.
        The list of the children is filtered whith a regular expression.
        """
        logging.debug("ScanChildrenObj %s %s", theObject.GetName(), theObject.getEntry())
        ChildList = []
        childrenEntries = self.getSalomePyQt().getChildren(theObject.getEntry())
        for ch in childrenEntries:
            logging.debug("child entry: %s", ch)
            child = self.getObjFromEntry(ch)
            aName = child.GetName()
            if not aName == "" and re.match(theRegExp, aName):
                ChildList.append(child)
        return ChildList
    
    def getSObject(self, theParent,Name) :
        logging.debug("getSObject %s %s", theParent.GetName(), Name)
        Sobjlist = self.ScanChildrenObj(theParent,  ".*")
        SObj = None
        for i in Sobjlist :
            if i.GetName() == Name :
                SObj = i
        return SObj
   
    def findSOinSalomeStudy(self, thePath, parentSO):
        logging.debug("findSOinSalomeStudy")
        childrenSO = self.ScanChildrenObj(parentSO,  ".*")
        for childSO in childrenSO:
            #twItem = self.getTwiFromEntry(childSO.GetID())
            #path = twItem.text(col.details)
            if childSO.getPath() == thePath:
                return childSO
        return None
                
    def getObject(self, entry):
        '''
        Return SATURNE8_DataObject by its entry.
        '''
        logging.debug("getObject")
        obj = None
        if entry in self.entryToSO:
            obj = self.entryToSO[entry]
        return obj

    def findOrCreateStudySO(self, thePath):
        '''
        Find or create Salome Study Object for CFD study
        '''
        logging.debug("findOrCreateStudySO %s", thePath)
        entry = self.findCFDStudyInSalomeStudy(thePath)
        obj = None
        if not entry:
            logging.debug("create Salome study object for %s", thePath)
            obj = SATURNE8_DataObject(thePath, None)
            entry = obj.getEntry()
            self.entryToSO[entry] = obj
        else:
            obj = self.getObjFromEntry(entry)
        return obj
    
    def findOrCreateChildSO(self, name, parentSO):
        """
        Find or create Salome Study Object as a child of an SO 
        """
        logging.debug("findOrCreateChildSO: %s parentSO: %s", name, parentSO.GetName())
        childrenSO = self.ScanChildrenObj(parentSO,  ".*")
        for childSO in childrenSO:
            if childSO.GetName() == name:
                return childSO
        # not found, create
        thePath = os.path.join(parentSO.getPath(), name)
        logging.debug("create Salome study object for %s", thePath)
        obj = SATURNE8_DataObject(thePath, parentSO)
        entry = obj.getEntry()
        self.entryToSO[entry] = obj
        return obj
        
    def removeObject(self, entry):
        ''' 
        Remove object by its entry
        '''
        logging.debug("removeObject %s", entry)
        if entry in self.entryToSO:
            self.getSalomePyQt().removeObject(entry)
            self.entryToSO.pop(entry)
            self.entryToTwi.pop(entry)

    def saveFile(self, filename):
        """
        Write one line per Saturne8 case, with the full case path
        """
        logging.debug("saveFile %s", filename)
        with open(filename, mode='w', encoding='utf-8') as f:
            caseEntries = self.getSaturne8Studies()
            for entry in caseEntries:
                logging.debug("entry: %s", entry)
                caseObj = self.entryToSO[entry]
                casePath = caseObj.getPath()
                logging.debug("casePath %s", casePath)
                f.write(casePath + "\n")

    def findAncestorStudyItemFromSelected(self):
        """
        get the parent of the current selected tree widget item recursively
        until the corresponding CFD study item is found. 
        If a CFD study item is selected, it is returned.
        """
        cur = self.getClientGui().getCLSMainWindow().getCurrentSelectedItem()
        while cur:
            if cur.text(col.id) == str(dict_object["Study"]):
                return cur
            cur = cur.parent()
        logging.debug("************* outside Study ? *****************")
        return None    
    
    def findOrCreateStudyTWI(self, studyObject, studyPath):
        logging.debug("findOrCreateStudyTWI %s", studyPath)
        twiRoot = self.moduleFolder
        studyName = os.path.basename(studyPath) # = studyObject.GetName()
        # --- check if study is already in tree
        twiStudy = self.getTwiChildWithName(twiRoot, studyName)
        if twiStudy:
            return twiStudy
        # --- create  
        twiStudy = QTreeWidgetItem()
        twiStudy.setText(col.name, studyName)
        twiStudy.setText(col.details, studyPath)
        entry = studyObject.GetID()
        twiStudy.setText(col.entry, entry)
        self.setIdAndIcon(twiStudy, "Study")
        twiRoot.addChild(twiStudy)
        self.entryToTwi[entry] = twiStudy
        self.pathToTwi[studyPath] = twiStudy
        self.getClientGui().getCLSMainWindow().initialSelection(twiStudy)
        return twiStudy

    def findOrCreateCaseTWI(self, caseObject, twiStudy, casePath):
        logging.debug("findOrCreateCaseTWI %s", casePath)
        caseName = os.path.basename(casePath)
        # --- check if case is already in tree
        twiCase = self.getTwiChildWithName(twiStudy, caseName)
        if twiCase:
            return twiCase
        # --- create  
        twiCase = QTreeWidgetItem()
        twiCase.setText(col.name, caseName)
        twiCase.setText(col.details, casePath)
        entry = caseObject.GetID()
        twiCase.setText(col.entry, entry)
        self.setIdAndIcon(twiCase, "Case")
        twiStudy.addChild(twiCase)
        self.entryToTwi[entry] = twiCase
        self.pathToTwi[casePath] = twiCase
        return twiCase

    def findOrCreateMeshTWI(self, meshObject, twiStudy, meshPath):
        logging.debug("findOrCreateMeshTWI %s", meshPath)
        meshName = os.path.basename(meshPath)
        # --- check if Mesh is already in tree
        twiMesh = self.getTwiChildWithName(twiStudy, meshName)
        if twiMesh:
            return twiMesh
        # --- create  
        twiMesh = QTreeWidgetItem()
        twiMesh.setText(col.name, meshObject.GetName())
        twiMesh.setText(col.details, meshPath)
        entry = meshObject.GetID()
        twiMesh.setText(col.entry, entry)
        self.setIdAndIcon(twiMesh, "MESHFolder")
        twiStudy.addChild(twiMesh)
        self.entryToTwi[entry] = twiMesh
        self.pathToTwi[meshPath] = twiMesh
        return twiMesh

    def createTWItem(self, parentTWI, itemName, itemPath):
        logging.debug("createTWItem %s %s %s", itemPath, itemName, parentTWI.text(col.name))
        
        # TODO: first, find or create SALOME study objects for "Study", "case" and "MESH"
        
        twItem = QTreeWidgetItem()
        twItem.setText(col.name, itemName)
        twItem.setText(col.details, itemPath)
        self.pathToTwi[itemPath] = twItem
        
        # --- parent is study
        if parentTWI == self.findAncestorStudyItemFromSelected():
            studyObj = self.findOrCreateStudySO(parentTWI.text(col.details))
            if os.path.isdir(itemPath):
                if CFDSTUDYGUI_Commons.isaCFDCase(itemPath):
                    self.setIdAndIcon(twItem, "Case")
                    obj =self.findOrCreateChildSO(itemName,studyObj)
                    if obj:
                        entry = obj.GetID()
                        twItem.setText(col.entry, entry)
                        self.entryToTwi[entry] = twItem
                else:
                    boo = False
                    dirList = os.listdir(itemPath)
                    for i in dirList:
                        if re.match(".*\.syd$", i) or re.match(".*\.syd_example$", i):
                            boo = True
                    if boo :
                        self.setIdAndIcon(twItem, "SYRCaseFolder")
                    else:
                        if itemName == "MESH":
                            obj = self.findOrCreateChildSO("MESH",studyObj)
                            self.setIdAndIcon(twItem, "MESHFolder")
                        elif itemName == "POST":
                            self.setIdAndIcon(twItem, "POSTFolder")
                        else:
                            self.setIdAndIcon(twItem, "OtherFolder")   
            if itemName in ("code_saturne", "neptune_cfd", "runcase"):
                self.setIdAndIcon(twItem, "CouplingLauncher")
            elif itemName == "RESU_COUPLING":
                self.setIdAndIcon(twItem, "RESU_COUPLINGFolder")
                                        
        # --- parent is Syrthes Case
        elif parentTWI.text(col.id) == str(dict_object["SYRCaseFolder"]):
            if os.path.isdir(itemPath):
                if itemName == "usr_examples":
                    self.setIdAndIcon(twItem, "SRCSYRFolder")
            if itemName in ["Makefile","syrthes.py","user_cond.c"]:
                self.setIdAndIcon(twItem, "SyrthesFile")
            if re.match(".*\.syd$", itemName) or re.match(".*\.syd_example$", itemName) :
                self.setIdAndIcon(twItem, "SyrthesSydFile")
                
        # --- parent is Syrthes user examples
        elif parentTWI.text(col.id) == str(dict_object["SRCSYRFolder"]):
            if re.match(".*\.c$", itemName):
                self.setIdAndIcon(twItem, "USRSRCSYRFile")

        # --- parent is Case
        elif parentTWI.text(col.id) == str(dict_object["Case"]):
            if os.path.isdir(itemPath):
                if itemName == "DATA":
                    self.setIdAndIcon(twItem, "DATAFolder")
                elif itemName == "SRC":
                    self.setIdAndIcon(twItem, "SRCFolder")
                elif itemName == "RESU":
                    self.setIdAndIcon(twItem, "RESUFolder")
                else:
                    self.setIdAndIcon(twItem, "OtherFolder")

        # --- parent is DATA folder
        elif parentTWI.text(col.id) == str(dict_object["DATAFolder"]):
            if os.path.isdir(itemPath):
                if itemName == "REFERENCE":
                    self.setIdAndIcon(twItem, "REFERENCEDATAFolder")
                if itemName == "DRAFT":
                    self.setIdAndIcon(twItem, "DRAFTFolder")
            else:
                if itemName[0:12] == "code_saturne" or itemName[0:10] == "neptune_cfd":
                    # could use "DATALaunch" but prefer to hide this wrapper.
                    self.setIdAndIcon(twItem, "OtherFile")
                elif itemName[0:10] == "run.cfg":
                    self.setIdAndIcon(twItem, "DATARunConf")
                elif re.match("^dp_", itemName) or re.match("^meteo",itemName) or re.match("^cs_", itemName):
                    self.setIdAndIcon(twItem, "DATAFile")
                elif re.match(".*\.py$", itemName):
                    self.setIdAndIcon(twItem, "DATAPyFile")
                else:
                    if os.path.isfile(itemPath):
                        fd = os.open(itemPath , os.O_RDONLY)
                        try:
                            f = os.fdopen(fd)
                            l1 = f.readline()
                            if l1.startswith('''<?xml version="1.0" encoding="utf-8"?><Code_Saturne_GUI''') or l1.startswith('''<?xml version="1.0" encoding="utf-8"?><NEPTUNE_CFD_GUI'''):
                                self.setIdAndIcon(twItem, "DATAfileXML")
                            elif l1.startswith('''<?xml version="1.0" encoding="utf-8"?>''') :
                                l2 = f.readline()
                                if l2.startswith('''<Code_Saturne_GUI''') or l2.startswith('''<NEPTUNE_CFD_GUI'''):
                                    self.setIdAndIcon(twItem, "DATAfileXML")
                            else:
                                    self.setIdAndIcon(twItem, "DATAFile")
                            f.close()
                        except:
                            pass

        # --- parent is DRAFT folder
        elif parentTWI.text(col.id) == str(dict_object["DRAFTFolder"]):
            draftParentFolder = os.path.basename(parentTWI.parent().text(col.details.id))
            if os.path.isfile(itemPath):
                if draftParentFolder == "DATA":
                    if re.match("^dp_", itemName) or re.match("^meteo",itemName) or re.match("^cs_", itemName):
                        self.setIdAndIcon(twItem, "DATADRAFTFile")
                elif draftParentFolder == "SRC":
                    if re.match(".*\.[fF]$", itemName) or \
                        re.match(".*\.[fF]90$", itemName) or \
                        re.match(".*\.for$", itemName) or \
                        re.match(".*\.FOR$", itemName):
                        self.setIdAndIcon(twItem, "SRCDRAFTFile")
                    elif re.match(".*\.c$", itemName):
                        self.setIdAndIcon(twItem, "SRCDRAFTFile")
                    elif re.match(".*\.cxx$", itemName) or \
                        re.match(".*\.cpp$", itemName):
                        self.setIdAndIcon(twItem, "SRCDRAFTFile")
                    elif re.match(".*\.h$", itemName) or \
                        re.match(".*\.hxx$", itemName) or \
                        re.match(".*\.hpp$", itemName):
                        self.setIdAndIcon(twItem, "SRCDRAFTFile")
            elif os.path.isdir(itemPath):
                self.setIdAndIcon(twItem, "OtherFolder")

        # --- parent is REFERENCE folder into DATA folder
        elif parentTWI.text(col.id) == str(dict_object["REFERENCEDATAFolder"]):
            if os.path.isfile(itemPath):
                if re.match("^dp_", itemName) or re.match("^meteo",itemName) or re.match("^cs_", itemName):
                    self.setIdAndIcon(twItem, "REFERENCEDATAFile")
            elif os.path.isdir(itemPath):
                self.setIdAndIcon(twItem, "OtherFolder")

        # --- parent is MESH folder
        elif parentTWI.text(col.id) == str(dict_object["MESHFolder"]):
            if os.path.isdir(itemPath):
                # --- TODO: check!
                if d_dirMesh != {}:
                    for key in d_dirMesh:
                        if itemPath in d_dirMesh[key]:
                            for k,v in dict_object.items():
                                if v == key:
                                    self.setIdAndIcon(twItem, k)
                                    break
            else:
                if re.match(".*\.des$", itemName):
                    self.setIdAndIcon(twItem, "DESFile")
                elif re.match(".*\.med$", itemName):
                    self.setIdAndIcon(twItem, "MEDFile")
                elif re.match(".*\.dat$", itemName):
                    self.setIdAndIcon(twItem, "DATFile")
                elif re.match(".*\.cgns$", itemName):
                    self.setIdAndIcon(twItem, "CGNSFile")
                elif re.match(".*\.ccm$", itemName):
                    self.setIdAndIcon(twItem, "CcmFile")
                elif re.match(".*\.case$", itemName):
                    self.setIdAndIcon(twItem, "CaseFile")
                elif re.match(".*\.neu$", itemName):
                    self.setIdAndIcon(twItem, "NeuFile")
                elif re.match(".*\.msh$", itemName):
                    self.setIdAndIcon(twItem, "MSHFile")
                elif re.match(".*\.hex$", itemName):
                    self.setIdAndIcon(twItem, "HexFile")
                elif re.match(".*\.unv$", itemName):
                    self.setIdAndIcon(twItem, "UnvFile")
                elif re.match(".*\.syr$", itemName):
                    self.setIdAndIcon(twItem, "SYRMESHFile")
                else:
                    self.setIdAndIcon(twItem, "MESHFile")

        # --- parent is POST folder
        elif parentTWI.text(col.id) == str(dict_object["POSTFolder"]):
            if os.path.isdir(itemPath):
                self.setIdAndIcon(twItem, "OtherFolder")
            else:
                self.setIdAndIcon(twItem, "POSTFile")

        # --- parent is SRC folder
        elif parentTWI.text(col.id) == str(dict_object["SRCFolder"]):
            if os.path.isfile(itemPath):
                if re.match(".*\.[fF]$", itemName) or re.match(".*\.[fF]90$", itemName) \
                or re.match(".*\.for$", itemName) or re.match(".*\.FOR$", itemName):
                    self.setIdAndIcon(twItem, "SRCFile")
                elif re.match(".*\.c$", itemName):
                    self.setIdAndIcon(twItem, "SRCFile")
                elif re.match(".*\.cpp$", itemName) or re.match(".*\.cxx$", itemName):
                    self.setIdAndIcon(twItem, "SRCFile")
                elif re.match(".*\.h$", itemName) or re.match(".*\.hpp$", itemName) or re.match(".*\.hxx$", itemName):
                    self.setIdAndIcon(twItem, "SRCFile")
                elif re.match(".*\.log$", itemName):
                    self.setIdAndIcon(twItem, "LOGSRCFile")
            elif os.path.isdir(itemPath):
                if itemName == "REFERENCE" or itemName == "EXAMPLES" :
                    self.setIdAndIcon(twItem, "USERSFolder")
                elif itemName == "DRAFT":
                    self.setIdAndIcon(twItem, "DRAFTFolder")
                else:
                    self.setIdAndIcon(twItem, "OtherFolder")

        # --- parent REFERENCE/base... folder
        elif parentTWI.text(col.id) == str(dict_object["USERSFolder"]):
            if os.path.isfile(itemPath):
                if re.match(".*\.[fF]$", itemName) or re.match(".*\.[fF]90$", itemName) \
                or re.match(".*\.for$", itemName) or re.match(".*\.FOR$", itemName):
                    self.setIdAndIcon(twItem, "USRSRCFile")
                elif re.match(".*\.c$", itemName):
                    self.setIdAndIcon(twItem, "USRSRCFile")
                elif re.match(".*\.cpp$", itemName) or re.match(".*\.cxx$", itemName):
                    self.setIdAndIcon(twItem, "USRSRCFile")
                elif re.match(".*\.h$", itemName) or re.match(".*\.hpp$", itemName) or re.match(".*\.hxx$", itemName):
                    self.setIdAndIcon(twItem, "USRSRCFile")
                elif re.match(".*\.log$", itemName):
                    self.setIdAndIcon(twItem, "LOGSRCFile")
            elif os.path.isdir(itemPath):
                if itemName in ("atmo", "base", "cplv", "cfbl", "cogz", \
                            "ctwr", "elec", "fuel", "lagr", "pprt", "rayt"):
                    self.setIdAndIcon(twItem, "USERSFolder")
                else:
                    self.setIdAndIcon(twItem, "OtherFolder")

        # --- parent is RESU folder
        elif parentTWI.text(col.id) == str(dict_object["RESUFolder"]):
            if os.path.isdir(itemPath):
                if "error" in os.listdir(itemPath):
                    self.setIdAndIcon(twItem, "RESUSubErrFolder")
                else:
                    self.setIdAndIcon(twItem, "RESUSubFolder")

        # --- parent is RESULT SRC folder
        elif parentTWI.text(col.id) == str(dict_object["RESSRCFolder"]):
            if os.path.isfile(itemPath):
                if re.match(".*\.[fF]$", itemName) or re.match(".*\.[fF]90$", itemName) \
                or re.match(".*\.for$", itemName) or re.match(".*\.FOR$", itemName):
                    self.setIdAndIcon(twItem, "RESSRCFile")
                elif re.match(".*\.c$", itemName):
                    self.setIdAndIcon(twItem, "RESSRCFile")
                elif re.match(".*\.cpp$", itemName) or re.match(".*\.cxx$", itemName):
                    self.setIdAndIcon(twItem, "RESSRCFile")
                elif re.match(".*\.h$", itemName) or re.match(".*\.hpp$", itemName) or re.match(".*\.hxx$", itemName):
                    self.setIdAndIcon(twItem, "RESSRCFile")

        # --- parent is RESULT sub folder
        elif parentTWI.text(col.id) == str(dict_object["RESUSubFolder"]) or parentTWI.text(col.id) == str(dict_object["RESUSubErrFolder"]):
            if os.path.isdir(itemPath):
                if itemName == "src_neptune" or itemName == "src_saturne":
                    self.setIdAndIcon(twItem, "RESSRCFolder")
                elif itemName == "monitoring":
                    self.setIdAndIcon(twItem, "HISTFolder")
                elif itemName == "checkpoint":
                    self.setIdAndIcon(twItem, "SUITEFolder")
                elif itemName == "mesh_input":
                    self.setIdAndIcon(twItem, "PRETFolder")
                elif itemName == "partition_output":
                    self.setIdAndIcon(twItem, "PRETFolder")
                elif itemName == "postprocessing":
                    self.setIdAndIcon(twItem, "POSTPROFolder")
            else:
                if re.match(".*\.dat$", itemName) or re.match(".*\.csv$", itemName):
                    self.setIdAndIcon(twItem, "HISTFile")
                elif re.match(".*\.xml$", itemName):
                    self.setIdAndIcon(twItem, "RESXMLFile")
                elif re.match(".*\.log$", itemName):
                    self.setIdAndIcon(twItem, "RESUFile")
                elif re.match("listing$", itemName):
                    self.setIdAndIcon(twItem, "RESUFile")
                elif re.match("error$", itemName):
                    self.setIdAndIcon(twItem, "RESUFile")
                elif re.match(".*\.png$", itemName):
                    self.setIdAndIcon(twItem, "RESUPNGFile")

        # --- parent is POSTPRO folder
        elif parentTWI.text(col.id) == str(dict_object["POSTPROFolder"]):
            if os.path.isfile(itemPath):
                if re.match(".*\.med$", itemName):
                    self.setIdAndIcon(twItem, "RESMEDFile")
                if re.match(".*\.case$", itemName):
                    self.setIdAndIcon(twItem, "RESENSIGHTFile")

        # --- parent is HIST folder
        elif parentTWI.text(col.id) == str(dict_object["HISTFolder"]):
            if os.path.isfile(itemPath):
                if re.match(".*\.dat$", itemName) or re.match(".*\.csv$", itemName):
                    self.setIdAndIcon(twItem, "HISTFile")

        # --- parent is RESU_COUPLING folder
        elif parentTWI.text(col.id) == str(dict_object["RESU_COUPLINGFolder"]):
            if os.path.isdir(itemPath):
                self.setIdAndIcon(twItem, "RESU_COUPLINGSubFolder")

        # --- parent is RESU_COUPLING sub folder
        elif parentTWI.text(col.id) == str(dict_object["RESU_COUPLINGSubFolder"]):
            if os.path.isdir(itemPath):
                if os.path.isfile(os.path.join(itemPath,"syrthes")):
                    self.setIdAndIcon(twItem, "RESUSubFolderSYR")
                else:
                    # test if folder is a result cfd folder?
                    self.setIdAndIcon(twItem, "RESUSubFolder")

        elif parentTWI.text(col.id) == str(dict_object["RESUSubFolderSYR"]):
            if re.match(".*\.log$", itemName):
                self.setIdAndIcon(twItem, "RESUFile")
            if re.match(".*\.dat$", itemName):
                self.setIdAndIcon(twItem, "RESUFile")
            if re.match(".*\.rdt$", itemName):
                self.setIdAndIcon(twItem, "RESUFile")
            if re.match(".*\.res$", itemName):
                self.setIdAndIcon(twItem, "RESUFile")
            if re.match(".*\.syr$", itemName):
                self.setIdAndIcon(twItem, "RESUFile")
            if re.match(".*\.data$", itemName):
                self.setIdAndIcon(twItem, "RESUFile")
            if re.match(".*\.add$", itemName):
                self.setIdAndIcon(twItem, "RESUFile")
            if re.match(".*\.c$", itemName):
                self.setIdAndIcon(twItem, "RESUFile")
            elif re.match("listing$", itemName):
                self.setIdAndIcon(twItem, "RESUFile")

        # --- MESH sub folder
        if parentTWI.text(col.id) in d_dirMesh:
            if os.path.isdir(itemPath):
                if d_dirMesh != {}:
                    for key in d_dirMesh:
                        if itemPath in d_dirMesh[key]:
                            for k,v in dict_object.items():
                                if v == key:
                                    self.setIdAndIcon(twItem, k)
                                    break
            else:
                if re.match(".*\.des$", itemName):
                    self.setIdAndIcon(twItem, "DESFile")
                elif re.match(".*\.med$", itemName):
                    self.setIdAndIcon(twItem, "MEDFile")
                elif re.match(".*\.dat$", itemName):
                    self.setIdAndIcon(twItem, "DATFile")
                elif re.match(".*\.cgns$", itemName):
                    self.setIdAndIcon(twItem, "CGNSFile")
                elif re.match(".*\.ccm$", itemName):
                    self.setIdAndIcon(twItem, "CcmFile")
                elif re.match(".*\.case$", itemName):
                    self.setIdAndIcon(twItem, "CaseFile")
                elif re.match(".*\.neu$", itemName):
                    self.setIdAndIcon(twItem, "NeuFile")
                elif re.match(".*\.msh$", itemName):
                    self.setIdAndIcon(twItem, "MSHFile")
                elif re.match(".*\.hex$", itemName):
                    self.setIdAndIcon(twItem, "HexFile")
                elif re.match(".*\.unv$", itemName):
                    self.setIdAndIcon(twItem, "UnvFile")
                elif re.match(".*\.syr$", itemName):
                    self.setIdAndIcon(twItem, "SYRMESHFile")
                else:
                    self.setIdAndIcon(twItem, "MESHFile")


        if twItem.text(col.id) == str(dict_object["OtherFile"]):
            if re.match(".*\.[fF]$", itemName) or \
            re.match(".*\.[fF]90$", itemName) or \
            re.match(".*\.for$", itemName) or \
            re.match(".*\.FOR$", itemName):
                if self.detectUSERSitem(parentTWI):
                    logging.debug("****************************** %s", itemPath)
                    self.setIdAndIcon(twItem, self.detectSRCitem(parentTWI))
            elif re.match(".*\.c$", itemName):
                if self.detectUSERSitem(parentTWI):
                    logging.debug("****************************** %s", itemPath)
                    self.setIdAndIcon(twItem, self.detectSRCitem(parentTWI))
            elif re.match(".*\.cpp$", itemName) or \
                re.match(".*\.cxx$", itemName):
                if self.detectUSERSitem(parentTWI):
                    logging.debug("****************************** %s", itemPath)
                    self.setIdAndIcon(twItem, self.detectSRCitem(parentTWI))
            elif re.match(".*\.h$", itemName) or \
                re.match(".*\.hxx$", itemName) or \
                re.match(".*\.hpp$", itemName):
                if self.detectUSERSitem(parentTWI):
                    logging.debug("****************************** %s", itemPath)
                    self.setIdAndIcon(twItem, self.detectSRCitem(parentTWI))

        if twItem.text(col.id) == str(dict_object["OtherFile"]):
            if os.path.isdir(itemPath):
                self.setIdAndIcon(twItem, "OtherFolder")
                
        parentTWI.addChild(twItem)
        return twItem
            
    def rebuildTWRecursively(self, twItem):
        """
        Compare the children (if any) of the tree item with the content of the
        corresponding folder on the disk.
        Create the items corresponding to new files or directories on the disk,
        remove the items corresponding to files or directories that are no more
        on the disk.
        """
        # --- find the path corresponding to the current item. 
        #     Do not consider items with no path (for instance, mesh groups).
        
        itemPath = twItem.text(col.details)
        logging.debug("rebuildTWRecursively %s", itemPath)
        if itemPath is None:
            return
        
        # --- if the item path exists and is a directory, get the names of the files on disk in this directory
        lst = []
        if os.path.isdir(itemPath):
            lst = os.listdir(itemPath)
        lst.sort()
        
        # --- get the paths of children of the item
        nbChildren = twItem.childCount()
        childPaths = {}
        for i in range(nbChildren):
            itm = twItem.child(i)
            pth = itm.text(col.details)
            if pth:
                childPaths[pth] = itm
        
        # --- find the new paths on disk, create the corresponding tree items as new children of the current item
        for aName in lst:
            aPath = os.path.join(itemPath, aName)
            if aPath not in childPaths:
                nc = self.createTWItem(twItem, aName, aPath)
        
        # --- find the items corresponding to files or directories no longer present on the disk and are removed
        #     only the items coresponding to a file or directory are taken into account,
        #     (the items corresponding to mesh groups have no path, and are not removed)
        for pth, itm in childPaths.items():
            aName = os.path.basename(pth)
            if aName not in lst:
                itmPth = itm.text(col.details)
                if itmPth:
                    self.removeObjFromTwi(itm)       # remove SALOME Objects first (recursive)
                    self.removeTwiWithChildren(itm)  # then remove tree widget items (recursive)

        # --- recursive call with the updated children of the item 
        nbChildren = twItem.childCount()
        for i in range(nbChildren):
            itm = twItem.child(i)
            self.rebuildTWRecursively(itm)
        logging.debug("rebuildTWRecursively %s END", itemPath)

    def detectUSERSitem(self, twItem):
        """
        Search if the branch containing twItem represents the USERS folder.
        """
        cur = twItem
        while cur:
            if cur.text(col.id) == str(dict_object["USERSFolder"]):
                return True
            elif cur.text(col.id) == str(dict_object["Study"]):
                return False
            cur = cur.parent()
        logging.debug("outside Study ? ")
        return False

    def detectSRCitem(self, twItem):
        """
        Returns the type of the branch twItem which represents
        the files in the SRC folder.
        """
        cur = twItem
        while cur:
            if cur.text(col.id) == str(dict_object["SRCFolder"]):
                return "USRSRCFile"
            cur = cur.parent()
        logging.debug("outside Study ?")
        return "USRSRCFile"
    
    def findCaseItem(self, twItem):
        cur = twItem
        while cur:
            if cur.text(col.id) == str(dict_object["Case"]):
                return cur
            cur = cur.parent()
        logging.debug("************* outside Case ? *****************")
        return cur
    
    def findStudyItem(self, twItem):
        cur = twItem
        while cur:
            if cur.text(col.id) == str(dict_object["Study"]):
                return cur
            cur = cur.parent()
        logging.debug("*** outside Study  ? ***")
        return cur

    def getTwiChildWithName(self, parentTwi, name):
        """
        explore the children of a parent TreeWidget Item
        to find one with the given name
        """
        nbChildren = parentTwi.childCount()
        for i in range(nbChildren) :
            child = parentTwi.child(i)
            if child.text(col.name) == name:
                return child
        return None

    def _SetStudyLocation(self, theStudyPath, theCaseName,theCreateOpt,
                        theCopyOpt, theNameRef = "", theSyrthesOpt =False, theSyrthesCase = "",theNprocs=""):
        """
        Constructs the tree representation of a CFD study (with the
        associated cases) for the Object Browser. Only the CFD Studies and cases are 
        stored in SALOME study, with their path
        """
        logging.debug("_SetStudyLocation %s %s", theStudyPath, theCaseName)

        iok = True
        if theCopyOpt:
            if not os.path.exists(theNameRef):
                raise ValueError("reference case is not a repository")
        if os.path.exists(theStudyPath) :

            if theCreateOpt:
                mess = cfdstudyMess.trMessage(ObjectTR.tr("STUDY_DIRECTORY_ALREADY_EXISTS"),[""])
                cfdstudyMess.criticalMessage(mess)
                return False
        if theCreateOpt or (not theCreateOpt and theCaseName!=""):
            iok = _CallCreateScript(theStudyPath, theCreateOpt, theCaseName,
                                    theCopyOpt, theNameRef, theSyrthesOpt, theSyrthesCase)

        studyObject = self.FindStudyObjectByPath(theStudyPath)
        twiStudy = None
        if studyObject is None:
            studyObject = self.findOrCreateStudySO(theStudyPath)
            twiStudy = self.findOrCreateStudyTWI(studyObject, theStudyPath)
        else:
            twiStudy = self.entryToTwi[studyObject.GetID()]
        
        self.getClientGui().getCLSMainWindow().initialSelection(twiStudy)
        if theCaseName:
            # --- find or create case SO 
            theCasePath = os.path.join(theStudyPath, theCaseName)
            caseObject = self.FindCaseByPath(theCasePath)
            if caseObject is None:
                caseObject = self.findOrCreateChildSO(theCaseName, studyObject)
            twiCase = self.findOrCreateCaseTWI(caseObject, twiStudy, theCasePath)
            self.rebuildTWRecursively(twiCase)
            
        self.UpdateSubTree(twiStudy)
            
        # TODO handle number of procs required in a consistant manner for coupled cases
        # Better handled using models/BatchRunningModel
        # if "run.cfg" in os.listdir(theStudyPath) and theCreateOpt:
        #     if theNprocs != "":
        #         pass


        return iok

    def _SetCaseLocation(self, theCasePath):
        logging.debug("_SetCaseLocation %s", theCasePath)        
        theStudyPath  = os.path.dirname(theCasePath)
        theCaseName   = os.path.basename(theCasePath)
        studyObject   = self.FindStudyObjectByPath(theStudyPath)
        if studyObject is None:
            if CFDSTUDYGUI_Commons.isaCFDStudy(theStudyPath):
                studyObject = self.findOrCreateStudySO(theStudyPath)
                twiStudy = self.findOrCreateStudyTWI(studyObject, theStudyPath)
            else:
                logging.critical("the study path %s does not correspond to a CFD study...")
                return
        else:
            twiStudy = self.entryToTwi[studyObject.GetID()]                
        if theCaseName:
            # --- find or create case SO 
            theCasePath = os.path.join(theStudyPath, theCaseName)
            caseObject = self.FindCaseByPath(theCasePath)
            if caseObject is None:
                caseObject = self.findOrCreateChildSO(theCaseName, studyObject)
            twiCase = self.findOrCreateCaseTWI(caseObject, twiStudy, theCasePath)
            self.rebuildTWRecursively(twiCase)
        if self.getSObject(studyObject,"MESH") == None:
            meshPath = os.path.join(theStudyPath, "MESH")
            meshObject = self.findOrCreateChildSO("MESH", studyObject)
            twiMesh = self.findOrCreateMeshTWI(meshObject, twiStudy, meshPath)
            self.rebuildTWRecursively(twiMesh)
        self.getClientGui().getCLSMainWindow().expandTree()        
    
    def FindStudyObjectByPath(self, theStudyPath):
        """
        Return the SALOME Study object (SO) representing 
        the CFD study described by its path on disk
        """
        logging.debug("FindStudyByPath %s", theStudyPath)
        studySO = None
        if theStudyPath in self.pathToTwi:
            twItem = self.pathToTwi[theStudyPath]
            if twItem.text(col.id) == str(dict_object["Study"]):
                studySO = self.getObjFromTwi(twItem)
        return studySO

    def FindCaseByPath(self, theCasePath):
        """
        Return the SALOME Study object (SO) representing 
        the CFD case described by its path on disk
        """
        logging.debug("FindCaseByPath %s", theCasePath)
        caseSO = None
        if theCasePath in self.pathToTwi:
            twItem = self.pathToTwi[theCasePath]
            if twItem.text(col.id) == str(dict_object["Case"]):
                caseSO = self.getObjFromTwi(twItem)
        return caseSO

    def UpdateSubTree(self, twItem):
        """
        Update recursively Tree Widget from the given item
        """
        logging.debug("UpdateSubTree")
        if twItem:
            getCFDTW().rebuildTWRecursively(twItem)
            self.getClientGui().getCLSMainWindow().expandTree()

    def GetCaseNameList(self,studyItem):
        """
        Returns the list of the existing cases names from a CFD study in the Object Browser.
        Used into slotAddCase to verify the existing cases
        """
        CaseList = []
        nbChildren = studyItem.childCount()
        for i in range(nbChildren):
            child = studyItem.child(i)
            if child.text(col.id) == str(dict_object["Case"]):
                CaseList.append(child.text(col.name))
        return CaseList

    def GetCaseList(self, studyItem):
        """
        Returns the list of the existing cases (tree widget items) from a CFD study in the Object Browser.
        """
        CaseList = []
        nbChildren = studyItem.childCount()
        for i in range(nbChildren):
            child = studyItem.child(i)
            if child.text(col.id) == str(dict_object["Case"]):
                CaseList.append(child)
        return CaseList


def FindCaseByPath(theCasePath):
    """
    Returns a CFD study described by the unix path I{theCasePath}.

    @type theCasePath: C{String}
    @param theCasePath: unix path of the CFD study.
    @return: the CFD study.
    @rtype: C{SObject} or C{None}
    """
    logging.debug("FindCaseByPath")
    component = _getComponent()
    if component == None:
        return None

    study = _getStudy()
    builder = study.NewBuilder()
    studyCfdObject = FindStudyByPath(os.path.dirname(theCasePath))
    iter  = study.NewChildIterator(studyCfdObject)
    while iter.More():
        attr = builder.FindOrCreateAttribute(iter.Value(), "AttributeLocalID")
        if attr.Value() == dict_object["Case"]:
            #compare case path
            aCurCasePath = _GetPath(iter.Value())
            if aCurCasePath == theCasePath:
                return iter.Value()
        iter.Next()

    return None


def _CallCreateScript(theStudyPath, isCreateStudy, theCaseNames,
                      theCopyOpt, theNameRef, theSyrthesOpt, theSyrthesCase):
    """
    Builds new CFD study, and/or new cases on the file system.

    @type theStudyPath: C{String}
    @param theStudyPath: unix path of the CFD study.
    @type isCreateStudy: C{True} or C{False}
    @param isCreateStudy: if C{True} build the new CFD study, if C{False}, only cases have to be build.
    @type theCaseNames: C{String}
    @param theCaseNames: unix pathes of the new CFD cases to be build.
    """
    logging.debug("_CallCreateScript")
    mess = ""
    scrpt, c ,mess = BinCode()
    if mess == "" :
        curd = os.getcwd()

        start_dir = ""
        if isCreateStudy:
            fatherdir,etude = os.path.split(theStudyPath)
            start_dir = fatherdir
        else:
            start_dir = theStudyPath

        args = [scrpt]
        args.append('create')

        if isCreateStudy:
            args.append("--study")
            args.append(theStudyPath)
        if theCaseNames != "":
            for i in theCaseNames.split(' '):
                args.append("--case")
                args.append(os.path.join(theStudyPath,i))
        if theCopyOpt:
            args.append("--copy-from")
            args.append(theNameRef)

        if theSyrthesOpt:
            args.append("--syrthes")
            args.append(os.path.join(theStudyPath,theSyrthesCase))

        runCommand(args, start_dir, "")

    else:
        cfdstudyMess.criticalMessage(mess)
    return mess == ""

def updateCasePath(theCasePath):

    logging.debug("updateCasePath")
    mess = ""
    scrpt, c ,mess = BinCode()
    if mess == "" :
        curd = os.getcwd()

        start_dir = ""
        args = [scrpt]
        args.append('create')
        args.append(theCasePath)
        args.append('--import-only')
        runCommand(args, start_dir, "")
    else:
        cfdstudyMess.criticalMessage(mess)
    return mess == ""


            

# def closeCFDStudyTree(theObject):
#     """
#     Close a CFD Study from the Object browser
#     """
#     logging.debug("closeCFDStudyTree")
#     # TODO : check usage
#     # if theObject == None:
#     #     return
#     # study   = _getStudy()
#     # builder = study.NewBuilder()
#     # builder.RemoveObjectWithChildren(theObject)
#     return


def _CreateObject(theFather, theBuilder, theName):
    """
    Creates a child branch in the tree from the father branch I{theFather}.
    Sets the AttributeName value of this new child with the name theName of the child object
    Calls _FillObject which sets the AttributeLocalID of the child
    _FillObject calls _setIcon which sets the AttributePixMap and AttributeComment of the child object

    Result : an object entry in the Object Browser with AttributeName, AttributeLocalID, AttributePixMap, AttributeComment
    @type theFather: C{SObject}
    @param theFather: branch of the tree to add a child.
    @type theBuilder: C{SUIT_Study}
    @param theBuilder: C{SObject} constructor.
    @type theName: C{String}
    @param theName: AttributeName of the new child branch.
    """
    logging.debug("_CreateObject: %s" % theName)
    newChild = theBuilder.NewObject(theFather)
    attr = theBuilder.FindOrCreateAttribute(newChild, "AttributeName")
    attr.SetValue(theName)
    _FillObject(newChild, theFather, theBuilder)
    return newChild


# def _CreateItem(theFather,theNewName) :
#     """
#     Creates a child with name theNewName under theFather root into Object Browser
#     @type theFather: C{SObject}
#     @type theNewName : C{String}
#     """
#     logging.debug("_CreateItem: NewItem = %s with Parent = %s" % (theNewName,theFather.GetName()))
#     if theNewName not in ScanChildNames(theFather,  ".*") :
#         theBuilder = _getNewBuilder()
#         newChild = _CreateObject(theFather, theBuilder, theNewName)
#         return newChild
#     return None


def getNameCodeFromXmlCasePath(XMLCasePath) :
    """
    """
    logging.debug("getNameCodeFromXmlCasePath")
    code = ""
    if os.path.isfile(XMLCasePath):
        fd = os.open(XMLCasePath,os.O_RDONLY)
        f = os.fdopen(fd)
        l1 = f.readline()
        if l1.startswith('''<?xml version="1.0" encoding="utf-8"?><Code_Saturne_GUI''') or l1.startswith('''<?xml version="1.0" encoding="utf-8"?><NEPTUNE_CFD_GUI'''):
            if "Code_Saturne" in l1 :
                code = "Code_Saturne"
            elif "NEPTUNE_CFD" in l1 :
                code = "NEPTUNE_CFD"
        elif l1.startswith('''<?xml version="1.0" encoding="utf-8"?>''') :
            l2 = f.readline()
            if l2.startswith('''<Code_Saturne_GUI''') or l2.startswith('''<NEPTUNE_CFD_GUI'''):
                if "Code_Saturne" in l2 :
                    code = "Code_Saturne"
                elif "NEPTUNE_CFD" in l2 :
                    code = "NEPTUNE_CFD"
            else :
                mess = cfdstudyMess.trMessage(ObjectTR.tr("XML_DATA_FILE"),[XMLCasePath])
                cfdstudyMess.warningMessage(mess)
        else :
            mess = cfdstudyMess.trMessage(ObjectTR.tr("XML_DATA_FILE"),[XMLCasePath])
            cfdstudyMess.warningMessage(mess)
        f.close()
    return code


def searchDepth(directory):
    l = []
    l = directory.split(str(os.sep))
    niveau = 0
    for i in list(reversed(range(len(l)-1))):
        if l[i] == "MESH":
            niveau = len(l)-1-i
            return len(l)-1-i
    return niveau


def parseDir(dirname):
    """
    External method which permits to return a directory whose keys are objectId for the salome study and value is a list of MESH sub-directories to see then into Object Browser, to access to the med or other extensions mesh files
    """
    global d_dirMesh
    niveau = 0
    for root,dirs,files in os.walk(dirname):
        l_dirs = []
        if dirs != []:
            for j in dirs:
                l_dirs.append(os.path.join(root,j))
            niveau = searchDepth(root)+1
            key = MESHSubFolder_int+niveau
            if key not in list(d_dirMesh.keys()):
                d_dirMesh[key] = l_dirs
                dict_object[MESHSubFolder+str(niveau)] = key
                icon_collection[dict_object[MESHSubFolder+str(niveau)]]  = "CFDSTUDY_FOLDER_OBJ_ICON"
            else:
                d_dirMesh[key] = d_dirMesh[key]+l_dirs


def _FillObject(theObject, theParent, theBuilder):
    """
    Creates the attribute "AttributeLocalID" for the branch I{theObject}.
    This attribute keeps the type of the I{theObject}.

    @type theObject: C{SObject}
    @param theObject: branch of the tree to add an attribut.
    @type theParent: C{SObject}
    @param theParent: parent of the branch I{theObject}.
    @type theBuilder: C{SUIT_Study}
    @param theBuilder: C{SObject} constructor for create an attribut.
    """
    logging.debug("_FillObject")
    attr = theBuilder.FindOrCreateAttribute(theParent, "AttributeLocalID")
    parentId = attr.Value()
    name = theObject.GetName()
    objectId = dict_object["OtherFile"]
    path = os.path.join(_GetPath(theParent), name)
    logging.debug("_FillObject Object Name : %s" % name)
    logging.debug("_FillObject Parent Name : %s" % theParent.GetName())
    # Parent is study
    if parentId == dict_object["Study"] or parentId == dict_object["CouplingStudy"]:
        if Trace(): print("_FillObject : parent is Study ", theParent.GetName())
        #check for case
        if os.path.isdir(path):
            if CFDSTUDYGUI_Commons.isaCFDCase(path):
                objectId = dict_object["Case"]
            else:
                boo = False
                dirList = os.listdir(path)
                for i in dirList:
                    if re.match(".*\.syd$", i) or re.match(".*\.syd_example$", i): boo = True
                if boo :
                    objectId = dict_object["SYRCaseFolder"]
                else:
                    if name == "MESH":
                        objectId = dict_object["MESHFolder"]
                        parseDir(path)
                    elif name == "POST":
                        objectId = dict_object["POSTFolder"]
                    else:
                        objectId = dict_object["OtherFolder"]

        if name in ("code_saturne", "neptune_cfd", "runcase"):
            objectId = dict_object["CouplingLauncher"]
        elif name == "RESU_COUPLING":
            objectId = dict_object["RESU_COUPLINGFolder"]
    #parent is Syrthes Case
    elif parentId == dict_object["SYRCaseFolder"]:
        if os.path.isdir(path):
            if name == "usr_examples":
                objectId = dict_object["SRCSYRFolder"]
        if name in ["Makefile","syrthes.py","user_cond.c"]:
            objectId = dict_object["SyrthesFile"]
        if re.match(".*\.syd$", name) or re.match(".*\.syd_example$", name) :
            objectId = dict_object["SyrthesSydFile"]
    #parent is Syrthes user examples
    elif parentId == dict_object["SRCSYRFolder"]:
        if re.match(".*\.c$", name):
            objectId = dict_object["USRSRCSYRFile"]

    #parent is Case
    elif parentId == dict_object["Case"]:
        if os.path.isdir(path):
            if name == "DATA":
                objectId = dict_object["DATAFolder"]
            elif name == "SRC":
                objectId = dict_object["SRCFolder"]
            elif name == "RESU":
                objectId = dict_object["RESUFolder"]
            else:
                objectId = dict_object["OtherFolder"]

    # parent is DATA folder
    elif parentId == dict_object["DATAFolder"]:
        if os.path.isdir(path):
            if name == "REFERENCE":
                objectId = dict_object["REFERENCEDATAFolder"]
            if name == "DRAFT":
                objectId = dict_object["DRAFTFolder"]
        else:
            if name[0:12] == "code_saturne" or name[0:10] == "neptune_cfd":
                 # could use "DATALaunch" but prefer to hide this wrapper.
                objectId = dict_object["OtherFile"]
            elif name[0:10] == "run.cfg":
                objectId = dict_object["DATARunConf"]
            elif re.match("^dp_", name) or re.match("^meteo",name) or re.match("^cs_", name):
                objectId = dict_object["DATAFile"]
            elif re.match(".*\.py$", name):
                objectId = dict_object["DATAPyFile"]
            else:
                if os.path.isfile(path):
                    fd = os.open(path , os.O_RDONLY)
                    try:
                        f = os.fdopen(fd)
                        l1 = f.readline()
                        if l1.startswith('''<?xml version="1.0" encoding="utf-8"?><Code_Saturne_GUI''') or l1.startswith('''<?xml version="1.0" encoding="utf-8"?><NEPTUNE_CFD_GUI'''):
                            objectId = dict_object["DATAfileXML"]
                        elif l1.startswith('''<?xml version="1.0" encoding="utf-8"?>''') :
                            l2 = f.readline()
                            if l2.startswith('''<Code_Saturne_GUI''') or l2.startswith('''<NEPTUNE_CFD_GUI'''):
                                objectId = dict_object["DATAfileXML"]
                        else:
                                objectId = dict_object["DATAFile"]
                        f.close()
                    except:
                        pass

    # parent is DRAFT folder
    elif parentId == dict_object["DRAFTFolder"]:
        draftParentFolder = os.path.basename(_GetPath(theParent.GetFather()))
        if os.path.isfile(path):
            if draftParentFolder == "DATA":
                if re.match("^dp_", name) or re.match("^meteo",name) or re.match("^cs_", name):
                    objectId = dict_object["DATADRAFTFile"]
            elif draftParentFolder == "SRC":
                if re.match(".*\.[fF]$", name) or \
                    re.match(".*\.[fF]90$", name) or \
                    re.match(".*\.for$", name) or \
                    re.match(".*\.FOR$", name):
                    objectId = dict_object["SRCDRAFTFile"]
                elif re.match(".*\.c$", name):
                    objectId = dict_object["SRCDRAFTFile"]
                elif re.match(".*\.cxx$", name) or \
                     re.match(".*\.cpp$", name):
                    objectId = dict_object["SRCDRAFTFile"]
                elif re.match(".*\.h$", name) or \
                     re.match(".*\.hxx$", name) or \
                     re.match(".*\.hpp$", name):
                    objectId = dict_object["SRCDRAFTFile"]
        elif os.path.isdir(path):
            objectId = dict_object["OtherFolder"]

    # parent is REFERENCE folder into DATA folder
    elif parentId == dict_object["REFERENCEDATAFolder"]:
        if os.path.isfile(path):
            if re.match("^dp_", name) or re.match("^meteo",name) or re.match("^cs_", name):
                objectId = dict_object["REFERENCEDATAFile"]
        elif os.path.isdir(path):
            objectId = dict_object["OtherFolder"]

    # parent is MESH folder
    elif parentId == dict_object["MESHFolder"]:
        if os.path.isdir(path):
            if d_dirMesh != {}:
                for key in list(d_dirMesh.keys()):
                    if path in d_dirMesh[key]:
                        objectId = key
        else:
            if re.match(".*\.des$", name):
                objectId = dict_object["DESFile"]
            elif re.match(".*\.med$", name):
                objectId = dict_object["MEDFile"]
            elif re.match(".*\.dat$", name):
                objectId = dict_object["DATFile"]
            elif re.match(".*\.cgns$", name):
                objectId = dict_object["CGNSFile"]
            elif re.match(".*\.ccm$", name):
                objectId = dict_object["CcmFile"]
            elif re.match(".*\.case$", name):
                objectId = dict_object["CaseFile"]
            elif re.match(".*\.neu$", name):
                objectId = dict_object["NeuFile"]
            elif re.match(".*\.msh$", name):
                objectId = dict_object["MSHFile"]
            elif re.match(".*\.hex$", name):
                objectId = dict_object["HexFile"]
            elif re.match(".*\.unv$", name):
                objectId = dict_object["UnvFile"]
            elif re.match(".*\.syr$", name):
                objectId = dict_object["SYRMESHFile"]
            else:
                objectId = dict_object["MESHFile"]

    # parent is POST folder
    elif parentId == dict_object["POSTFolder"]:
        if os.path.isdir(path):
            objectId = dict_object["OtherFolder"]
        else:
            objectId = dict_object["POSTFile"]

    # parent is SRC folder
    elif parentId == dict_object["SRCFolder"]:
        if os.path.isfile(path):
            if re.match(".*\.[fF]$", name) or re.match(".*\.[fF]90$", name) \
              or re.match(".*\.for$", name) or re.match(".*\.FOR$", name):
                objectId = dict_object["SRCFile"]
            elif re.match(".*\.c$", name):
                objectId = dict_object["SRCFile"]
            elif re.match(".*\.cpp$", name) or re.match(".*\.cxx$", name):
                objectId = dict_object["SRCFile"]
            elif re.match(".*\.h$", name) or re.match(".*\.hpp$", name) or re.match(".*\.hxx$", name):
                objectId = dict_object["SRCFile"]
            elif re.match(".*\.log$", name):
                objectId = dict_object["LOGSRCFile"]
        elif os.path.isdir(path):
            if name == "REFERENCE" or name == "EXAMPLES" :
                objectId = dict_object["USERSFolder"]
            elif name == "DRAFT":
                objectId = dict_object["DRAFTFolder"]
            else:
                objectId = dict_object["OtherFolder"]

    # parent REFERENCE/base... folder
    elif parentId == dict_object["USERSFolder"]:
        if os.path.isfile(path):
            if re.match(".*\.[fF]$", name) or re.match(".*\.[fF]90$", name) \
              or re.match(".*\.for$", name) or re.match(".*\.FOR$", name):
                objectId = dict_object["USRSRCFile"]
            elif re.match(".*\.c$", name):
                objectId = dict_object["USRSRCFile"]
            elif re.match(".*\.cpp$", name) or re.match(".*\.cxx$", name):
                objectId = dict_object["USRSRCFile"]
            elif re.match(".*\.h$", name) or re.match(".*\.hpp$", name) or re.match(".*\.hxx$", name):
                objectId = dict_object["USRSRCFile"]
            elif re.match(".*\.log$", name):
                objectId = dict_object["LOGSRCFile"]
        elif os.path.isdir(path):
            if name in ("atmo", "base", "cplv", "cfbl", "cogz", \
                        "ctwr", "elec", "fuel", "lagr", "pprt", "rayt"):
                objectId = dict_object["USERSFolder"]
            else:
                objectId = dict_object["OtherFolder"]

    # parent is RESU folder
    elif parentId == dict_object["RESUFolder"]:
        if os.path.isdir(path):
            if "error" in os.listdir(path):
                objectId = dict_object["RESUSubErrFolder"]
            else:
                objectId = dict_object["RESUSubFolder"]

    # parent is RESULT SRC folder
    elif parentId == dict_object["RESSRCFolder"]:
        if os.path.isfile(path):
            if re.match(".*\.[fF]$", name) or re.match(".*\.[fF]90$", name) \
              or re.match(".*\.for$", name) or re.match(".*\.FOR$", name):
                objectId = dict_object["RESSRCFile"]
            elif re.match(".*\.c$", name):
                objectId = dict_object["RESSRCFile"]
            elif re.match(".*\.cpp$", name) or re.match(".*\.cxx$", name):
                objectId = dict_object["RESSRCFile"]
            elif re.match(".*\.h$", name) or re.match(".*\.hpp$", name) or re.match(".*\.hxx$", name):
                objectId = dict_object["RESSRCFile"]

    # parent is RESULT sub folder
    elif parentId == dict_object["RESUSubFolder"] or parentId == dict_object["RESUSubErrFolder"]:
        if os.path.isdir(path):
            if name == "src_neptune" or name == "src_saturne":
                objectId = dict_object["RESSRCFolder"]
            elif name == "monitoring":
                objectId = dict_object["HISTFolder"]
            elif name == "checkpoint":
                objectId = dict_object["SUITEFolder"]
            elif name == "mesh_input":
                objectId = dict_object["PRETFolder"]
            elif name == "partition_output":
                objectId = dict_object["PRETFolder"]
            elif name == "postprocessing":
                objectId = dict_object["POSTPROFolder"]
        else:
            if re.match(".*\.dat$", name) or re.match(".*\.csv$", name):
                objectId = dict_object["HISTFile"]
            elif re.match(".*\.xml$", name):
                objectId = dict_object["RESXMLFile"]
            elif re.match(".*\.log$", name):
                objectId = dict_object["RESUFile"]
            elif re.match("listing$", name):
                objectId = dict_object["RESUFile"]
            elif re.match("error$", name):
                objectId = dict_object["RESUFile"]
            elif re.match(".*\.png$", name):
                objectId = dict_object["RESUPNGFile"]

    elif parentId == dict_object["POSTPROFolder"] :
        if os.path.isfile(path):
            if re.match(".*\.med$", name):
                objectId = dict_object["RESMEDFile"]
            if re.match(".*\.case$", name):
                objectId = dict_object["RESENSIGHTFile"]

    # parent is HIST folder
    elif parentId == dict_object["HISTFolder"]:
        if os.path.isfile(path):
            if re.match(".*\.dat$", name) or re.match(".*\.csv$", name):
                objectId = dict_object["HISTFile"]

    # parent is RESU_COUPLING folder
    elif parentId == dict_object["RESU_COUPLINGFolder"]:
        if os.path.isdir(path):
            objectId = dict_object["RESU_COUPLINGSubFolder"]

    # parent is RESU_COUPLING sub folder
    elif parentId == dict_object["RESU_COUPLINGSubFolder"]:
        if os.path.isdir(path):
            if os.path.isfile(os.path.join(path,"syrthes")):
                objectId = dict_object["RESUSubFolderSYR"]
            else:
                # test if folder is a result cfd folder?
                objectId = dict_object["RESUSubFolder"]

    elif parentId == dict_object["RESUSubFolderSYR"]:
        if re.match(".*\.log$", name):
            objectId = dict_object["RESUFile"]
        if re.match(".*\.dat$", name):
            objectId = dict_object["RESUFile"]
        if re.match(".*\.rdt$", name):
            objectId = dict_object["RESUFile"]
        if re.match(".*\.res$", name):
            objectId = dict_object["RESUFile"]
        if re.match(".*\.syr$", name):
            objectId = dict_object["RESUFile"]
        if re.match(".*\.data$", name):
            objectId = dict_object["RESUFile"]
        if re.match(".*\.add$", name):
            objectId = dict_object["RESUFile"]
        if re.match(".*\.c$", name):
            objectId = dict_object["RESUFile"]
        elif re.match("listing$", name):
            objectId = dict_object["RESUFile"]

#MESH sub folder
    if parentId in list(d_dirMesh.keys()):
        if os.path.isdir(path):
            if d_dirMesh != {}:
                for key in list(d_dirMesh.keys()):
                    if path in d_dirMesh[key]:
                        objectId = key
        else:
            if re.match(".*\.des$", name):
                objectId = dict_object["DESFile"]
            elif re.match(".*\.med$", name):
                objectId = dict_object["MEDFile"]
            elif re.match(".*\.dat$", name):
                objectId = dict_object["DATFile"]
            elif re.match(".*\.cgns$", name):
                objectId = dict_object["CGNSFile"]
            elif re.match(".*\.ccm$", name):
                objectId = dict_object["CcmFile"]
            elif re.match(".*\.case$", name):
                objectId = dict_object["CaseFile"]
            elif re.match(".*\.neu$", name):
                objectId = dict_object["NeuFile"]
            elif re.match(".*\.msh$", name):
                objectId = dict_object["MSHFile"]
            elif re.match(".*\.hex$", name):
                objectId = dict_object["HexFile"]
            elif re.match(".*\.unv$", name):
                objectId = dict_object["UnvFile"]
            elif re.match(".*\.syr$", name):
                objectId = dict_object["SYRMESHFile"]
            else:
                objectId = dict_object["MESHFile"]


    if objectId == dict_object["OtherFile"]:
        if re.match(".*\.[fF]$", name) or \
           re.match(".*\.[fF]90$", name) or \
           re.match(".*\.for$", name) or \
           re.match(".*\.FOR$", name):
            if _DetectUSERSObject(theObject) == True:
                if Trace(): print("******************************", path)
                objectId = _DetectSRCObject(theParent)
        elif re.match(".*\.c$", name):
            if _DetectUSERSObject(theObject) == True:
                if Trace(): print("******************************", path)
                objectId = _DetectSRCObject(theParent)
        elif re.match(".*\.cpp$", name) or \
           re.match(".*\.cxx$", name):
            if _DetectUSERSObject(theObject) == True:
                if Trace(): print("******************************", path)
                objectId = _DetectSRCObject(theParent)
        elif re.match(".*\.h$", name) or \
           re.match(".*\.hxx$", name) or \
           re.match(".*\.hpp$", name):
            if _DetectUSERSObject(theObject) == True:
                if Trace(): print("******************************", path)
                objectId = _DetectSRCObject(theParent)

    if objectId == dict_object["OtherFile"]:
        if os.path.isdir(path):
            objectId = dict_object["OtherFolder"]

    logging.debug("_FillObject: %s %s" % \
        (name, [k for k, v in dict_object.items() if v == objectId][0]))

    if objectId in (dict_object["OtherFile"],
                    dict_object["OtherFolder"],
                    dict_object["MESHFile"],
                    dict_object["DATFile"]):
        study   = _getStudy()
        builder = study.NewBuilder()
        builder.RemoveObjectWithChildren(theObject)
        return

    attr = theBuilder.FindOrCreateAttribute(theObject, "AttributeLocalID")
    attr.SetValue(objectId)

    _SetIcon(theObject, theBuilder)


def _SetIcon(theObject, theBuilder):
    """
    Creates the attribute "AttributePixMap" and "AttributeComment" for the branch I{theObject}.

    @type theObject: C{SObject}
    @param theObject: branch of the tree to add an icon.
    @type theBuilder: C{SUIT_Study}
    @param theBuilder: C{SObject} constructor for create an attribut.
    """
    attr = theBuilder.FindOrCreateAttribute(theObject, "AttributeLocalID")
    id = int(attr.Value())
    if icon_collection[id] == "":
        return
    attr = theBuilder.FindOrCreateAttribute(theObject, "AttributePixMap")
    attr.SetPixMap(str(ObjectTR.tr(icon_collection[id])))
    #check path for link and create new attribute
    if id != dict_object["Case"]:
        path = _GetPath(theObject)
        if os.path.islink(path):
            attr = theBuilder.FindOrCreateAttribute(theObject, "AttributeComment")
            attr.SetValue("->" + os.path.realpath(path))


def _GetPath(theObject):
    """
    Returns the unix path of the branch I{theObject}.
    """
    name = None
    if theObject:
        name = theObject.getName()
        logging.debug("_GetPath %s", name)
        return theObject.getPath()
    else:
        logging.debug("_GetPath None")
        return
    
    # # check for null object
    # # check object from others component
    # # check if CFDSTUDY component object

    # if _getComponent() == None:
    #     return ""

    # if not theObject or \
    #        theObject.GetFatherComponent().GetID() != _getComponent().GetID() or \
    #        theObject.GetID() == _getComponent().GetID():
    #     return ""

    # study   = _getStudy()
    # builder = study.NewBuilder()
    # path = str(theObject.GetName())
    # attr = builder.FindOrCreateAttribute(theObject, "AttributeLocalID")
    # if attr.Value() == dict_object["Study"] or attr.Value() == dict_object["CouplingStudy"]:
    #     dir = builder.FindOrCreateAttribute(theObject, "AttributeComment")
    #     return os.path.join(dir.Value(), path)

    # father = theObject.GetFather()
    # attr = builder.FindOrCreateAttribute(father, "AttributeLocalID")
    # path = os.path.join(_GetPath(father), path)

    # return path


def _GetDirList(theObject):
    """
    Returns the unix pathes of the directories which are child of the branch I{theObject}.

    @type theObject: C{SObject}
    @param theObject: branch of the tree.
    @return: list of unix pathes of directory.
    @rtype: C{List} of C{String}
    """
    study   = _getStudy()
    builder = study.NewBuilder()

    path = _GetPath(theObject)
    attr = builder.FindOrCreateAttribute(theObject, "AttributeLocalID")
    lst = []
    if os.path.isdir(path):
        lst = os.listdir(path)
    lst.sort()
    return lst


def _DetectUSERSObject(theObject):
    """
    Search if the branch I{theObject} represents the USERS folder.

    @type theObject: C{SObject}
    @param theObject: branch of the tree.
    @return: C{True} if the I{theObject} represents the USERS folder
    @rtype: C{True} or C{False}
    """
    study   = _getStudy()
    builder = study.NewBuilder()
    cur = theObject.GetFather()
    attr = builder.FindOrCreateAttribute(cur, "AttributeLocalID")

    while True:
        if attr.Value() == dict_object["USERSFolder"]:
            return True
        elif attr.Value() == dict_object["Study"]:
            return False

        cur = cur.GetFather()
        attr = builder.FindOrCreateAttribute(cur, "AttributeLocalID")

    return False


def _DetectSRCObject(theObject):
    """
    Returns the type of the branch I{theObject} which represents
    the files in the SRC folder.

    @type theObject: C{SObject}
    @param theObject: branch of the tree.
    @return: type of the I{theObject} which represents files in the SRC folder.
    @rtype: C{int}
    """
    study   = _getStudy()
    builder = study.NewBuilder()
    cur = theObject.GetFather()
    attr = builder.FindOrCreateAttribute(cur, "AttributeLocalID")

    while True:
        if attr.Value() == dict_object["SRCFolder"]:
            return dict_object["USRSRCFile"]
        if attr.Value() == dict_object["SRCFolder"]:
            return dict_object["USRSRCFile"]

        cur = cur.GetFather()
        attr = builder.FindOrCreateAttribute(cur, "AttributeLocalID")

    return dict_object["USRSRCFile"]


# def GetCase(theObject):
#     """
#     Returns the case to which belongs the I{theObject}.

#     @type theObject: C{SObject}
#     @param theObject: file or folder we want to know the case.
#     @return: case to which belongs the I{theObject}.
#     @rtype: C{SObject}
#     """
#     if theObject == None:
#         return None

#     study   = _getStudy()
#     builder = study.NewBuilder()
#     cur = theObject

#     while cur:
#         attr = builder.FindOrCreateAttribute(cur, "AttributeLocalID")
#         if Trace():
#             print("attr:",attr)
#             print("Value for Case", attr.Value())
#         value = attr.Value()
#         if value == dict_object["Case"]:
#             return cur
#         elif value == dict_object["Study"] or value == dict_object["CouplingStudy"] \
#              or value == __MODULE_ID__ \
#              or value == 0:
#             return None

#         cur = cur.GetFather()

#     return None


def GetFirstStudy():
    """
    Returns the first CFD study loaded in the Object Browser.

    @return: first study of the tree.
    @rtype: C{SObject}
    """
    study = _getStudy()

    component = _getComponent()
    if component == None:
        return None

    iter  = study.NewChildIterator(component)
    return iter.Value()


def GetStudyByObj(theObject):
    """
    Returns the CFD study to which belongs the I{theObject}.

    @type theObject: C{SObject}
    @param theObject: file or folder we want to know the father's CFD study.
    @return: study to which belongs the I{theObject}.
    @rtype: C{SObject}
    """
    if theObject == None:
        return None

    study   = _getStudy()
    builder = study.NewBuilder()
    cur = theObject

    while cur:
        attr = builder.FindOrCreateAttribute(cur, "AttributeLocalID")
        value = attr.Value()
        if value == dict_object["Study"] or value == dict_object["CouplingStudy"]:
            return cur
        elif value == __MODULE_ID__ or value == 0:
            return None

        cur = cur.GetFather()

    return None



def getXmlCaseNameList(caseItem):
    """
    Returns a list of xml file names in the DATA folder of a case
    """
    aChildList = []
    aChildList = ScanChildren(caseItem, "^DATA$")
    if len(aChildList) != 1:
        # --- no DATA folder
        print("There are no data folder in selected by user case")
        return

    dataItem =  aChildList[0]
    aDataPath = dataItem.text(col.details)
    nbChildren = dataItem.childCount()
    XmlCaseNameList = []
    for i in range(nbChildren):
        childItem = dataItem.child(i)
        path = childItem.text(col.details)
        if "XML" in subprocess.check_output(["file", path]).decode():
            XmlCaseNameList.append(childItem.text(col.name))
    return XmlCaseNameList
    
def ScanChildren(twItem, theRegExp):
    """
    Returns a list of children data from a parent branch data.
    The list of the children is filtered whith a regular expression.
    """
    children = []
    nbChildren = twItem.childCount()
    for i in range(nbChildren):
        child = twItem.child(i)
        name = child.text(col.name)
        if re.match(theRegExp, name):
            children.append(child)
    return children


def ScanChildNames(theObject, theRegExp):
    """
    Returns a list of children data names from a parent branch data.
    The list of the children is filtered whith a regular expression.

    @type theObject: C{SObject}
    @param theObject: parent data.
    @type theRegExp: C{String}
    @param theRegExp: regular expression to filter children data.
    @return: list name of branch of children data.
    @rtype: C{list} of C{String}
    """
    NameList = []

    study   = _getStudy()
    builder = study.NewBuilder()

    iter  = study.NewChildIterator(theObject)

    while iter.More():
        aName = iter.Value().GetName()
        if not aName == "" and re.match(theRegExp, aName):
            NameList.append(aName)
        iter.Next()

    #log.debug("ScanChildNames: %s -> %s" % (theObject.GetName(), NameList))
    return NameList


def getType(theObject):
    if theObject == None:
        return None
    study   = _getStudy()
    builder = study.NewBuilder()
    attr = builder.FindOrCreateAttribute(theObject, "AttributeLocalID")
    return attr.Value()

# def hasTheSameType(ListObject):
#     if ListObject == []:
#         return False
#     typListBool = True
#     typListBoolRESUSub = None
#     typList = []
#     typ     = getType(list(ListObject)[0])
#     typList.append(typ)
#     if len(ListObject)> 1:
#         for SObject in list(ListObject)[1:]:
#             typListBool = typListBool and getType(SObject) == typ
#             typList.append(getType(SObject))
#         if not typListBool:
#             typListBoolRESUSub = True
#             for ty in typList:
#                 typListBoolRESUSub = typListBoolRESUSub and (ty == dict_object["RESUSubFolder"] or ty == dict_object["RESUSubErrFolder"] or ty == dict_object["RESU_COUPLINGSubFolder"])
#     if typListBoolRESUSub != None:
#         if typListBoolRESUSub == True:
#             return typListBoolRESUSub
#     else :
#         return typListBool

# def isACFDSTUDYListObject(ListObject):
#     if ListObject == []:
#         return False
#     typListBool = True
#     for sobj in ListObject :
#         typListBool = typListBool and sobj.GetFatherComponent().GetName() == "CFDSTUDY"
#     return typListBool

# def isASmeshListObject(ListObject):
#     if ListObject == []:
#         return False
#     typListBool = True
#     for sobj in ListObject :
#         if sobj.GetFatherComponent().GetName() == "Mesh":
#             if getMeshFromMesh(sobj) == None:
#                 meshGroupObject,group = getMeshFromGroup(sobj)
#                 typListBool = typListBool and meshGroupObject != None
#             else:
#                 typListBool = True
#         else:
#            return False
#     return typListBool

# def checkType(theObject, theType):
#     """
#     Checks if I{theObject} has the type ("AttributeLocalID") I{theType}.

#     @type theObject: C{SObject}
#     @param theObject: object from the Object Browser.
#     @type theType: C{String}
#     @param theType: type of the object in the Object Browser.
#     @rtype: C{True} or C{False}
#     @return: C{True} if C{theObject} has the type I{theType}.
#     """
#     if theObject == None or theType == None:
#         return False
#     if theObject != None and theType!= None :
#         return getType(theObject) == theType


# def checkPreMEDType(theObject):
#     """
#     Checks if I{theObject} is a mesh file, that can be converted to med format.

#     @type theObject: C{SObject}
#     @param theObject: object from the Object Browser.
#     @rtype: C{True} or C{False}
#     @return: C{True} if C{theObject} is a mesh file, that can be converted to med.
#     """
#     return checkType(theObject, dict_object["DESFile"]) or \
#            checkType(theObject, dict_object["CGNSFile"]) or \
#            checkType(theObject, dict_object["CcmFile"]) or \
#            checkType(theObject, dict_object["CaseFile"]) or \
#            checkType(theObject, dict_object["NeuFile"]) or \
#            checkType(theObject, dict_object["MSHFile"]) or \
#            checkType(theObject, dict_object["HexFile"]) or \
#            checkType(theObject, dict_object["UnvFile"])


def checkCaseLaunchGUI(theCase):
    """
    Checks if I{theCase} structure seems correct the DATA folder.

    @type theCase: C{SObject}
    @param theCase: object from the Object Browser.
    @rtype: C{True} or C{False}
    @return: C{True} if C{theCase} has the script to start GUI in the DATA folder.
    """
    
    caseItem = getCFDTW().getTwiFromEntry(theCase.GetID())
    if caseItem.text(col.id) != str(dict_object["Case"]):
        return False

    aChildList = ScanChildren(theCase, "^DATA$")
    if not len(aChildList) == 1:
        # no DATA folder
        print("There is no data folder in case selected by user")
        return False

    aDataObj =  aChildList[0]
    aDataPath = _GetPath(aDataObj)

    import sys
    is_case = False
    aChildList = ScanChildren(aDataObj, "^run.cfg$")
    if len(aChildList) == 1:
        is_case = True
    else:
        aChildList = ScanChildren(aDataObj, "^SRC$")
        if len(aChildList) == 1:
            is_case = True

    return is_case


# def checkCode(theCase):
#     """
#     Checks if I{theCase} is code_saturne or neptune_cfd.

#     @type theCase: C{SObject}
#     @param theCase: object from the Object Browser.
#     @rtype: C{CFD_Saturne} or C{CFD_Neptune}
#     @return: C{True} if C{theCase} has the script to start GUI in the DATA folder.
#     """

#     # TODO: this should be a feature od the code_saturne scripts
#     # (for exampe a sub-command of "code_saturne run" or code_saturne.info")

#     if not checkType(theCase, dict_object["Case"]):
#         return CFD_Code()

#     aChildList = ScanChildren(theCase, "^DATA$")
#     if not len(aChildList) == 1:
#         # no DATA folder
#         print("There is no data folder in selected case")
#         return CFD_Code()

#     aDataObj =  aChildList[0]
#     aDataPath = _GetPath(aDataObj)

#     # code_saturne is returned by default
#     # all xml files are read until NEPTUNE_CFD is found
#     # thus it will not work with a mix of saturne/neptune xml files

#     fileList = ScanChildren(aDataObj, "^.*$")

#     for ifile in fileList:
#         filePath = _GetPath(ifile)
#         if os.path.isfile(filePath):
#             fd = os.open(filePath,os.O_RDONLY)
#             f = os.fdopen(fd)
#             l1 = f.readline()
#             if l1.startswith('''<?xml version="1.0" encoding="utf-8"?><NEPTUNE_CFD_GUI'''):
#                 return CFD_Neptune
#             elif l1.startswith('''<?xml version="1.0" encoding="utf-8"?>''') :
#                 l2 = f.readline()
#                 if l2.startswith('''<NEPTUNE_CFD_GUI'''):
#                     return CFD_Neptune
#             f.close()

#     return CFD_Saturne


def isLinkPathItem(twItem):
    """
    Checks if the tree item represents a unix symbolic link.
    """
    if twItem:
        path = twItem.text(col.details)
        return os.path.islink(path)


def setCaseInProcess(theCasePath, isInProcess):
    """
    Udpates the case icon with I{Case} or I{CaseInProcess} in the Object Browser.

    @type theCasePath: C{String}
    @param theCasePath: absolute path of the case.
    @type isInProcess: C{True} or C{False}
    @param isInProcess: if C{True}, shows the I{CaseInProcess} icon.
    """
    logging.debug("setCaseInProcess")
    aStudyPath, aCaseName = os.path.split(theCasePath)
    aStudyObj = FindStudyByPath(aStudyPath)
    if not aStudyPath:
        if Trace():
            print("Study by case path not found")
        return

    #get case object
    lst = ScanChildren(aStudyObj, aCaseName)
    if len(lst) != 1:
        if Trace():
            print("Invalid number of cases under study")
        return

    aCaseObj = lst[0]

    study   = _getStudy()
    builder = study.NewBuilder()

    attr = builder.FindOrCreateAttribute(aCaseObj, "AttributePixMap")
    if isInProcess:
        attr.SetPixMap(str(ObjectTR.tr(icon_collection[dict_object["CaseInProcess"]])))
    else:
        attr.SetPixMap(str(ObjectTR.tr(icon_collection[dict_object["Case"]])))


#def getTwi(parentTwi, name):
    

#def publishInStudySalome(SO_father, objName, idElem):
    #"""
    #Publish objName into Object Browser under SO_father with the AttributeLocalID idElem
    #listPublishedId is used into PublishedIntoObjectBrowser method and caracterize entries
    #PublishedIntoObjectBrowser method adds entries into Salome Object Browser.
    #These entries do not provide from an Unix cfd study directory, and are idendified into the object browser
    #by a localId Attribute from the python list listPublishedId
    #"""
    #study = _getStudy()
    #builder = study.NewBuilder()
    #studyObject = builder.NewObject(SO_father)
    #attr = builder.FindOrCreateAttribute(studyObject, "AttributeName")
    #attr.SetValue(objName)
    #attr = builder.FindOrCreateAttribute(studyObject, "AttributeLocalID")
    #attr.SetValue(idElem)
    #_SetIcon(studyObject, builder)
    #log.debug("publishInStudySalome: %s" % ScanChildNames(SO_father,  ".*"))
    #return studyObject


def getOrLoadObject(item):
    """
    Get the CORBA object associated with the SObject `item`, eventually by
    first loading it with the corresponding engine.
    """
    object = item.GetObject()
    # if object is None: # the engine has not been loaded yet
    #     sComponent = item.GetFatherComponent()
    #     study   = _getStudy()
    #     builder = study.NewBuilder()
    #     engine = _getEngine()
    #     if engine is None:
    #         print("Cannot load component ", __MODULE_NAME__)
    #     object = item.GetObject()
    return object

def getMeshFromMesh(meshSobjItem) :
    """
    return: The SALOMEDS._objref_SObject instance of the mesh, if the meshSobjItem is a sobj of a mesh, None if not
    """
    meshItem = None
    obj = getOrLoadObject(meshSobjItem)
    if obj != None:
        mesh = obj._narrow(SMESH.SMESH_Mesh)
        if mesh != None:
            meshItem = salome.ObjectToSObject(mesh)
    return meshItem

def SetAutoColor(meshSobjItem) :
    obj = getOrLoadObject(meshSobjItem)
    if obj is not None:
        mesh = obj._narrow(SMESH.SMESH_Mesh)
        if mesh is not None:
            mesh.SetAutoColor(1)

def getMeshFromGroup(meshGroupItem):
    """
    Get the mesh item owning the mesh group `meshGroupItem`.

    :type   meshGroupItem: SObject
    :param  meshGroupItem: Mesh group belonging to the searched mesh.

    :return: The SALOMEDS._objref_SObject instance corresponding to the mesh group or None
             and SMESH._objref_SMESH_Group instance  or None if it was not
             found.
    """
    group = None
    meshItem = None
    obj = getOrLoadObject(meshGroupItem)

    if obj is not None:
        group = obj._narrow(SMESH.SMESH_GroupBase)
        if group != None: # The type of the object is ok
            meshObj = group.GetMesh()
            meshItem = salome.ObjectToSObject(meshObj)
    return meshItem, group



class SATURNE8_DataObject:
    '''
    Data Object of SATURNE8 module
    '''

    def __init__(self, path, parent):
        '''
        Constructor of SATURNE8_DataObject class
        '''
        logging.debug("SATURNE8_DataObject.__init__")
        from .CLSMainWindow import getSalomePyQt
        self.getSalomePyQt = getSalomePyQt
        name = os.path.basename(path)
        parentName = None
        if parent:
            parentName = parent.GetName()
            entry = getSalomePyQt().createObject(name,
                                                "SATURNE8_CASE_ICON",
                                                path,
                                                parent.getEntry())
            logging.debug("name: %s path: %s entry: %s parent %s",name, path, entry, parentName)
        else:
            entry = getSalomePyQt().createObject(name,
                                                "SATURNE8_CASE_ICON",
                                                path)
            logging.debug("name: %s path: %s entry: %s",name, path, entry)
        getSalomePyQt().setIcon(entry, "SATURNE8_CASE_ICON")
        self.entry = entry
        self.path = path
        self.name = name

    def getEntry(self):
        '''
        Return entry of object
        '''
        logging.debug("getEntry %s", self.entry)
        return self.entry

    def GetID(self):
        """
        for compatibility avec standard Salome Study Objects
        """
        logging.debug("GetID %s", self.entry)
        return self.entry
                      
    def getPath(self):
        '''
        Return text string
        '''
        logging.debug("getPath %s", self.path)
        return self.path

    def GetName(self):
        """
        for compatibility avec standard Salome Study Objects
        """
        logging.debug("GetName %s", self.name)
        return self.name        
        