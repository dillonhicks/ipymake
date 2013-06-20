"""
:mod:`enforcetype` -- Streamlined Function Parameter Type Enforcement
==========================================================================
"""
from types import ClassType, InstanceType
class enforcetypes:
    """
    `enforcetypes` is a decorator class to simplify parameter checking.
    The `enforcetype` is a complex decorator that can take arguements.
    Each argument matches the desired type of that parameter at the 
    matching index of the **decorated** function. 
    
    If the function is a class method, the decorator wrapping makes
    sure to skip the automatic *self* parameter.

    And example below::
    
        @enforcetypes(str, int)
        def print_info(name, age):
            print "%s is %i years old." % (name, age)
   
    .. doctest::

        >>> print_info('dillon', 21)
        dillon is 21 years old.
        >>> print_info('dillon', 'twenty-one')
        TypeError: Parameter age (1) is not a valid type for hello(). 
            Got type str, but expected one of the following: int
        

     If you need more than one different type, you can also specify a
     list of types as a valid argument to the decorator::

         @enforcetypes(str, [int, str])
         def print_info(name, age):
             print "%s is %s years old." % (name, age)
                
    ... doctest::
        
        >>> print_info('dillon', 21)
        dillon is 21 years old.
        >>> print_info('dillon', 'twenty-one')
        dillon is twenty-one years old.
        >>> print_info('dillon', False)
        TypeError: Parameter age (1) is not a valid type for hello(). 
           Got type bool, but expected one of the following: int, str
        
    """
    def __init__(self, *type_rules):
        """
        Initializes the type rules for the function/method to be
        wrapped.
        """
        self.rules = []
        for rule in type_rules:
            if type(rule) is type or type(rule) is ClassType:
                # It is singly type, append it as a 1 element list,
                # this cleans up the code in __call__, by
                # standardizing all of the elements in rule to be
                # lists --even if they are one item.
                self.rules.append([rule])
            elif type(rule) is list:
                # Already a list, so we are good.  Check this later to
                # see of all rules in the list apply
                self.rules.append(rule)
                
            else:
                # Ugh, not a supported type, raise the flag.
                raise TypeError("Parameter %s is not a valid type for enforcetypes.__init__();"
                                " expected either a list, classobject or type types" % type(rule))
                    


    def __call__(self, method):
        import types        
        # (Instance) methods and functions vary slightly. Methods have
        # one extra step, but we just want the variable names from
        # the function/method.
        if type(method) is types.FunctionType:
            var_names = method.func_code.co_varnames
        else:
            var_names = method.im_func.func_code.co_varnames
    
        # This is the wrapper method that will be returned.
        def type_enforced_method(*args):
            
            # Go through the list or arguments sent to the method,
            # including their index.
            for i, arg in enumerate(args):
                    # First parameter for a method is most always
                    # 'self', we don't need to check that type, so
                    # skip it.
                if i == 0 and var_names[0] == 'self':
                    #skip self                                                                                                                            
                    continue
                
                # Making sure there are rules defined for the particular parameter i.
                if i < len(self.rules):
                    is_valid_type = False
                    rule = self.rules[i]
                    # We expect every rule to be a list of types, so
                    # iterate through them until a match with the type
                    # of the current arg is found.
                    for rule_type in rule: 
                        if type(rule_type) is type:
                            if type(arg) is rule_type:
                                is_valid_type = True
                                break
                                
                        elif type(rule_type) is types.ClassType:
                            if isinstance(arg, rule_type):
                                is_valid_type = True
                                break
                            
                           
                    if not is_valid_type:
                        # Blasts, not a correct type. Red alert, all
                        # men to battle stations, and most importantly
                        # raise the type error.
                        var_name = var_names[i]
                        if type(arg) is InstanceType:
                            type_name = arg.__class__.__name__
                        else:
                            type_name = type(arg).__name__
                        raise TypeError("Parameter %s (%i) is not a valid type for %s()."
                                        " Got type %s, but expected one of the following: %s" %
                                        (var_name, i, method.__name__, type_name,
                                        ', '.join([tp.__name__ for tp in rule])))
                    
                    
            return method(*args)

        # Make sure the wrapped method keeps the name and docstring of
        # the original method. Not keeping them may not cause
        # problems, but I would rather be safe.
        type_enforced_method.func_globals.update(method.func_globals)
        type_enforced_method.__name__ = method.__name__
        type_enforced_method.__doc__ = method.__doc__
        return type_enforced_method

