"""
:mod:`gsconsole` -- Group Scheduling Commandline Console
==========================================================

"""
import sys
import os
import traceback
from code import InteractiveConsole
import signal 
import string
import pykusp.configutility as config

try:
    global Params
    Params.debug_level
except NameError:
    class FallbackParams:
        debug_level = 0
        verbose_level = 0

    Params = FallbackParams()


class LogLevels:
    NORMAL = 0
    VERBOSE = 1
    VERY_VERBOSE = 2
    DEBUG = 3
    VERBOSE_DEBUG = 4
    

class KUSPConsole(InteractiveConsole):
    """
    A class to provide an interactive/interperator shell for thoe
    Group Scheduling API and utilities.
    """
    def __init__(self, commands_module=None):
        import readline
        InteractiveConsole.__init__(self, globals())
        self.public_methods = ('pyex', 'quit', 'exit', 'help', 'menu') 
        self.hidden_actions = filter(lambda m: not m in self.public_methods, 
                                     dir(self) )
        self.hidden_actions.extend(dir(InteractiveConsole()))# DO NOT CHANGE THIS LINE!
        self.prompt = 'kusp>'
        self.banner = \
"""
================================================
KUSP Abstract Interactive Console

Type `help' for commands or `help <command>' 
for extended help about particular commands.
================================================
"""
        if commands_module is None:
            return

        from types import MethodType, FunctionType
        __import__(commands_module) 
        extra_commands = sys.modules[commands_module]
        c_filter = lambda name: not name.startswith("_") and \
                                type(getattr(extra_commands, name)) is FunctionType
 
        console_actions = filter( c_filter, dir(extra_commands))

        for action in console_actions:
            console_method = MethodType(getattr(extra_commands, action), self, self.__class__)
            setattr(self, action, console_method)

    
    #########################################
    # Interactive Console Methods
    # -- Should not be callable by the user.
    #########################################
    def interact(self):
        """
        Starts the interactive console main loop and prints the
        banner, similarly to Python interperator loop.

        The functionality of the loop can be described as:

        while(running_conditions):
            user_input = self.raw_input()
            self.push(user_input)

        """
        InteractiveConsole.interact(self, self.banner)
        
    def write(self, out_string, log_level=LogLevels.NORMAL):
        """
        Writes the out_string to stdout. This is more flexible than
        'print' because it provides a log_level argument that works
        with the global Params object to see if the verbosity and/or
        debug levels are high enough to write out diagnostic messages.
        """
        write_message = False
        if log_level == LogLevels.NORMAL:
            write_message = True
        else:
            if log_level >= LogLevels.DEBUG:
                # log_level - 3 to translate it to proper debug level.
                if log_level-2 <= Params.debug_level:
                    write_message = True
                    
            else:
                if log_level >= LogLevels.VERBOSE and \
                        log_level <= LogLevels.VERY_VERBOSE:
                    if log_level >= Params.verbose_level:
                        write_message = True

        if write_message:
            sys.stdout.write(out_string)
                

    def raw_input(self, prompt=''):
        """
        Override the default raw_input to give a more intuative prompt.
        gsched> instead of the python standard >>>
        """
        return  InteractiveConsole.raw_input(self, prompt=self.prompt)
       


    def push(self, line):
        line = line.strip()
        if line == '':
            return
        line = self.eval_substitutions(line)
        user_in = line.split(" ")
        if Params.debug_level >= 1:
            print "DEBUG:",user_in
        action = user_in.pop(0)
        if action == 'pyex':
            self.write('VERBOSE DEBUG: %s\n' % user_in, 
                       LogLevels.VERBOSE_DEBUG)
            args = [' '.join(user_in)]
            self.write('VERBOSE DEBUG: %s\n' % args, 
                       LogLevels.VERBOSE_DEBUG)
        else:
            args = user_in
        if action != 'quit':
            try:
                self.execute_action(action, *args)
            except:
                traceback.print_exc(file=self)
        else:
            self.execute_action(action, *args)



    def pyex(self, *args):
        """Execute arbitray python expression.
            
        usage: pyex <arbitary-python-expression>
            
        This feature can be combined with the variable substitution
        feature. So that you can do :
        
        gsched> pyex cur_group = 'pipeline_group'
        gsched> group_info {cur_group}
        
        Since you have defined cur_group, it is now in the global name
        space. So the parser looks for patterns matching {<var-name>}
        and replaces those with the string representations of
        the variables value. Such that:
        
        gsched> group_info {cur_group}
        
        Becomes:
        
        gsched> group_info pipeline_group
        
        """
        py_expression = args[0]
        self.runcode(py_expression)
    
    def help(self, *args):
        """Prints this help menu, or help about a specific command.
            
        usage: help [command-name]
        """
        show_extended_help = False
    
        # Filter function sent to the python filter() function that
        # specifies to filter item_strings that start with an
        # underscore or if they are a hidden action and not accessable
        # to the user anyway.
        filter_func = lambda item_string: \
            not item_string.startswith("_") and \
            not item_string in self.hidden_actions
    
        # Obtain the list of attributes for this class as specified by
        # filter_func
        menu_actions = filter(filter_func, dir(self))
    
        if len(args) > 0:
            # Specific help has been requested filter the specific
            # help topics by seeing if they exist in the help topics.
            temp_actions = filter( lambda item_string: item_string in args,
                                       menu_actions)
            if len(temp_actions) > 0:
                # The user inputted 1 or more valid help topics,
                # swtich the actions to be printed to the valid user
                # inputted help topics. Then switch the output mode to
                # extended.
                menu_actions = temp_actions
                show_extended_help = True
    
        for action_name in menu_actions:
            # For all actions that are valid attributes of this class,
            # first obtain that attribute object. We hope that it is a
            # callable method.
            method = getattr(self, action_name)
            if callable(method):
                # Great it is a callable method and has passed all of
                # the other filtering of attributes that should not be
                # accessable by the user.
                    
                # Get the name of the method (name of the command)
                name = method.__name__
                # Get the docstring, which is used to generate the
                # help
                help_string = method.__doc__
                    
                if not show_extended_help:
                    # For the general help menu, just print out the
                    # one line summary of the help. There is a little
                    # string fomatting to make it easier to read.
                    help_string = help_string.split('\n')
                    if len(help_string) > 1:
                        help_string = help_string[0]
                        self.write(name.rjust(20)+" : ")
                        self.write(help_string.rjust(25)+"\n")
                else:
                    # The user has specified a help topic about which
                    # they want more information, so present all of
                    # the help information about the topic. Obviously
                    # formatted to be easier to read.
                    self.write('\nHelp for command: %s\n\n' % name)
                    for line in help_string.split('\n'):
                        line = line.strip()
                        self.write('    %s\n' % line)
    
    def quit(self, *args):
        """Immediately quit gschedsh.
        """
        sys.exit()


    def exit(self, *args):
        """Immediately exit gschedsh.
        """
        sys.exit()
    
        



    ##### END INTERACTIVE CONSOLE METHODS ####




    ##############################################
    # Private Methods -- Background helper routines for the public
    # callable routines (see gsmethods), Should not be callable by the
    # user.
    ##############################################

    def execute_action(self, action, *args):
        if hasattr(self, action) and \
                not action in self.hidden_actions:
            method = getattr(self, action)
            method(*args)
        else:
            self.write( "\nUnknown action: %s\n\n" 
                        "Please choose a valid command.\n\n"% action)
            self.help()

    def get_terminal_size():
        """Code found on stackoverflow.com that seems to be the
        generally accepted way to get the terminal size. May be used
        in the future for formatting output.
        """
        def ioctl_GWINSZ(fd):
            try:
                import fcntl, termios, struct, os
                cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ,
                                                     '1234'))
            except:
                return None
            return cr
        cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
        if not cr:
            try:
                fd = os.open(os.ctermid(), os.O_RDONLY)
                cr = ioctl_GWINSZ(fd)
                os.close(fd)
            except:
                pass
            if not cr:
                try:
                    cr = (env['LINES'], env['COLUMNS'])
                except:
                    cr = (25, 80)
        return int(cr[1]), int(cr[0])



    def eval_substitutions(self, line):
        start_brace = line.find('{')
        if start_brace < 0:
            return line

        end_brace = line.find('}')
        if end_brace < 0:
            return line

        raw_sub = line[start_brace:end_brace+1]
        sub_string = raw_sub[1:-1]
        self.write("VERBOSE DEBUG: Looking for substitution `%s'\n" % sub_string,
                   LogLevels.VERBOSE_DEBUG)
        if globals().has_key(sub_string):
            sub_string = str(globals()[sub_string])
            self.write("VERBOSE DEBUG: Substituting `%s'\n" % sub_string,
                   LogLevels.VERBOSE_DEBUG)
        

        line = line.replace(raw_sub, sub_string)
        return self.eval_substitutions(line)
    

    ######## END PRIVATE METHODS #############

