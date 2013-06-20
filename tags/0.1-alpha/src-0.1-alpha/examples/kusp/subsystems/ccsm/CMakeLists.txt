PROJECT( CCSM )

INCLUDE_DIRECTORIES( include ) 

ADD_LIBRARY( ccsm SHARED ${CCSM_SOURCE_DIR}/libccsm/ccsm.c )

#
# SWIG SETUP For libccsmmodule
#
FIND_PACKAGE( SWIG REQUIRED )
INCLUDE(${SWIG_USE_FILE})
FIND_PACKAGE( PythonLibs ) 
INCLUDE_DIRECTORIES(${PYTHON_INCLUDE_PATH})

INCLUDE_DIRECTORIES( ${CMAKE_CURRENT_BINARY_DIR} )
SET(CMAKE_SWIG_FLAGS "")

CONFIGURE_FILE( ${CMAKE_CURRENT_SOURCE_DIR}/libccsm/ccsm.i
				${CMAKE_CURRENT_BINARY_DIR}/ccsm.i COPYONLY )
				
CONFIGURE_FILE( ${CMAKE_CURRENT_SOURCE_DIR}/libccsm/ccsm.c
				${CMAKE_CURRENT_BINARY_DIR}/ccsm.c COPYONLY )			



# FIXME.DILLON - some confusion exists over ccsm.py vs ccsmapi.py
#	the distutils file (setup_groupsched.py) appears to be trying to
#	reference ccsm.py after it has been renamed by the command below.
ADD_CUSTOM_COMMAND( OUTPUT swig_ccsm_setup 
                    COMMAND swig -python ${CMAKE_CURRENT_SOURCE_DIR}/libccsm/ccsm.i
                    COMMAND mv ${CMAKE_CURRENT_SOURCE_DIR}/libccsm/ccsm.py
                       ${CMAKE_CURRENT_SOURCE_DIR}/pyccsm/ccsmapi.py
                    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
                    COMMENT "Creating ccsm SWiG Python Wrappers." VERBATIM )

#
# Running distutils in setup.py, and building python package
# from  directory pyccsm.
#
ADD_CUSTOM_TARGET( ccsm_python_module ALL
				COMMAND python setup_ccsm.py -v --build -b ${CMAKE_CURRENT_BINARY_DIR}
				--cbd ${CMAKE_CURRENT_BINARY_DIR}
				DEPENDS ccsm swig_ccsm_setup
				WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
				COMMENT "Building ccsm Python module." VERBATIM )
				
INSTALL( TARGETS ccsm	
	LIBRARY DESTINATION lib )

INSTALL( FILES ${CMAKE_CURRENT_SOURCE_DIR}/include/ccsm.h
		DESTINATION include )
#
# 'python setup.py install' For the distutils for pyccsm. 
#
INSTALL( CODE "EXECUTE_PROCESS( COMMAND python setup_ccsm.py -v --install --prefix ${CMAKE_INSTALL_PREFIX} --cbd ${CMAKE_CURRENT_BINARY_DIR} WORKING_DIRECTORY ${CCSM_SOURCE_DIR})")


		
