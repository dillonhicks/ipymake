#
# LIBKUSP
#
PROJECT( libkusp )
FIND_PACKAGE( BISON REQUIRED )
FIND_PACKAGE( FLEX REQUIRED )

FLEX_TARGET( preproc ${kusp-common_SOURCE_DIR}/libkusp/preproc_lex.l
			${CMAKE_CURRENT_SOURCE_DIR}/preproc_lex.c)
			
BISON_TARGET( configfile_PARSER ${kusp-common_SOURCE_DIR}/libkusp/configfile_yacc.y 
			${CMAKE_CURRENT_SOURCE_DIR}/configfile_yacc.c COMPILE_FLAGS "-d -p configfile")

FLEX_TARGET( configfile_SCANNER ${kusp-common_SOURCE_DIR}/libkusp/configfile_lex.l 
			${CMAKE_CURRENT_SOURCE_DIR}/configfile_lex.c COMPILE_FLAGS "-P configfile" )

ADD_FLEX_BISON_DEPENDENCY( configfile_SCANNER configfile_PARSER )

# Generate libkusp.so
ADD_LIBRARY(kusp SHARED
    ${CMAKE_CURRENT_SOURCE_DIR}/configfile.c 
    ${CMAKE_CURRENT_SOURCE_DIR}/linkedlist.c 
    ${CMAKE_CURRENT_SOURCE_DIR}/hashtable.c 
    ${CMAKE_CURRENT_SOURCE_DIR}/hashtable_types.c 
    ${CMAKE_CURRENT_SOURCE_DIR}/misc.c 
    ${CMAKE_CURRENT_SOURCE_DIR}/kusp_common.c 
    ${CMAKE_CURRENT_SOURCE_DIR}/rdwr.c 
    ${CMAKE_CURRENT_SOURCE_DIR}/vector.c 
    ${CMAKE_CURRENT_SOURCE_DIR}/exception.c 
    ${CMAKE_CURRENT_SOURCE_DIR}/configverify.c 
    ${CMAKE_CURRENT_SOURCE_DIR}/net.c 
    ${CMAKE_CURRENT_SOURCE_DIR}/kusp_private.h 
	${FLEX_preproc_OUTPUTS}
	${BISON_configfile_PARSER_OUTPUT_SOURCE}
	${FLEX_configfile_SCANNER_OUTPUTS}
)

# Generate libkusp.a
ADD_LIBRARY(kusp-static STATIC
    ${CMAKE_CURRENT_SOURCE_DIR}/configfile.c 
    ${CMAKE_CURRENT_SOURCE_DIR}/linkedlist.c 
    ${CMAKE_CURRENT_SOURCE_DIR}/hashtable.c 
    ${CMAKE_CURRENT_SOURCE_DIR}/hashtable_types.c 
    ${CMAKE_CURRENT_SOURCE_DIR}/misc.c 
    ${CMAKE_CURRENT_SOURCE_DIR}/kusp_common.c 
    ${CMAKE_CURRENT_SOURCE_DIR}/rdwr.c 
    ${CMAKE_CURRENT_SOURCE_DIR}/vector.c 
    ${CMAKE_CURRENT_SOURCE_DIR}/exception.c 
    ${CMAKE_CURRENT_SOURCE_DIR}/configverify.c 
    ${CMAKE_CURRENT_SOURCE_DIR}/net.c 
    ${CMAKE_CURRENT_SOURCE_DIR}/kusp_private.h 
	${FLEX_preproc_OUTPUTS}
	${BISON_configfile_PARSER_OUTPUT_SOURCE}
	${FLEX_configfile_SCANNER_OUTPUTS}
)

# Rename kusp-static target so it generates libkusp.a instead of
# libkusp-static.a
SET_TARGET_PROPERTIES(kusp-static PROPERTIES OUTPUT_NAME "kusp")

# Since we're building the shared and static libs in the same directory, need
# to set the following to keep them from clobbering each other during the
# build.
SET_TARGET_PROPERTIES(kusp PROPERTIES CLEAN_DIRECT_OUTPUT 1)
SET_TARGET_PROPERTIES(kusp-static PROPERTIES CLEAN_DIRECT_OUTPUT 1)


INSTALL(TARGETS kusp kusp-static 
	LIBRARY DESTINATION lib
	ARCHIVE DESTINATION lib)
