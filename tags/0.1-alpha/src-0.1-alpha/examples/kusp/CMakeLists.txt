#   KUSP Userspace Source Tree CMake Configuration
#	AUTHORS: Dillon Hicks, Noah Watkins	(2009)
#	
CMAKE_MINIMUM_REQUIRED(VERSION 2.6)
SET( CMAKE_VERBOSE_MAKEFILE ON )

#########################
#  RPM Options Setup
#########################
SET( RPM_PACKAGES GSCHED_RPM DISCOVERY_RPM COMMON_RPM 
         CCSM_RPM DATASTREAMS_RPM NETSPEC_RPM CLKSYNC_RPM)
SET( ALL_RPMS FALSE)
IF( NOT (DEFINED IS_RPM_BUILD) )
    SET(IS_RPM_BUILD 0)    
ELSE()
    SET( ALL_RPMS TRUE ) 
    FOREACH(package ${RPM_PACKAGES})
	IF(DEFINED ${package})
	  SET(ALL_RPMS FALSE)
	  BREAK()
	ENDIF()
    ENDFOREACH(package)
ENDIF()
####  End Rpm Options Setup ####


MESSAGE(
	"*******************************************************************************\n"
	"*                 KUSP Userspace Software CMake Configuration                 *\n"
	"*******************************************************************************\n"
	" \n"
	"  Any errors and problems related to CMake should be dealt with in the \n"
	"  steps:\n"
	" \n"
	"  1) Consult the KUSP CMake Developers Guide:\n"
	" 	 -- http://www.ittc.ku.edu/kusp/kusp_docs/cmake/index.html \n"
	" \n"
	"  2) Join the KUSP Google Group and post a thread pertaining to your issue:\n"
	"	-- http://groups.google.com/group/kusp \n"
	"\n"
	"*******************************************************************************\n\n" )

#
# Creating project, and associated variables.
#
PROJECT(KUSP)

#
# Setting the CMake module path to specify the 
# directory into which CMake should look to 
# find extra modules, such as BISON and FLEX.
#
SET( CMAKE_MODULE_PATH ${CMAKE_CURRENT_SOURCE_DIR}/cmake )

#
# Setting compiler flags.
#
SET(CMAKE_C_FLAGS "-g -Wall")

#
# FIXME.NOAH: What is this used for?
#
INCLUDE(FindPythonInterp)

#
# FIXME.NOAH: What is this used for?
#
INCLUDE(FindPythonLibs)

#
# Only adding subsystems because workspace and examples 
# should be made indepedently.
#
ADD_SUBDIRECTORY(subsystems)
IF(NOT IS_RPM_BUILD)
    ADD_SUBDIRECTORY(workspace)
ENDIF()

#
# Make subsystem includes available by default.
#
INCLUDE_DIRECTORIES(${groupsched_SOURCE_DIR}/include)

IF( NOT IS_RPM_BUILD)
MESSAGE(
	"*******************************************************************************\n"
	"*                                 ADVISORY                                    *\n"
	"*******************************************************************************\n"
	"  To compile programs that use KUSP libraries and headers,\n"
	"  You will need to let the compilation environment know where \n"
	"  they are installed.\n"
	"\n"	
	"  You should add the following lines to your .bashrc:\n"	
	"\n"
 	"   export PYTHONPATH=$KUSPINSTALL/lib/python<your-python-version>/site-packages:$PYTHONPATH \n"
	"   export LD_LIBRARY_PATH=$KUSPINSTALL/lib:$LD_LIBRARY_PATH \n"
  	"   export PATH=$KUSPINSTALL/bin:$PATH \n"
	"\n"
	"\n"
	"\n"
	"  Disregard this advisory if you installed in /usr or /usr/local\n"
	"\n"
	"*******************************************************************************\n\n" )
ENDIF()

	
