PROJECT(clksync)

INCLUDE_DIRECTORIES( ${clksync_SOURCE_DIR}/include )
INCLUDE_DIRECTORIES( ${kusp-common_SOURCE_DIR}/include )
LINK_LIBRARIES( kusp pthread dsui m )

ADD_EXECUTABLE(clksyncctl clksyncctl.c)

ADD_LIBRARY(clksync SHARED ${clksync_SOURCE_DIR}/clksyncctl.c )
INSTALL(TARGETS clksync LIBRARY DESTINATION lib)

ADD_CUSTOM_TARGET( clksync_python_module ALL
				COMMAND python setup_clksync.py -v --build -b ${CMAKE_CURRENT_BINARY_DIR} 
				--cbd ${CMAKE_CURRENT_BINARY_DIR}
				WORKING_DIRECTORY ${clksync_SOURCE_DIR}
				COMMENT "Building clocksync Python module." VERBATIM )

#
# Generic install everything created in the project to the 
# install location.
#
INSTALL(TARGETS clksyncctl
	RUNTIME DESTINATION bin)

INSTALL( CODE "EXECUTE_PROCESS( COMMAND python setup_clksync.py -v --install --prefix ${CMAKE_INSTALL_PREFIX} --cbd ${CMAKE_CURRENT_BINARY_DIR} WORKING_DIRECTORY ${clksync_SOURCE_DIR} )" )
	
