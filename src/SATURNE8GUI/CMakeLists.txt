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

INCLUDE(UsePyQt)
INCLUDE(UseQtExt)

#additional include directories
INCLUDE_DIRECTORIES(
  ${QT_INCLUDES}
)

# --- scripts ---

# scripts / static
SET(_bin_SCRIPTS
  SATURNE8GUI.py
)

SET(_lib_SCRIPTS
  __init__.py
  initlog.py
  clientgui.py
  utilstudy.py
  CLSMainWindow.py
  SATURNE8_DataModel.py
)


# --- resources ---

#resource files / to be processed by lrelease
SET(_ts_RESOURCES
  SATURNE8_msg_en.ts
  SATURNE8_msg_fr.ts
  SATURNE8_icons.ts
)

# uic files / to be processed by pyuic
SET(_pyuic_files
  mw_saturne8.ui
)

# scripts / pyuic wrappings
PYQT_WRAP_UIC(_pyuic_SCRIPTS ${_pyuic_files})

# --- rules ---

SALOME_INSTALL_SCRIPTS("${_bin_SCRIPTS}" ${SALOME_INSTALL_SCRIPT_PYTHON})
SALOME_INSTALL_SCRIPTS("${_pyuic_SCRIPTS}" ${SALOME_INSTALL_PYTHON}/saturne8)
SALOME_INSTALL_SCRIPTS("${_lib_SCRIPTS}" ${SALOME_INSTALL_PYTHON}/saturne8)

QT_INSTALL_TS_RESOURCES("${_ts_RESOURCES}" "${SALOME_SATURNE8_INSTALL_RES_DATA}")
