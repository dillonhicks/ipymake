CMAKE_MINIMUM_REQUIRED(VERSION 2.6)

PROJECT( namepipe )

INCLUDE_DIRECTORIES( ${CMAKE_CURRENT_BINARY_DIR} )

SET(CMAKE_C_FLAGS "-DCONFIG_DSUI -Wall")
EXECUTE_PROCESS( COMMAND dsui-header --prefix namepipe WORKING_DIRECTORY
	${CMAKE_CURRENT_BINARY_DIR} )
ADD_EXECUTABLE( namepipe namepipe.c namepipe_dsui.c )

TARGET_LINK_LIBRARIES(namepipe pthread dsui kusp m)

#Copy over postprocessing and DSUI/DSKI configuration files
#May want to copy over custom filter modules as well...

