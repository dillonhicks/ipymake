""" location.py.tpl

@author: Dillon Hicks
@date: 12 JULY 2009
@summary: This file exists to make available as python variables some
environmental information such as installation directory locations, etc. At
the moment we intend this file to provide a transition role from autotools to
CMake methods. However, as we are not completely sure how things will work
out, this may become a permentant feature.

"""

#
# For backwards compatibility with the pre-cmake
# code, when kusproot was the install path rather 
# than the source path.
#
kusproot = "%(KUSP_INSTALL_PREFIX)s"
