from binaryninja import *
from .flowgraph import *
from .list_comments import *
from .textify_function import *



def __flowgraph(bv, function):
    flowgraph = BinocularsFlowgraph(bv, None)
    flowgraph.start()

def __flowgraph_to_function(bv, function):
    flowgraph = BinocularsFlowgraph(bv, function)
    flowgraph.start()

def __flowgraph_cppfilt(bv, function):
    flowgraph = BinocularsFlowgraph(bv, None, demangle='cppfilt')
    flowgraph.start()

def __flowgraph_to_function_cppfilt(bv, function):
    flowgraph = BinocularsFlowgraph(bv, function, demangle='cppfilt')
    flowgraph.start()

def __flowgraph_bn(bv, function):
    flowgraph = BinocularsFlowgraph(bv, None, demangle='bn')
    flowgraph.start()

def __flowgraph_to_function_bn(bv, function):
    flowgraph = BinocularsFlowgraph(bv, function, demangle='bn')
    flowgraph.start()

def __list_comments(bv):
    list_comments = BinocularsListComments(bv)
    list_comments.start()

def __textify_function(bv, function):
    textify_function = BinocularsTextifyFunction(bv, function)
    textify_function.start()

# UI menu items
PluginCommand.register(
    "[BINoculars]\\List Comments",
    "",
    __list_comments
)

PluginCommand.register_for_function(
    "[BINoculars]\\Textify Function",
    "",
    __textify_function
)

PluginCommand.register_for_function(
    "[BINoculars]\\Flowgraph\\All\\raw",
    "Best integrity",
    __flowgraph
)

PluginCommand.register_for_function(
    "[BINoculars]\\Flowgraph\\Function\\raw",
    "Best integrity",
    __flowgraph_to_function
)

PluginCommand.register_for_function(
    "[BINoculars]\\Flowgraph\\All\\bn",
    "",
    __flowgraph_bn
)

PluginCommand.register_for_function(
    "[BINoculars]\\Flowgraph\\Function\\bn",
    "",
    __flowgraph_to_function_bn
)

# Only display menu option if module installed
try:
    import cxxfilt

    PluginCommand.register_for_function(
        "[BINoculars]\\Flowgraph\\All\\c++filt",
        "",
        __flowgraph_cppfilt
    )

    PluginCommand.register_for_function(
        "[BINoculars]\\Flowgraph\\Function\\c++filt",
        "",
        __flowgraph_to_function_cppfilt
    )

except ImportError:
    print('cxxfilt not installed')
