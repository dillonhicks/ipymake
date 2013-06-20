CMAKE_MINIMUM_REQUIRED(VERSION 2.6)

PROJECT( multithreadsA )

INCLUDE_DIRECTORIES( ${CMAKE_CURRENT_BINARY_DIR} )

SET(CMAKE_C_FLAGS " -Wall")

ADD_EXECUTABLE( multithreadsA ${CMAKE_CURRENT_SOURCE_DIR}/multithreadsA.c )
TARGET_LINK_LIBRARIES(multithreadsA pthread dsui kusp ccsm gsched m)

ADD_EXECUTABLE( multithreadsB ${CMAKE_CURRENT_SOURCE_DIR}/multithreadsB.c )
TARGET_LINK_LIBRARIES(multithreadsB pthread dsui kusp ccsm gsched m)

ADD_EXECUTABLE( multithreadsC ${CMAKE_CURRENT_SOURCE_DIR}/multithreadsC.c )
TARGET_LINK_LIBRARIES(multithreadsC pthread dsui kusp ccsm gsched m)

ADD_EXECUTABLE( multithreadsD ${CMAKE_CURRENT_SOURCE_DIR}/multithreadsD.c )
TARGET_LINK_LIBRARIES(multithreadsD pthread dsui kusp ccsm gsched m)

