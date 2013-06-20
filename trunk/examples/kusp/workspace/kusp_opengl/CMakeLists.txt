set(CMAKE_C_FLAGS "-Wall -pedantic -ansi -L/usr/X11R6/lib ")
add_library( kuspgl STATIC kuspgl.c GLCube.c)
add_executable(kuspgl_test kusp_test.c)
target_link_libraries(kuspgl_test GL GLU Xxf86vm kuspgl)
