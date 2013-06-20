"""
:mod:`gsnetworkx` -- Gsched NetworkX Utilities 
=========================================================

.. moduleauthor:: Dillon Hicks <hhicks@ittc.ku.edu>

Group Scheduling Hierarchies are best visualized using Directed
Graphs. The top-down/parent-child relationships in Group Scheduling
make its Tree like nature easy to graph this way.  Using NetoworkX,
:mod:`gsnetworkx` creates NetworkX graph images of Group Scheduling
Hierarchies. The :mod:`gsnetworkx` module is used by the
:command:`gssnapshot` to create the graphs of system hierarchies.


.. contents::


**Global Drawing Settings:**

.. attribute:: drawing_settings
 
    Used to make specific graph looks by modifying their drawing attributes.
   
    +-------------+------------+----------------------------------------+
    | Setting     |  Default   |    Description                         |
    +-------------+------------+----------------------------------------+
    | arrowstyle  |  '-|>'     |  The style or arrow used by edges to   |
    |             |            |connect nodes.                          |
    +-------------+------------+----------------------------------------+
    | style       |  'dotted'  | How to draw the edge.                  |
    |             |            |                                        |
    +-------------+------------+----------------------------------------+
    | node_shape  |   'o'      | The shape of the node.                 |
    +-------------+------------+----------------------------------------+
    | node_size   |   10000    | Relative size of the node.             |
    +-------------+------------+----------------------------------------+
    | font_size   |   12       |                                        |
    +-------------+------------+----------------------------------------+
    | alpha       |   0.6      | Alpha level for the node fill color.   |
    +-------------+------------+----------------------------------------+
    | width       |   4        | Width of an edge.                      |
    +-------------+------------+----------------------------------------+
    | cmap        |  Oranges   | matplotlib.pyplot.cm.Oranges           |
    +-------------+------------+----------------------------------------+
    | font_wieght |   'bold'   | Normal font attributes (bold, itallic) |
    +-------------+------------+----------------------------------------+
  

 
.. attribute:: node_settings
    
    Drawing Settings for nodes.
    
.. attribute:: edge_settings

    Drawing Settings for edges

.. attribute:: figure_settings

    Matplotlib settings for the output canvas.
    
.. attribute:: graph_wide_settings

    Graph wide drawing settings.


:func:`graph_from_configfile` 
-----------------------------------------

..  autofunction:: graph_from_configfile



:func:`graph_from_gsh`
------------------------------------

.. autofunction:: graph_from_gsh


:func:`image_from_configfile` 
------------------------------------------

.. autofunction:: image_from_configfile

:func:`image_from_graph` 
------------------------------------

.. autofunction:: image_from_graph


:func:`image_from_gsh` 
-----------------------------------

.. autofunction:: image_from_gsh


Example Use
--------------


To print  the current */proc/group_sched* as a graph image, you first would to parse */proc/group_sched* into a :class:`gsstructures.GSHierarchy`.


   
   >>> import pygsched.gsprocutils as gsproc
   >>> import pygsched.gsnetworkx as gsnx
   >>> gsh = gsproc.parse()
   >>> gsnx.image_from_gsh(gsh, outpath='just_a_test.svg')

"""

import networkx as nx
from gshierarchy import GSGroup, GSThread, GSHierarchy
import pykusp.configutility as config
import matplotlib.pyplot as plt

drawing_settings = {
                    'arrowstyle': '-|>',
                    'node_shape' :  'o',
                    'node_size' : 10000,
                    'font_size' : 12,
                    'style' : 'dotted',
                    'alpha' : 0.6,
                    'width'      : 4,
                    'cmap'  : plt.cm.Oranges,
                    'font_weight' : 'bold'
                    }

edge_settings = {
    'color' : 'black'
    
}

node_settings ={
    'style' : 'filled',
    'fillcolor' : 'aliceblue',
    'shape'  : 'rectangle'
}

figure_settings = {
                 'figsize' : (46,20),
                 'facecolor' : 'w',
                 'edgecolor' : 'k'
                 }

graph_wide_settings = {
                 'colorscheme' : 'X11',

}


def graph_from_configfile(configfile):
    """
    Creates a :class:`NetworkX.DiGraph` from a Group Scheduling Hierarchy 
    configuration file (.gsh).
    
    :param configfile: The path to the .gsh configuration file
        from which to make a graph.
    :type configfile: string
    :returns: An AGraph that represents the hierarchy described by 
        the configuration file.
    :rtype: `networkx.DiGraph`
    
    """
    gsh_dict = config.parse_configfile(configfile)
    gsh = GSHierarchy(gsh_dict)
    return graph_from_gsh(gsh)


