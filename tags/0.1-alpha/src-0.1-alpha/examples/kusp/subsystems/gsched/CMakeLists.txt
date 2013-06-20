PROJECT(groupsched)

IF(IS_RPM_BUILD)
    IF((NOT DEFINED GSCHED_RPM) AND (NOT ALL_RPMS))
        RETURN()
    ENDIF()
ENDIF()

#
# The directory of the gsched.h API.
#
INCLUDE_DIRECTORIES( ${groupsched_SOURCE_DIR}/include )
INCLUDE_DIRECTORIES( ${kusp-common_SOURCE_DIR}/include ) 
#
# Define the gsched library to be a shared libary built from 
# the gsched.c source file.
#
ADD_LIBRARY(gsched SHARED libgsched/gsched.c)

LINK_LIBRARIES( gsched )

#
# Defining the executables start and stop
# to be compiled from source files start.c
# and stop.c, respectively.
#
ADD_EXECUTABLE( start start.c )
ADD_EXECUTABLE( stop stop.c )

CONFIGURE_FILE( ${CMAKE_CURRENT_SOURCE_DIR}/libgsched/gsched.i
				${CMAKE_CURRENT_BINARY_DIR}/gsched.i COPYONLY )
CONFIGURE_FILE( ${CMAKE_CURRENT_SOURCE_DIR}/libgsched/gsched.c
				${CMAKE_CURRENT_BINARY_DIR}/gsched.c COPYONLY )		

ADD_CUSTOM_COMMAND( OUTPUT swig_setup 
                    COMMAND swig -python ${CMAKE_CURRENT_SOURCE_DIR}/libgsched/gsched.i
                    COMMAND mv ${CMAKE_CURRENT_SOURCE_DIR}/libgsched/gsched.py
                        ${CMAKE_CURRENT_SOURCE_DIR}/pygsched/gschedapi.py
		    COMMAND swig -python ${CMAKE_CURRENT_SOURCE_DIR}/libgsched/sdf_seq.i
                    COMMAND mv ${CMAKE_CURRENT_SOURCE_DIR}/libgsched/sdf_seq.py
                        ${CMAKE_CURRENT_SOURCE_DIR}/pygsched/
                    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
                    COMMENT "Creating gsched SWiG Python Wrappers." VERBATIM)


#
# Running distutils in setup.py, and building python package
# from  directory pygsched.
#
ADD_CUSTOM_TARGET( groupsched_python_module ALL
				COMMAND python setup_groupsched.py -v --build -b ${CMAKE_CURRENT_BINARY_DIR}
				--cbd ${CMAKE_CURRENT_BINARY_DIR}
				DEPENDS gsched swig_setup
				WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
				COMMENT "Building groupsched Python module." VERBATIM )


#
# Installing everything created in the gsched project.
#
INSTALL(TARGETS gsched start stop
	RUNTIME DESTINATION bin
	LIBRARY DESTINATION lib
	ARCHIVE DESTINATION lib)
INSTALL( FILES ${groupsched_SOURCE_DIR}/include/sched_gsched.h
		DESTINATION include )
INSTALL( FILES ${groupsched_SOURCE_DIR}/include/linux/sched_gsched.h
	       ${groupsched_SOURCE_DIR}/include/linux/gsched_sdf_mpgd.h
		DESTINATION include/linux )
#
# Copying the generated swig wrapper into the pygsched directory.
#
#INSTALL(CODE "CONFIGURE_FILE( ${groupsched_SOURCE_DIR}/gsched.py ${groupsched_SOURCE_DIR}/pygsched/gsched.py COPYONLY)" ) 
	

#
# 'python setup.py install' For the distutils for pygsched. 
#
INSTALL( CODE "EXECUTE_PROCESS( COMMAND python setup_groupsched.py -v --install --prefix ${CMAKE_INSTALL_PREFIX} --cbd ${CMAKE_CURRENT_BINARY_DIR} WORKING_DIRECTORY ${groupsched_SOURCE_DIR})")


