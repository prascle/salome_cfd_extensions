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

#------------------------------------------------------------

AC_DEFUN([CHECK_SATURNE8],[

AC_CHECKING(for Saturne8)

Saturne8_ok=no

SATURNE8_LDFLAGS=""
SATURNE8_CXXFLAGS=""

AC_ARG_WITH(gui,
	    --with-py-light=DIR root directory path of SATURNE8 installation,
	    SATURNE8_DIR="$withval",SATURNE8_DIR="")

if test "x$SATURNE8_DIR" = "x" ; then

# no --with-light option used

  if test "x$SATURNE8_ROOT_DIR" != "x" ; then

    # SATURNE8_ROOT_DIR environment variable defined
    LIGHT_DIR=$SATURNE8_ROOT_DIR

  else

    # search SATURNE8 binaries in PATH variable
    AC_PATH_PROG(TEMP, SATURNE8GUI.py)
    if test "x$TEMP" != "x" ; then
      SATURNE8_BIN_DIR=`dirname $TEMP`
      SATURNE8_DIR=`dirname $SATURNE8_BIN_DIR`
    fi

  fi
#
fi

if test -f ${SATURNE8_DIR}/lib/salome/SATURNE8GUI.py  ; then
  Saturne8_ok=yes
  AC_MSG_RESULT(Using SATURNE8 distribution in ${SATURNE8_DIR})

  if test "x$SATURNE8_ROOT_DIR" == "x" ; then
    SATURNE8_ROOT_DIR=${SATURNE8_DIR}
  fi
  AC_SUBST(SATURNE8_ROOT_DIR)
else
  AC_MSG_WARN("Cannot find compiled SATURNE8 distribution")
fi

AC_MSG_RESULT(for SATURNE8: $Saturne8_ok)

])dnl

