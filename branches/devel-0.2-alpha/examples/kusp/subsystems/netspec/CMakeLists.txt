PROJECT( netspec )

IF(IS_RPM_BUILD)
    IF((NOT DEFINED NETSPEC_RPM) AND (NOT ALL_RPMS))
        RETURN()
    ENDIF()
ENDIF()


INCLUDE_DIRECTORIES( ${kusp-common_SOURCE_DIR}/include )
INCLUDE_DIRECTORIES( ${kusp-common_SOURCE_DIR}/libkusp )
INCLUDE_DIRECTORIES( ${netspec_SOURCE_DIR}/include )

ADD_LIBRARY( netspec SHARED ${netspec_SOURCE_DIR}/libnetspec/interface.c )

ADD_EXECUTABLE( ns_syscmd ${netspec_SOURCE_DIR}/syscmd/syscmd.c )

TARGET_LINK_LIBRARIES( ns_syscmd netspec kusp m)

#
# Python-Distutils for netspec
#
ADD_CUSTOM_TARGET( netspec_python_module 
				COMMAND python setup_netspec.py -v --build -b ${CMAKE_CURRENT_BINARY_DIR} 
				DEPENDS ns_syscmd netspec kusp 
				WORKING_DIRECTORY ${netspec_SOURCE_DIR}
				COMMENT "Building netspec Python module." VERBATIM )
				

INSTALL(TARGETS netspec
	RUNTIME DESTINATION bin
	LIBRARY DESTINATION lib
	ARCHIVE DESTINATION lib)

INSTALL( FILES ${netspec_SOURCE_DIR}/include/netspec2.h
		 DESTINATION include )

INSTALL( FILES ${netspec_SOURCE_DIR}/netspecd.xinetd
		 DESTINATION share )

INSTALL( CODE "EXECUTE_PROCESS( COMMAND python setup_netspec.py -v --install --prefix ${CMAKE_INSTALL_PREFIX} WORKING_DIRECTORY ${netspec_SOURCE_DIR})" )
