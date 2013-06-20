PROJECT( experiment_frontend )
INCLUDE_DIRECTORIES( ${CMAKE_CURRENT_BINARY_DIR} )
ADD_EXECUTABLE( console_p console_prototype.c )
TARGET_LINK_LIBRARIES( console_p panel ncurses )

SET(CMAKE_C_FLAGS "-DCONFIG_DSUI -Wall")

EXECUTE_PROCESS( COMMAND dsui-header --prefix sigpipe WORKING_DIRECTORY
	${CMAKE_CURRENT_BINARY_DIR} )
ADD_EXECUTABLE( sigpipe_supreme ${CMAKE_CURRENT_SOURCE_DIR}/sigpipe.c
	${CMAKE_CURRENT_BINARY_DIR}/sigpipe_dsui.c )

TARGET_LINK_LIBRARIES(sigpipe_supreme pthread dsui kusp ccsm m panel ncurses )


