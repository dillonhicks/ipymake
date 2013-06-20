# $Id$
#
# AUTHOR(s):  Andrew Boie
#
# Copyright 2005(C), The University of Kansas
#
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA


"""miscellaneous functions and constants used by the group scheduling modules"""

import struct
import os
import string
from math import fabs
from errno import errorcode

STRING_PARAM_SIZE = 64
MAX_GROUP_NAME_LEN = 32
MAX_MEMBER_NAME_LEN = 32
MAX_SCHEDULER_NAME_LEN = 20

# these are also defined in group_sched_abi.h. make sure they match!
comp_types = {
    "clear"      : 0x00000000,
    "process"    : 0x00000001,
    "group"      : 0x00000002,
    "nothing"    : 0x00000004,
    "pass"       : 0x00000008,
    "hardirq"    : 0x00000010,
    "softirq"    : 0x00000020,
    "bottomhalf" : 0x00000100,
    "return"     : 0x00000040,
    }

# per-computation parameters.
task_param_id = {
    "schedpolicy"   : 1,
    "irqblocklevel" : 2,
    }

# for each param id, allowed parameters
task_param_vals = {
    "schedpolicy"   : { "exclusive"  : 0x01000,
                        "privileged" : 0x02000,
                        "groupstop"  : 0x10000,
                        } 
    }



# schedpolicy options
class GroupSchedulingException(Exception):
    pass

class GroupSchedulingKernelException(GroupSchedulingException):
    pass

def error_kernel(message, errno, error_dict={}):
    errno = int(fabs(errno))
    
    ecode = errorcode[errno]
    emessage = os.strerror(errno)

    if error_dict and ecode in error_dict:
        emessage = error_dict[ecode]
        pass
    
    message = str(message+": ["+ecode+"] "+emessage)
    
    raise GroupSchedulingKernelException, message

def error_local(message):
    raise GroupSchedulingException, str(message)


typemap = {"string"               : str(STRING_PARAM_SIZE)+"s",
           "integer"              : "i",
           "long"                 : "l",
           "float"                : "f",
           "longlong"             : "L",
           }

# helper functions


def struct_size(specdict):
    keys = specdict.keys()
    keys.sort()

    codelist = [typemap[specdict[key][1]] for key in keys]
    codes = string.join(codelist, "")
    return struct.calcsize(codelist)

def dict_to_struct(paramdict, specdict):

    if (paramdict.keys() != specdict.keys()):
        raise Exception("Parameter dictionary does not match spec.")
    
    # put the keys in the proper order
    orderdict = {}
    for key in specdict:
        orderdict[specdict[key][0]] = key
        pass
    orderlist = orderdict.keys()
    orderlist.sort()

    codelist = [typemap[specdict[orderdict[order]][1]] for order in orderlist]
    params = tuple([paramdict[orderdict[order]] for order in orderlist])
    codes = string.join(codelist, "")

    result = struct.pack(codes, *params)

    return result

def struct_to_dict(paramstruct, specdict):
    # put the keys in the proper order
    orderdict = {}
    for key in specdict:
        orderdict[specdict[key][0]] = key
        pass

    orderlist = order.keys()
    orderlist.sort()

    # build up a string with the formatting codes
    codelist = [typemap[specdict[orderdict[order]][1]] for order in orderlist]
    codes = string.join(codelist, "")
    params = struct.unpack(codes, paramstruct)

    # build the dictionary
    result = {}
    for index in range(len(params)):
        z = params[index]
        if type(z) is str:
            z = z.rstrip('\x00')
            pass

        order = orderlist.pop(0)
        
        result[orderdict[order]] = z
        pass
    return result

def cast_int(*possibles):
    result = []
    for item in possibles:
        try:
            result.append(int(item))
        except Exception, ex:
            result.append(item)
            pass
        pass
    if len(result) == 1:
        return result[0]
    else:
        return result
    pass

# group scheduling API

