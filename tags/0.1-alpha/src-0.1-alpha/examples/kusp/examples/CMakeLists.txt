cmake_minimum_required(VERSION 2.6)

INCLUDE_DIRECTORIES( ${CMAKE_INSTALL_PREFIX}/include )
LINK_DIRECTORIES( ${CMAKE_INSTALL_PREFIX}/lib )


ADD_SUBDIRECTORY( simple_dsui )
ADD_SUBDIRECTORY( unified_sigpipe )
ADD_SUBDIRECTORY( multithreads )

ADD_SUBDIRECTORY( sigpipe_gsched )
ADD_SUBDIRECTORY( sigpipe_gsched_ccsm )
ADD_SUBDIRECTORY( sigpipe_gschedctrl )

ADD_SUBDIRECTORY( socketpipe_gsched )
ADD_SUBDIRECTORY( socketpipe_gsched_ccsm )
ADD_SUBDIRECTORY( socketpipe_gschedctrl )

ADD_SUBDIRECTORY( balanced_pipeline )
ADD_SUBDIRECTORY( balanced_pipeline_gschedctrl )

ADD_SUBDIRECTORY( global_timeline )
