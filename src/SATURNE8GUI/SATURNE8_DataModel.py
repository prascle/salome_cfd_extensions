# -*- coding: utf-8 -*-
# Copyright (C) 2009-2017 EDF, OPEN CASCADE
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 USA
#
# See http://www.salome-platform.org/ or email : webmaster.salome@opencascade.com
#

#  Author : Roman NIKOLAEV Open CASCADE S.A.S. (roman.nikolaev@opencascade.com)
#  Date   : 13/04/2009
#

import logging
import os

from .CLSMainWindow import getSalomePyQt
from . import CFDSTUDYGUI_DataModel

def processText(text):
    '''
    Remove "\n" sumbol from end of line
    '''
    logging.debug("processText")
    processed = str(text)
    if processed[len(processed)-1:] == "\n":
        processed = processed[:len(processed)-1]

    return processed


class SATURNE8_DataModel:
    '''
    Data model of SALOME SATURNE8 module
    What is stored in the SALOME study and saved in the hdf study file.
    Only the path of the Saturne8 case files (*.syd) are stored.
    '''

    def __init__(self):
        '''
        Constructor of SATURNE8_DataModel class.
        '''
        logging.debug("SATURNE8_DataModel.__init__")
        self.myObjects = {}

    def getSaturne8Studies(self):
        '''
        Return the list of CFD Studies cases:
        Salome Study entries that are direct children of the module.
        '''
        # === Only with light Study objects (texts) ===
        logging.debug("get Module children in Salome Study (CFD Studies)")
        children = getSalomePyQt().getChildren()
        for child in children:
            logging.debug("child: %s", child)
        logging.debug("done")
        return children
        
    def findInStudy(self, text):
        logging.debug("findInStudy %s", text)
        caseObjs = self.getSaturne8Studies()
        for entry in caseObjs:
            if entry not in self.myObjects:
                logging.critical(
                    "inconsistency: entry in SALOME study, under the Saturne8 module, not known")
                return ""
            caseObj = self.myObjects[entry]
            casePath = caseObj.getText()
            logging.debug("entry: %s case: %s", entry, casePath)
            if text == casePath:
                return entry
        return ""

    def getObject(self, entry):
        '''
        Return SATURNE8_DataObject by its entry.
        '''
        logging.debug("getObject")
        obj = None
        if entry in self.myObjects:
            obj = self.myObjects[entry]
        return obj

    def findOrCreateObject(self, text):
        '''
        Create SATURNE8_DataObject (Saturne8 case name and path).
        '''
        logging.debug("findOrCreateObject %s", text)
        entry = self.findInStudy(text)
        if not entry:
            logging.debug("create study entry for %s", text)
            obj = SATURNE8_DataObject(text)
            entry = obj.getEntry()
            self.myObjects[entry] = obj
        return entry

    def removeObject(self, entry):
        ''' 
        Remove object by its entry
        '''
        logging.debug("removeObject %s", entry)
        if entry in self.myObjects:
            getSalomePyQt().removeObject(entry)
            self.myObjects.pop(entry)

    def saveFile(self, filename):
        """
        Write one line per Saturne8 case, with the full case path
        """
        logging.debug("saveFile %s", filename)
        with open(filename, mode='w', encoding='utf-8') as f:
            caseEntries = self.getSaturne8Studies()
            for entry in caseEntries:
                logging.debug("entry: %s", entry)
                caseObj = self.myObjects[entry]
                casePath = caseObj.getText()
                logging.debug("casePath %s", casePath)
                f.write(casePath + "\n")


class SATURNE8_DataObject:
    '''
    Data Object of SATURNE8 module
    '''

    def __init__(self, text):
        '''
        Constructor of SATURNE8_DataObject class
        '''
        logging.debug("SATURNE8_DataObject.__init__")
        casePath = text
        caseName = os.path.basename(casePath)
        entry = getSalomePyQt().createObject(caseName,
                                             "SATURNE8_CASE_ICON",
                                             casePath)
        logging.debug("entry: %s", entry)
        getSalomePyQt().setIcon(entry, "SATURNE8_CASE_ICON")
        self.entry = entry
        self.text = casePath

    def getEntry(self):
        '''
        Return entry of object
        '''
        logging.debug("getEntry %s", self.entry)
        return self.entry

    def getText(self):
        '''
        Return text string
        '''
        logging.debug("getText %s", self.text)
        return self.text
