from pyccsm import ccsmapi
import os
from pyccsm.ccsmstructures import CCSMSet

class CCSMSession:
    def __init__(self, open=True):
        self.fd = None
        if open:
            self.open()

    def open(self):
        if not self.fd is None:
            raise ValueError('CCSM Session Cannot Be Opened: Session Already Opened')
        retval = ccsmapi.ccsm_open()
        if retval < 0:
            print 'CCSM Error: %s' % os.strerror(-retval)
        else:
            self.fd = retval
        return retval

    def close(self):
        if self.fd is None:
            raise ValueError('CCSM Session Cannot Be Closed: Session Not Opened')
        retval = ccsmapi.ccsm_close(self.fd)
        if retval < 0:
            print 'CCSM Error: %s' % os.strerror(-retval)
        return retval
       

    def create_set(self, set, flags):
        if isinstance(set, CCSMSet):
            set = set.get_name()
        elif not type(set) is str:
            raise TypeError('CCSMSession: set is not of '
                            'type CCSMSet or string.', set.__class__) 
        flags = int(flags)
        retval = ccsmapi.ccsm_create_set(self.fd, set, flags)
        if retval < 0:
            print 'CCSM Error: %s' % os.strerror(-retval)
        return retval
       

    def destroy_set(self, set):
        if isinstance(set, CCSMSet):
            set = set.get_name()
        elif not type(set) is str:
            raise TypeError('CCSMSession: set is not of '
                            'type CCSMSet or string.', set.__class__) 
        retval = ccsmapi.ccsm_destroy_set(self.fd, set)
        
        if retval < 0:
            print 'CCSM Error: %s' % os.strerror(-retval)
        return retval
       

    def add_member(self, set, member):
        if isinstance(set, CCSMSet):
            set = set.get_name()
        elif not type(set) is str:
            raise TypeError('CCSMSession: set is not of '
                            'type CCSMSet or string.', set.__class__)
        if isinstance(member, CCSMSet):
            member = member.get_name()
        elif not type(member) is str:
            raise TypeError('CCSMSession: member is not of '
                            'type CCSMSet or string.', member.__class__) 
         
        retval = ccsmapi.ccsm_add_member(self.fd, set, member)
        if retval < 0:
            print 'CCSM Error: %s' % os.strerror(-retval)
        return retval
       

    def remove_member(self, set, member):
        if isinstance(set, CCSMSet):
            set = set.get_name()
        elif not type(set) is str:
            raise TypeError('CCSMSession: set is not of '
                            'type CCSMSet or string.', set.__class__)
        if isinstance(member, CCSMSet):
            member = member.get_name()
        elif not type(member) is str:
            raise TypeError('CCSMSession: member is not of '
                            'type CCSMSet or string.', member.__class__) 
         
        retval = ccsmapi.ccsm_remove_member(self.fd, set, member)
        if retval < 0:
            print 'CCSM Error: %s' % os.strerror(-retval)
        return retval

    

    def create_component_self(self, component):
        if not type(component) is str:
            component = str(component)
        retval = ccsmapi.ccsm_create_component_self(self.fd, component)
        if retval < 0:
            print 'CCSM Error: %s' % os.strerror(-retval)
        return retval


    def create_component_by_pid(self, component, pid):
        if not type(component) is str:
            component = str(component)
        if not type(pid) is int:
            try:
                pid = int(pid)
            except ValueError, eargs:
                raise TypeError('CCSMSession: pid must be of type int.', type(pid))

        retval = ccsmapi.ccsm_create_component_by_pid(self.fd, component, pid)
        if retval < 0:
            print 'CCSM Error: %s' % os.strerror(-retval)
        return retval
    

    def destroy_component_by_name(self, component):
        
        if not type(component) is str:
            component = str(component)
        retval = ccsmapi.ccsm_create_component_self(self.fd, component)
        if retval < 0:
            print 'CCSM Error: %s' % os.strerror(-retval)
        return retval

    

    def destroy_component_by_pid(self, pid):
        if not type(component) is str:
            component = str(component)
        if not type(pid) is int:
            try:
                pid = int(pid)
            except ValueError, eargs:
                raise TypeError('CCSMSession: pid must be of type int.', type(pid))

        retval = ccsmapi.ccsm_destroy_component_by_pid(self.fd, component, pid)
        if retval < 0:
            print 'CCSM Error: %s' % os.strerror(-retval)
        return retval

    
