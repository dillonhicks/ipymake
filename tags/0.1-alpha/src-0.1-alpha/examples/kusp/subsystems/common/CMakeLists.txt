PROJECT(kusp-common)

IF(IS_RPM_BUILD)
    IF((NOT DEFINED KUSP_COMMON_RPM) AND (NOT ALL_RPMS))
        RETURN()
    ENDIF()
ENDIF()


INCLUDE_DIRECTORIES( ${kusp-common_SOURCE_DIR}/include )
ADD_SUBDIRECTORY( include )
ADD_SUBDIRECTORY( libkusp )

# Creating a stashed location of the install directory in 'pykusp.location' python module.
# This is used by several of the modules to determine where the root installation directory
# is, so that they can easily find the shared files, libraries, etc. in case of a local install.
#
EXECUTE_PROCESS( COMMAND python generate_location_file -p ${CMAKE_INSTALL_PREFIX} --rpm_build=${IS_RPM_BUILD}
	WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/pykusp )


#
# printconfig
#
ADD_EXECUTABLE( printconfig ${kusp-common_SOURCE_DIR}/libkusp/printconfig.c)
TARGET_LINK_LIBRARIES( printconfig kusp m )

#
# calib
#
ADD_EXECUTABLE( calib ${kusp-common_SOURCE_DIR}/libperf/calib.c)	
TARGET_LINK_LIBRARIES( calib kusp m )


# Distutils build scripts for libkusp and pykusp
#
ADD_CUSTOM_TARGET( libkusp_python_module ALL
						COMMAND python setup_libkusp.py -v --build -b ${CMAKE_CURRENT_BINARY_DIR}
                        --cbd ${CMAKE_CURRENT_BINARY_DIR}
						DEPENDS kusp
						WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
						COMMENT "Building libkusp Python module." VERBATIM )
						
ADD_CUSTOM_TARGET( pykusp_python_module ALL
						COMMAND python setup_pykusp.py -v --build -b ${CMAKE_CURRENT_BINARY_DIR}
						DEPENDS kusp
						WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
						COMMENT "Building pykusp Python module." VERBATIM )


# Installing the CMake managed targets to the appropriate destinations.
#
INSTALL(TARGETS printconfig calib
	RUNTIME DESTINATION bin )
	
# Installing the shared files.
#
INSTALL( FILES ${CMAKE_CURRENT_SOURCE_DIR}/libkusp/cspec.cspec
         DESTINATION share )
#
# Distutils install scripts for libkusp and pykusp
#
INSTALL( CODE "EXECUTE_PROCESS( COMMAND python setup_libkusp.py -v --install --prefix ${CMAKE_INSTALL_PREFIX} --cbd ${CMAKE_CURRENT_BINARY_DIR} WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR} )" )
INSTALL( CODE "EXECUTE_PROCESS( COMMAND python setup_pykusp.py -v --install --prefix ${CMAKE_INSTALL_PREFIX} WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR} )" )


