CMAKE_MINIMUM_REQUIRED(VERSION 2.6)

PROJECT( flock )

INCLUDE_DIRECTORIES( ${CMAKE_CURRENT_BINARY_DIR} )

SET(CMAKE_C_FLAGS "-DCONFIG_DSUI -Wall")
EXECUTE_PROCESS( COMMAND dsui-header --prefix filelock WORKING_DIRECTORY
	${CMAKE_CURRENT_BINARY_DIR} )
ADD_EXECUTABLE( flock filelock.c filelock_dsui.c )

TARGET_LINK_LIBRARIES(flock pthread dsui kusp m)

#Copy over postprocessing and DSUI/DSKI configuration files
#May want to copy over custom filter modules as well...

