PROJECT( datastreams )

IF(IS_RPM_BUILD)
    IF((NOT DEFINED DATASTREAMS_RPM) AND (NOT ALL_RPMS))
        RETURN()
    ENDIF()
ENDIF()


ADD_SUBDIRECTORY( dsui )
ADD_SUBDIRECTORY( dski )

ADD_CUSTOM_COMMAND( OUTPUT swig_setup 
                    COMMAND swig -python ${CMAKE_CURRENT_SOURCE_DIR}/pydsui_backend.i
                    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
                    COMMENT "Creating DSUI SWIG Python Wrappers." VERBATIM)



ADD_CUSTOM_TARGET( datastreams_python_module ALL
				 COMMAND python setup_datastreams.py -v --build -b ${CMAKE_CURRENT_BINARY_DIR} --kernel ${KERNELROOT} --cbd ${CMAKE_CURRENT_BINARY_DIR}
				 WORKING_DIRECTORY ${datastreams_SOURCE_DIR} 
				 DEPENDS dsui swig_setup
				 COMMENT "Building datastreams Python module." VERBATIM )

INSTALL( FILES ${CMAKE_CURRENT_SOURCE_DIR}/dstream_admin.ns
		 ${CMAKE_CURRENT_SOURCE_DIR}/ns.cspec
		 ${CMAKE_CURRENT_SOURCE_DIR}/postprocess/pipes.cspec
		 DESTINATION share )

INSTALL( FILES 	 ${CMAKE_CURRENT_SOURCE_DIR}/include/clksyncapi.h
		 ${CMAKE_CURRENT_SOURCE_DIR}/include/dski.h
		 ${CMAKE_CURRENT_SOURCE_DIR}/include/dsui.h
		 ${CMAKE_CURRENT_SOURCE_DIR}/include/dsentity.h
		 ${CMAKE_CURRENT_SOURCE_DIR}/include/dsheader.h
		 ${CMAKE_CURRENT_SOURCE_DIR}/include/dslist.h
		 ${CMAKE_CURRENT_SOURCE_DIR}/include/dsnamespace.h
		 DESTINATION include )
		 
INSTALL( FILES ${CMAKE_CURRENT_SOURCE_DIR}/include/linux/clksync.h
		DESTINATION include/linux )

INSTALL( CODE "EXECUTE_PROCESS( COMMAND python setup_datastreams.py -v --install --prefix ${CMAKE_INSTALL_PREFIX} --kernel ${KERNELROOT} --cbd ${CMAKE_CURRENT_BINARY_DIR} WORKING_DIRECTORY ${datastreams_SOURCE_DIR} )" )
