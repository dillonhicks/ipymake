PROJECT( discovery )

IF(IS_RPM_BUILD)
    IF((NOT DEFINED DISCOVERY_RPM) AND (NOT ALL_RPMS))
        RETURN()
    ENDIF()
ENDIF()

ADD_CUSTOM_TARGET( discovery_python_module ALL
									COMMAND python setup_discovery.py -v --build -b ${CMAKE_CURRENT_BINARY_DIR}
									WORKING_DIRECTORY ${discovery_SOURCE_DIR}
									COMMENT "Building discovery Python module." VERBATIM )

INSTALL( CODE "EXECUTE_PROCESS( COMMAND python setup_discovery.py --install --prefix ${CMAKE_INSTALL_PREFIX} WORKING_DIRECTORY ${discovery_SOURCE_DIR} )" )
	
