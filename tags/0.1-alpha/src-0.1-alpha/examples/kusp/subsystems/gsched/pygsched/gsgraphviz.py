"""
:mod:`gsgraphviz` -- Gsched Pygraphviz Utilites
================================================
    :synopsis: Specialized pygraphvis wrapper utilites for creating graphs 
        and images of Group Scheduling Hierarchies.

.. moduleauthor:: Dillon Hicks <hhicks@ittc.ku.edu>


Group Scheduling Hierarchies are best visualized using    Directed
Graphs. The top-down/parent-child relationships in Group Scheduling make its 
Tree like nature  easy to graph this way.  Using Pygraphviz, :mod:`gsgraphviz` 
creates Graphviz style graph images of Group Scheduling Hierarchies. 

.. contents::

:func:`dotfile_from_configfile` 
----------------------------------

.. autofunction:: gsgraphviz.dotfile_from_configfile


:func:`dotfile_from_gsh`
--------------------------

.. autofunction:: gsgraphviz.dotfile_from_gsh


:func:`graph_from_configfile` 
--------------------------------

.. autofunction:: gsgraphviz.graph_from_configfile



:func:`graph_from_gsh` 
------------------------

.. autofunction:: gsgraphviz.graph_from_gsh


:func:`image_from_gsh` 
-----------------------

.. autofunction:: gsgraphviz.image_from_gsh



"""

#not included in autodocs
"""
**Current Version 1.0**

"""

from pygraphviz import *
from gshierarchy import GSHierarchy, GSGroup, GSThread
import pykusp.configutility as config

# To (hopefully) be used in the future to create 
# cooler graphs by giving them specific drawing attributes.
edge_settings = {
                  'color' : 'black',
                  'arrowhead' : 'normal'
                }
                   

def graph_from_configfile(configfile):
    """
    Creates a `pygraphviz.AGraph` from a Group Scheduling Hierarchy 
    configuration file (.gsh) by parsing `configfile` into a 
    :class:`GSHierachy` object before it is then used by 
    :func:`graph_from_gsh` to make the graph.
    
    :param configfile: The path to the .gsh configuration file
        from which to make a graph.
    :type configfile: string
    :returns: An AGraph that represents the hierarchy described by 
        the configuration file.
    :rtype: `pygraphviz.AGraph`
    
    """
    gsh_dict = config.parse_configfile(configfile)
    gsh = GSHierarchy(gsh_dict)
    return graph_from_gsh(gsh)


def dotfile_from_configfile(configfile, outfile=None):
    """
    Creates a dotfile from a Group Scheduling 
    configuration file (.gsh).
    """
    gsh_dict = config.parse_configfile(configfile)
    gsh = GSHierarchy(gsh_dict)
    create_dotfile_from_gsh(gsh,outfile=outfile)

def graph_from_gsh(root_node):
    """
    Creates a `GSGraph` from a GSGroup or GSHierarchy. 

    This method can accept either a `gsstructures.GSHierarchy` or a
    `gsstructures.GSGroup` object as the root_node. From the root_node it
    analyzes the Group->Member relationship that the hierarchy 
    represents and uses `pygraphviz` to create an `pygraphviz.AGraph` object
    which can be used in a variety of ways by the `pygraphviz` API.
        
    :param root_node: The Group Scheduling Hierarchy or Group from which to make the graph.
    :etype root_node: `GSGroup` or `GSHierarchy`
    :returns: The graph of the Group Scheduling Hierarchy from root_node
    :return type: `pygraphviz.AGraph`
    """
    
    if isinstance(root_node, GSHierarchy):
        root_node = root_node.get_root_group()
    elif not isinstance(root_node, GSGroup):
        raise TypeError('gsgraphviz (1): root_node is not a GSGroup or GSHierarchy'
                        ' instance.', root_node )
    
    gsh_graph = AGraph(directed=True)
    
    def create_graph_R(group):
    # Hidden/Anonymous inner function
    # that recurses the Group Scheduling Hierarchy 
        
        group_name = group.get_name()
        for mem in group.get_members():
            # For each of the groups child 
            # members.
            child_name = mem.get_name()
            gsh_graph.add_edge(group_name, 
                               child_name, **edge_settings)
            if isinstance(mem, GSGroup):
                # mem is a GSGroup so call create_graph_R
                # with mem, to add all of its child members
                # to the graph.
                create_graph_R(mem)            
            
    create_graph_R(root_node)
    return gsh_graph


def image_from_gsh(root_node, layout_prog='dot', outpath=None ):
    """
    Create an image from a `GSGroup` or a `GSHierarchy` object.
    
    The standard image is a PNG image, with a standard *tree* look. 
    The image type is based on the extension of the file specified by 
    outpath.
    
    :param root_node: The root of the Hierarchy.
    :type root_node: GSGroup or GSHierarchy
    :param layout_prog: The graphviz layout program to use to layout 
        the Hierarchy AGraph before drawing.
    :type layout_prog: string
    
    """
    if isinstance(root_node, GSHierarchy):
        root_node = root_node.get_root_group()
    elif not isinstance(root_node, GSGroup):
        raise TypeError('gsgraphviz (2): root_node is not a GSGroup or GSHierarchy'
                        ' instance.', root_node )
    
    if outpath is None:
        outpath = "%s_graph.png" % root_node.get_name()
    
    
    graph = graph_from_gsh(root_node)
    graph.layout(prog=layout_prog)
    graph.draw(outpath)
    
def dotfile_from_gsh(root_node, outpath=None):
    """
    Creates a dot file from a Group Scheduling Hierarchy.
    """
    if isinstance(root_node, GSHierarchy):  
        root_node = root_node.get_root_group()
    elif not isinstance(root_node, GSGroup):
        raise TypeError('gsgraphviz (3): root_node is not a GSGroup or GSHierarchy'
                        ' instance.', root_node )
    
    if outpath is None:
        outpath = "%s.dot" % root_node.get_name()
        
    graph = graph_from_gsh(root_node)
    graph.write(outpath)


if __name__=="__main__":
    import gsprocutils as gsproc
    current_hierarchy = gsproc.parse()
    image_from_gsh(current_hierarchy, outpath='./graphviz_test.svg')
    image_from_gsh(current_hierarchy, layout_prog='neato'
                         ,outpath='./graphviz_test_neato.png')
    image_from_gsh(current_hierarchy, layout_prog='fdp',
                          outpath='./graphviz_test_fdp.png')
    image_from_gsh(current_hierarchy, layout_prog='twopi',
                          outpath='./graphviz_test_twopi.png')
    image_from_gsh(current_hierarchy, layout_prog='circo', 
                          outpath='./graphviz_test_circo.png')
    
    dotfile_from_gsh(current_hierarchy)


