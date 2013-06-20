CMAKE_MINIMUM_REQUIRED(VERSION 2.6)

PROJECT( multithreads  )

INCLUDE_DIRECTORIES( ${CMAKE_CURRENT_BINARY_DIR} )

SET(CMAKE_C_FLAGS "-DCONFIG_DSUI -Wall")
EXECUTE_PROCESS( COMMAND dsui-header --prefix multithreads WORKING_DIRECTORY
	${CMAKE_CURRENT_BINARY_DIR} )
ADD_EXECUTABLE( multithreads ${CMAKE_CURRENT_SOURCE_DIR}/multithreads.c
	${CMAKE_CURRENT_BINARY_DIR}/multithreads_dsui.c )

TARGET_LINK_LIBRARIES(multithreads pthread dsui kusp ccsm gsched m)

#Copy over postprocessing and DSUI/DSKI configuration files
#May want to copy over custom filter modules as well...

