"""
==============================================================
:mod:`ccsmgraphviz` -- Pygraphviz Utilites for :mod:`pyccm` 
==============================================================
    :synopsis: 
    
.. moduleauthor:: Dillon Hicks <hhicks@ittc.ku.edu>

**Current Version: 1.0** 

:class:`CCSMSet` objects to Graphs
===================================

.. todo:: Write small how to on CCSM Graphs.


Graphs to Images
=======================================

.. todo:: Write small how to on CCSM Graphs.


Module Changes
================

*Version* *(YYYY-MM-DD)*: *Changes*
    
* 1.0 (2009-10-11): First completed version

"""
from ccsmstructures import *
from pygraphviz import *

def graph_from_ccsmh(root_node):
    """
    Creates a `pygraphviz.AGraph` from a `CCSMSet` or `CCSMHierarchy`. 

    This method can accept either a `ccsmstructures.CCSMHierarchy` or a
    `ccsmstructures.CCSMSet` object as the root_node. From the root_node it
    analyzes the Set->Child-Set relationship that the hierarchy 
    represents and uses `pygraphviz` to create an `pygraphviz.AGraph` object
    which can be used in a variety of ways by the `pygraphviz` API.
        
    :param root_node: The CCSM Hierarchy or Set from which to make the graph.
    :etype root_node: `CCSMSet` or `CCSMHierarchy`
    :returns: The graph of the CCSM Hierarchy from root_node
    :return type: `pygraphviz.AGraph`
    """
    
    if isinstance(root_node, CCSMSet):
        root_node = root_node.get_root_set()
    elif not isinstance(root_node, CCSMSet):
        raise TypeError('ccsmgraphviz (1): root_node is not a CCSMSet or CCSMHierarchy'
                        ' instance.', root_node )
    
    ccsm_graph = AGraph()
    
    def create_graph_R(set):
    # Hidden/Anonymous inner function
    # that recurses the CCSM Hierarchy 
        
        set_name = set.get_name()
        for mem in set.get_set_members():
            # For each of the sets child 
            # members.
            child_name = mem.get_name()
            ccsm_graph.add_edge(set_name, 
                               child_name)
            # mem is a CCSMSet so call create_graph_R
            # with mem, to add all of its child members
            # to the graph.
            create_graph_R(mem)            
            
    create_graph_R(root_node)
    return ccsm_graph


def create_image_from_ccsmh(root_node, layout_prog='dot', outpath=None ):
    """
    Create an image from a `CCSMSet` or a `CCSMHierarchy` object.
    
    The standard image is a PNG image, with a standard *tree* look. 
    The image type is based on the extension of the file specified by 
    outpath.
    
    :param root_node: The root of the Hierarchy.
    :type root_node: CCSMSet or CCSMHierarchy
    :param layout_prog: The graphviz layout program to use to layout 
        the Hierarchy AGraph before drawing.
    :type layout_prog: string
    
    """
    if isinstance(root_node, CCSMSet):
        root_node = root_node.get_root_set()
    elif not isinstance(root_node, CCSMSet):
        raise TypeError('ccsmgraphviz (2): root_node is not a CCSMSet or CCSMHierarchy'
                        ' instance.', root_node )
    
    if outpath is None:
        outpath = "%s_graph.png" % root_node.get_name()
    
    
    graph = graph_from_ccsmh(root_node)
    graph.layout(prog=layout_prog)
    graph.draw(outpath)

if __name__=="__main__":
    import ccsmprocutils as ccsmproc
    sets = ccsmproc.parse()
    for set in sets:
        create_image_from_ccsmh(set)
