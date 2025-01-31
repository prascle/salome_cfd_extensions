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
  SATURNE8.png
  SATURNE8_case.png
  SATURNE8_case_open.png
  LightApp.xml
  SATURNE8_en.xml
)

INSTALL(FILES ${SATURNE8_RESOURCES_FILES} DESTINATION ${SALOME_SATURNE8_INSTALL_RES_DATA})
SALOME_CONFIGURE_FILE(${CMAKE_CURRENT_SOURCE_DIR}/SalomeApp.xml.in ${CMAKE_CURRENT_BINARY_DIR}/SalomeApp.xml INSTALL ${SALOME_SATURNE8_INSTALL_RES_DATA})