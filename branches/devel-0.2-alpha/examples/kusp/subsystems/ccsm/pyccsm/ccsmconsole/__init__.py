"""
:mod:`ccsmconsole` -- CCSM Commandline Console
==========================================================

"""
import sys
import os
import string
from pykusp.devutils.kuspconsole import KUSPConsole
import pyccsm.ccsmsession as session
from pyccsm.ccsmstructures import CCSMSet
import pyccsm.ccsmprocutils as ccsmproc

class CCSMConsole(KUSPConsole):
    """
    A class to provide an interactive/interperator shell for thoe
    CCSM API and utilities.
    """
    def __init__(self):
        KUSPConsole.__init__(self, 'pyccsm.ccsmconsole.ccsmmethods') 
        self.ccsm_session = session.CCSMSession()
        self.prompt = 'ccsm>'
        self.banner = \
"""
================================================
KUSP CCSM API Shell

Type `help' for commands or `help <command>' 
for extended help about particular commands.
================================================
"""                
