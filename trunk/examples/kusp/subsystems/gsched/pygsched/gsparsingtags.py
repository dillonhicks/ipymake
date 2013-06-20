""" gsparsingtags.py
PARSING TAGS FOR THE .gsh CONFIG FILE                          

@author: Dillon Hicks
@contact: kusp[at]googlegroups[dot]com
@contact: hhicks[at]ittc[dot]ku[dot]edu
@version: 1.0                                         
@summary: These should be more or less self explanatory, 
    for more info look at the example.gsh configuration file for 
    the parsing syntax.                       
"""

########################## Top Level Tags ######################################
GSH_INSTALLATION_TAG = 'gsh-installation'
SDF_SPECIFICATION_TAG = 'sdf-specification'
GROUPS_TAG = 'groups'
THREADS_TAG = 'threads'
THREAD_SPEC_TAG = 'thread-specification'

TOP_LEVEL_TAGS = (GSH_INSTALLATION_TAG,
                      SDF_SPECIFICATION_TAG,
                      GROUPS_TAG,
                      THREADS_TAG,
                      THREAD_SPEC_TAG )
################################################################################



##################### GSH-INSTALLATION LEVEL TAGS ##############################    

LOCAL_ROOT_TAG = 'local-root'
ATTACHMENT_POINT_TAG = 'attachment-point'

GSH_INSTALLATION_TAGS = ( LOCAL_ROOT_TAG,
                          ATTACHMENT_POINT_TAG)

################################################################################



###################### SDF SPECIFICATION LEVEL TAGS ############################
SDF_NAME_TAG        = 'name'
SDF_PGD_TAG         = 'per_group_data'
SDF_PMD_TAG         = 'per_member_data' 
DATA_TYPE_TAG       = 'type'
DATA_DOCSTRING_TAG  = 'doc'
DATA_INDEX_TAG      = 'index'
DATA_ATTRIBUTES_TAG = 'attributes'
DATA_VALUE_TAG      = 'value'

SDF_SPECIFICATION_TAGS = ( SDF_NAME_TAG,
                           SDF_PGD_TAG,
                           SDF_PMD_TAG , 
                           DATA_TYPE_TAG,
                           DATA_DOCSTRING_TAG,
                           DATA_INDEX_TAG,
                           DATA_ATTRIBUTES_TAG,
                           DATA_VALUE_TAG )
################################################################################


############################ GROUP LEVEL TAGS ##################################
GROUP_SDF_TAG = 'sdf'
GROUP_ATTRIBUTES_TAG = 'attributes'
GROUP_PGD_TAG = 'per_group_data'
GROUP_MEMBERS_TAG = 'members'
GROUP_MEMBER_NAME_TAG = 'member_name'
GROUP_COMMENT_TAG = 'comment'
GROUPS_TAGS = ( GROUP_SDF_TAG,
                GROUP_ATTRIBUTES_TAG,
                GROUP_PGD_TAG,
                GROUP_MEMBERS_TAG,
                GROUP_COMMENT_TAG,
                GROUP_MEMBER_NAME_TAG)

################################################################################



################### THREAD_SPEC LEVEL TAGS ###############

THREAD_SPEC_ATTRIBUTES_TAG = 'attributes' 
THREAD_SPEC_PMD_TAG = 'per_member_data'
THREAD_SPEC_COMMENT_TAG = 'comment'

THREAD_SPEC_TAGS = (THREAD_SPEC_ATTRIBUTES_TAG,
               THREAD_SPEC_PMD_TAG,
               THREAD_SPEC_COMMENT_TAG)
       
################################################################################
