# Copyright (C) 2013-2017 EDF, OPEN CASCADE
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

SET(SATURNE8_RESOURCES_FILES
  CaseAdd.png
  CaseEdit.png
  CaseInProcess.png
  Case.png
  CaseRun.png
  CFDSTUDY.png
  CheckCompilation.png
  CloseGui.png
  Close.png
  compiler-icon.png
  create_load_case.png
  data_editor-icon.png
  Delete.png
  Document.png
  EditableDocument.png
  EditFile.png
  edit-redo.png
  edit-undo.png
  Executable.png
  file_transfer.png
  Folder.png
  FolderRed.png
  InfoCFDSTUDY.png
  LaunchGUI.png
  LaunchGUIwithOptions.png
  LightApp.xml
  MED_Module_Convert.png
  mesh_group.png
  mesh.png
  mesh_tree_group.png
  mesh_tree_mesh.png
  MoveFile.png
  MoveFolder.png
  NewTreeCreate.png
  OpenedFolder.png
  ot-logo.png
  paravisFile.png
  resu_viewer-icon.png
  run_button.png
  RunScript.png
  saturne8_240.png
  SATURNE8_case_open.png
  SATURNE8_case.png
  SATURNE8_en.xml
  SalomeAppSL.xml
  SATURNE8.png
  Save.png
  SetTreeLocation.png
  SMESH_Module_Export.png
  src_editor-icon.png
  Study.png
  TmpFile.png
  UnknownDocument.png
  UpdateObjBrowser.png
  ViewFile.png
  VISU_Module_Export.png
  VISU_Plot_Export.png
  VISU_Plot.png
)

INSTALL(FILES ${SATURNE8_RESOURCES_FILES} DESTINATION ${SALOME_SATURNE8_INSTALL_RES_DATA})
#SALOME_CONFIGURE_FILE(${CMAKE_CURRENT_SOURCE_DIR}/SalomeApp.xml.in ${CMAKE_CURRENT_BINARY_DIR}/SalomeAppSL.xml INSTALL ${SALOME_SATURNE8_INSTALL_RES_DATA})