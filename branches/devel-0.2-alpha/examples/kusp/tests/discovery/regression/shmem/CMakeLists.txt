CMAKE_MINIMUM_REQUIRED(VERSION 2.6)

PROJECT( shmem  )

INCLUDE_DIRECTORIES( ${CMAKE_CURRENT_BINARY_DIR} )

SET(CMAKE_C_FLAGS "-Wall")
ADD_EXECUTABLE( shmem shmem.c )

TARGET_LINK_LIBRARIES(shmem pthread)

EXECUTE_PROCESS(COMMAND mkdir ${CMAKE_CURRENT_BINARY_DIR}/data)
#Copy over postprocessing and DSUI/DSKI configuration files
#May want to copy over custom filter modules as well...

