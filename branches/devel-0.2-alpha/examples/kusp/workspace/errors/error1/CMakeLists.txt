CMAKE_MINIMUM_REQUIRED(VERSION 2.6)

PROJECT( SOCKETPIPE_GSCHED )

INCLUDE_DIRECTORIES( ${CMAKE_CURRENT_BINARY_DIR} )

SET(CMAKE_C_FLAGS "-DCONFIG_DSUI -Wall")
EXECUTE_PROCESS( COMMAND dsui-header --prefix socketpipe_gsched WORKING_DIRECTORY
        ${CMAKE_CURRENT_BINARY_DIR} )

ADD_EXECUTABLE( socketpipe_gsched socketpipe_gsched.c socketpipe_gsched_dsui.c )

TARGET_LINK_LIBRARIES(socketpipe_gsched pthread dsui kusp ccsm gsched m)

#Copy over postprocessing and DSUI/DSKI configuration files
#May want to copy over custom filter modules as well...

