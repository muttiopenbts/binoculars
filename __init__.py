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

def __flowgraph_from_function_bn(bv, function):
    flowgraph = BinocularsFlowgraph(bv, function, method='from_function', demangle='bn')
    flowgraph.start()

def __flowgraph_from_function_raw(bv, function):
    flowgraph = BinocularsFlowgraph(bv, function, method='from_function', demangle='raw')
    flowgraph.start()

def __flowgraph_from_function_cppfilt(bv, function):
    flowgraph = BinocularsFlowgraph(bv, function, method='from_function', demangle='cppfilt')
    flowgraph.start()

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
    "[BINoculars]\\Flowgraph\\Binary\\Raw",
    "Best integrity",
    __flowgraph
)

PluginCommand.register_for_function(
    "[BINoculars]\\Flowgraph\\Function to\\Raw",
    "Best integrity",
    __flowgraph_to_function
)

PluginCommand.register_for_function(
    "[BINoculars]\\Flowgraph\\Binary\\Bn",
    "",
    __flowgraph_bn
)

PluginCommand.register_for_function(
    "[BINoculars]\\Flowgraph\\Function to\\Bn",
    "",
    __flowgraph_to_function_bn
)

PluginCommand.register_for_function(
    "[BINoculars]\\Flowgraph\\Function from\\Raw",
    "",
    __flowgraph_from_function_raw
)

PluginCommand.register_for_function(
    "[BINoculars]\\Flowgraph\\Function from\\Bn",
    "",
    __flowgraph_from_function_bn
)

# Only display menu option if module installed
try:
    import cxxfilt

    PluginCommand.register_for_function(
        "[BINoculars]\\Flowgraph\\Binary\\C++filt",
        "",
        __flowgraph_cppfilt
    )

    PluginCommand.register_for_function(
        "[BINoculars]\\Flowgraph\\Function to\\C++filt",
        "",
        __flowgraph_to_function_cppfilt
    )

    PluginCommand.register_for_function(
        "[BINoculars]\\Flowgraph\\Function from\\C++filt",
        "",
        __flowgraph_from_function_cppfilt
    )

except ImportError:
    print('cxxfilt not installed')
