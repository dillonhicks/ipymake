CMAKE_MINIMUM_REQUIRED(VERSION 2.6)

PROJECT( fcntl )

INCLUDE_DIRECTORIES( ${CMAKE_CURRENT_BINARY_DIR} )

SET(CMAKE_C_FLAGS "-DCONFIG_DSUI -Wall")
EXECUTE_PROCESS( COMMAND dsui-header --prefix filelock WORKING_DIRECTORY
	${CMAKE_CURRENT_BINARY_DIR} )
ADD_EXECUTABLE( filelock filelock.c filelock_dsui.c )

TARGET_LINK_LIBRARIES(filelock pthread dsui kusp m)
EXECUTE_PROCESS(COMMAND mkdir ${CMAKE_CURRENT_BINARY_DIR}/data)
#Copy over postprocessing and DSUI/DSKI configuration files
#May want to copy over custom filter modules as well...