def graph_from_gsh(gsh):
    """
    Creates a :class:`networkx.DiGraph` from :class:`gsstructures.GSGroup` or a 
    :class:`gsstructures.GSHierarchy`.
     
    This method can accept either a :class:`gsstructures.GSHierarchy` or a
    :class:`gsstructures.GSGroup` object as the root_node. From the root_node it
    analyzes the Group->Member relationship that the hierarchy 
    represents and uses :mod:`NetworkX` to create a :class:`networkx.DiGraph` object
    which can be used in a variety of ways by the `NetworkX` API.
        
    :param root_node: The Group Scheduling Hierarchy or Group from which to make the graph.
    :type root_node: :class:`gsstructures.GSHierarchy` or :class:`gsstructures.GSGroup`
    :returns: The graph of the Group Scheduling Hierarchy from root_node
    :return type: :class:`networkx.DiGraph`
    """
    
#    if isinstance(root_node, GSHierarchy):
#        #root_node = root_node.get_super_root()
    if not isinstance(gsh, GSHierarchy):
        raise TypeError('gsnetworkx (1): gsh is not a GSHierarchy'
                        ' instance.', gsh )
    
    gsh_graph = nx.DiGraph()
    for member in gsh.get_members():
        gsh_graph.add_node(member)
    
    def create_graph_R(group):
    # Hidden/Anonymous inner function
    # that recurses the Group Scheduling Hierarchy 
        for mem in group.get_members():
            # For each of the groups child 
            # members.
            gsh_graph.add_edge(group, 
                               mem)
            if isinstance(mem, GSGroup):
                # mem is a GSGroup so call create_graph_R
                # with mem, to add all of its child members
                # to the graph.
                create_graph_R(mem)            
            
    create_graph_R(gsh.get_root_group())
    return gsh_graph


def image_from_gsh(gsh, layout_prog='dot', outpath=None ):
    """
    Create an image from a :class:`gsstructures.GSGroup` or a 
    :class:`gsstructures.GSHierarchy`.
    
    The standard image is a PNG image, with a standard *tree* look. 
    The image type is based on the extension of the file specified by 
    outpath.
    
    :param root_node: The root of the Hierarchy.
    :type root_node: GSGroup or GSHierarchy
    :param layout_prog: The graphviz layout program to use to layout 
        the Hierarchy AGraph before drawing.
    :type layout_prog: string
    
    """
    graph = graph_from_gsh(gsh)
    image_from_graph(graph, layout_prog, outpath)

def image_from_configfile(configfile, layout_prog='dot', 
                                 outpath=None ):
    """
    Create an image from a Group Scheduling configuration file (.gsh).
    
    The standard image is a PNG image, with a standard *tree* look. 
    The image type is based on the extension of the file specified by 
    outpath.
    
    :param root_node: The root of the Hierarchy.
    :type root_node: GSGroup or GSHierarchy
    :param layout_prog: The graphviz layout program to use to layout 
        the Hierarchy AGraph before drawing.
    :type layout_prog: string
    
    """
    graph = graph_from_configfile(configfile)
    image_from_graph(graph, layout_prog, outpath)


def image_from_graph(graph, layout_prog='dot', outpath=None):
    """
    Create an image from a :class:`NetworkX.DiGraph`.
    
    The standard image is a PNG image, with a standard *tree* look. 
    The image type is based on the extension of the file specified by 
    outpath.
    
    :param root_node: The root of the Hierarchy.
    :type root_node: GSGroup or GSHierarchy
    :param layout_prog: The graphviz layout program to use to layout 
        the Hierarchy AGraph before drawing.
    :type layout_prog: string
    
    """
    if outpath is None:
        outpath = "%s_nxgraph.svg" % root_node.get_name()


#
#    Commented out here is the code that creates the Image
#    by using the graphviz backend of NetworkX.
#
#    agraph = nx.to_agraph(graph)
#    agraph.graph_attr.update(**graph_wide_settings)
#    agraph.node_attr.update(**node_settings)
#    agraph.edge_attr.update(**edge_settings)
#    agraph.layout(prog=layout_prog)
#    agraph.draw('other_'+outpath)
    pos=nx.graphviz_layout(graph, prog=layout_prog)
    plt.figure(**figure_settings)
    nx.draw(graph, pos, node_color=range(graph.number_of_nodes()),
            **drawing_settings)
    plt.savefig(outpath)




if __name__=="__main__":
    import gsprocutils as gsproc
    current_hierarchy = gsproc.parse()
    image_from_gsh(current_hierarchy, outpath='networkx_test_sys.svg')
    


