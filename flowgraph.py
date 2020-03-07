''' Requirements:
pip install cxxfilt
pip install tco

reference: http://matthiaseisen.com/articles/graphviz/
'''
from binaryninja import *
import graphviz
import tempfile


try:
    import cxxfilt

except ImportError:
    print('cxxfilt not installed')

import os
os.environ['PATH'] += os.pathsep + '/usr/local/bin/'
GRAPHVIZ_OUTPUT_PATH = '/tmp/'
debug = False


class BinocularsFlowgraph(BackgroundTaskThread):

    def __init__(self, bv, function, *args, **kwargs):
        BackgroundTaskThread.__init__(self, '', True)
        self.progress = "Binoculars Flowgraph Running..."
        self.bv = bv
        self.function = function
        # demangle type can be cppfilt, bn, None
        self.demangle = kwargs.get('demangle')
        '''Caller can specify which method to invoke.'''
        self.method = kwargs.get('method')

    def get_styles(self, label):
        styles = {
            'graph': {
                'label': label,
                'fontsize': '16',
                'fontcolor': 'white',
                #'bgcolor': '#333333',
                'bgcolor': '#101010',
                #'rankdir': 'LR',
            },
            'nodes': {
                'fontname': 'Helvetica',
                'shape': 'box',
                'fontcolor': 'white',
                'color': 'white',
                'style': 'filled',
                'fillcolor': '#006699',
            },
            'edges': {
                #'style': 'dashed',
                'color': 'white',
                'arrowhead': 'open',
                'fontname': 'Courier',
                'fontsize': '12',
                'fontcolor': 'white',
            }
        }
        return styles

    def apply_styles(self, graph, styles):
        graph.graph_attr.update(('graph' in styles and styles['graph']) or {})
        graph.node_attr.update(('nodes' in styles and styles['nodes']) or {})
        graph.edge_attr.update(('edges' in styles and styles['edges']) or {})
        return graph

    def view_flowgraph_to_bin(self):
        flowgraph = self.build_flowgraph_to_bin()
        self.draw_graph(flowgraph)


    def view_flowgraph_to_function(self):
        flowgraph = {}

        self.build_flowgraph_to_function(self.function, flowgraph)
        self.draw_graph(flowgraph)


    def view_flowgraph_from_function(self):
        flowgraph = {}

        self.build_flowgraph_from_function(self.function, flowgraph)
        self.draw_graph(flowgraph, forwards=True)


    def draw_graph(self, flowgraph, forwards=False):
        g = graphviz.Digraph(format='png')
        filename = None

        if hasattr(self.function, 'symbol'):
            filename = "{}-{}".format(os.path.basename(self.bv.file.filename),
                self.__get_demangled(self.function.symbol.name))

            fullpath = os.path.join(tempfile.gettempdir(), filename)


        for node in flowgraph.keys():
            g.node(node)
            dst = node
            debug and print('node: {}'.format(node))

            if not isinstance(flowgraph[node],dict):
                continue

            for src in flowgraph[node].keys():
                debug and print('src: {}'.format(src))
                for xref_addr in flowgraph[node][src]:
                    debug and print('xref_addr: {}'.format(xref_addr))
                    if forwards:
                        g.edge(dst, src, label=hex(xref_addr).replace("L", ""))
                    else:
                        g.edge(src, dst, label=hex(xref_addr).replace("L", ""))

        debug and print('g: {}'.format(g))

        styles = self.get_styles('Flowgraph {}'.format(filename))
        g = self.apply_styles(g, styles)

        g.view(directory=GRAPHVIZ_OUTPUT_PATH)

    '''https://en.wikipedia.org/wiki/Name_mangling
    graphviz doesn't like colons in node names. This function tries to address
    this.
    '''
    def __get_demangled_bn(self, name):
        return_pretty_name = None
        demangle_name = None

        if name and name.find('__Z', 0, 3) > -1:
            # Test for gnu3 style names __Z
            type, demangle_name = demangle_gnu3(self.bv.arch, name)

        elif name and name.find('?', 0, 1) > -1:
            # Test for msvc++ names ?funcname
            # TODO: improve match with regex
            type, demangle_name = demangle_ms(self.bv.arch, name)

        if demangle_name:
            return_pretty_name = get_qualified_name(demangle_name)
        else:
            return_pretty_name = name

        return return_pretty_name


    '''https://en.wikipedia.org/wiki/Name_mangling
    graphviz doesn't like colons in node names. This function tries to address
    this.
    '''
    def __get_demangled_filt(self, name):
        return_pretty_name = None

        try:
            return_pretty_name = cxxfilt.demangle(name, external_only=False)
        except:
            return_pretty_name = name

        return return_pretty_name


    def __get_demangled(self, name):
        if self.demangle == 'cppfilt':
            return_pretty_name = self.__get_demangled_filt(name)

        elif self.demangle == 'bn':
            return_pretty_name = self.__get_demangled_bn(name)

        else:
            return_pretty_name = name

        # Graphviz doesn't like colons in names
        return_pretty_name = return_pretty_name.replace(':','.')

        return return_pretty_name


    def build_flowgraph_to_bin(self):
        flowgraph = {}

        for function in self.bv.functions:
            pretty_name_function = self.__get_demangled(function.symbol.name)

            if pretty_name_function not in flowgraph.keys():
                flowgraph[pretty_name_function] = {}

            for xref in self.bv.get_code_refs(function.symbol.address):
                pretty_name_xref = self.__get_demangled(xref.function.symbol.name)

                # Find all xrefs to function.
                if pretty_name_xref not in flowgraph[pretty_name_function].keys():
                    # Add xref function name to base function
                    flowgraph[pretty_name_function][pretty_name_xref] = []

                if xref.address not in flowgraph[pretty_name_function][pretty_name_xref]:
                    # Add newly discovered xref address to xref function.
                    # Function can have multiple xrefs to it from the same xref function block.
                    flowgraph[pretty_name_function][pretty_name_xref].append(xref.address)

        return flowgraph


    def get_xrefs_to_function(self, function, flowgraph):
        '''Discover all xrefs to specified function. Not recursive.
        Returns:
            List of xref objects
            Updates flowgraph dictionay with new xrefs
                e.g. {'_lua_typename': {'_luaB_type': [4295090502],
                      '_typeerror': [4295080892],
                      '_tconcat': [4295128755, 4295128872],}}
        '''
        xref_list = []

        pretty_name_function = self.__get_demangled(function.symbol.name)

        if pretty_name_function not in flowgraph.keys():
            # Add function name to graph if not already stored
            flowgraph[pretty_name_function] = {}

            for xref in self.bv.get_code_refs(function.symbol.address):

                pretty_name_xref = self.__get_demangled(xref.function.symbol.name)

                # Find all xrefs to function.
                if pretty_name_xref not in flowgraph[pretty_name_function].keys():
                    # Add xref function name to base function
                    flowgraph[pretty_name_function][pretty_name_xref] = []

                if xref.address not in flowgraph[pretty_name_function][pretty_name_xref]:
                    # Add newly discovered xref address to xref function.
                    # Function can have multiple xrefs to it from the same xref function block.
                    flowgraph[pretty_name_function][pretty_name_xref].append(xref.address)
                    xref_list.append(xref)

            return xref_list if xref_list else None



    def build_flowgraph_to_function(self, function, flowgraph, debug=False):
        '''Builds a dictionary of xrefs to specified
        function, and repeats process of xrefs to discovered xrefs.

        Returns:
            None. Updates parameter dictionary flowgraph.
                Dictionary of all xrefs to function.
                Dictionary can be used for drawing graphviz.
        '''
        # Use this as a counter to prevent infinite loop.
        # TODO: Work towards removing hard_break.
        hard_break = 1000

        xrefs = self.get_xrefs_to_function(function,flowgraph)

        while xrefs:
            # Loops until xrefs list becomes empty or hard_break runs down.
            if hard_break < 1:
                break
            hard_break = hard_break - 1

            debug and print('xrefs len {}'.format(len(xrefs)))
            new_xrefs = self.get_xrefs_to_function(xrefs.pop().function,flowgraph)

            if new_xrefs:
                xrefs = new_xrefs + xrefs


    def build_flowgraph_from_function(self, function, flowgraph, debug=False):
        '''Iterate over every instuction address and check if address xrefs to
        other function.

            e.g. 0x1000000 call hi_func -> xref from current function to hi_func

        Arguments:

        Returns:
            xref_list. List of xrefs from function to code block.
            flowgraph. Updates by reference. Dictionary.
                e.g. {'main':'printf':[10001,10004]}
        '''
        xref_list = []

        pretty_name_function = self.__get_demangled(name=function.symbol.name)
        debug and print(pretty_name_function)

        if pretty_name_function not in flowgraph.keys():
            # Add function name to graph if not already stored
            flowgraph[pretty_name_function] = {}

        # Extract all code blocks from function block.
        basic_blocks = sorted(function.basic_blocks, key=lambda bb: bb.start)


        for basic_block in basic_blocks:
            for inst in basic_block.get_disassembly_text():
                if str(inst.tokens[0]) == function.name: continue

                xrefs = self.bv.get_code_refs_from(inst.address)
                debug and print('xref {}'.format(xrefs))

                #if xref:
                for xref in xrefs:
                    debug and print('xref\tfrom:{}\tto:{}'.format(hex(inst.address), hex(xref)))
                    xref_address = xref

                    # Attempt to convert address to symbol
                    xref_symbols = self.bv.get_functions_containing(xref)
                    debug and print('xref symbols {}'.format(xref_symbols))
                    if not xref_symbols:
                        continue

                    xref_symb = xref_symbols[0].symbol

                    pretty_name_xref = self.__get_demangled(name=xref_symb.name)
                    debug and print('xref symbol {}'.format(xref_symb))
                    debug and print('xref symbol {}'.format(pretty_name_xref))


                    if pretty_name_xref not in flowgraph[pretty_name_function].keys():
                        # Add xref function name to base function
                        flowgraph[pretty_name_function][pretty_name_xref] = []

                    if inst.address not in flowgraph[pretty_name_function][pretty_name_xref]:
                        # Add newly discovered xref address to xref function.
                        # Function can have multiple xrefs to it from the same xref function block.
                        flowgraph[pretty_name_function][pretty_name_xref].append(inst.address)
                        xref_list.append(xref)


        return xref_list if xref_list else None


    def build_flowgraph_to_function_recursive(self, function, flowgraph):
        # This function isn't reliable because of python's lmiitation with
        # recursion. System resources will be exhausted.
        pretty_name = self.__get_demangled(function.symbol.name)

        if pretty_name not in flowgraph.keys():
            flowgraph[pretty_name] = {}

        for xref in self.bv.get_code_refs(function.symbol.address):
            pretty_name_xref = self.__get_demangled(xref.function.symbol.name)

            if pretty_name_xref not in flowgraph[pretty_name].keys():
                flowgraph[pretty_name][pretty_name_xref] = []

            if xref.address not in flowgraph[pretty_name][pretty_name_xref]:
                flowgraph[pretty_name][pretty_name_xref].append(xref.address)

            self.build_flowgraph_to_function_recursive(xref.function, flowgraph)


    def run(self):
        if self.function and self.method == 'from_function':
            self.view_flowgraph_from_function()
        elif self.function == None:
            self.view_flowgraph_to_bin()
        else:
            self.view_flowgraph_to_function()
