''' Requirements:
pip install cxxfilt
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
debug = True

# reference: http://matthiaseisen.com/articles/graphviz/

class BinocularsFlowgraph(BackgroundTaskThread):

    def __init__(self, bv, function, *args, **kwargs):
        BackgroundTaskThread.__init__(self, '', True)
        self.progress = "Binoculars Flowgraph Running..."
        self.bv = bv
        self.function = function
        # demangle type can be cppfilt, bn, None
        self.demangle = kwargs.get('demangle')

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
        g = graphviz.Digraph(format='png')
        flowgraph = self.build_flowgraph_to_bin()

        for node in flowgraph.keys():
            debug and print('Node: {}'.format(node))

            g.node(node)
            dst = node
            for src in flowgraph[dst]:
                g.edge(src, dst)

        styles = self.get_styles('flowgraph')
        g = self.apply_styles(g, styles)
        g.view(directory=GRAPHVIZ_OUTPUT_PATH)

    def view_flowgraph_to_function(self):
        g = graphviz.Digraph(format='png')
        filename = "{}-{}".format(os.path.basename(self.bv.file.filename),
            self.__get_demangled(self.function.symbol.name))

        fullpath = os.path.join(tempfile.gettempdir(), filename)

        flowgraph = {}
        self.build_flowgraph_to_function_recursive(self.function, flowgraph)
        for node in flowgraph.keys():
            g.node(node)
            dst = node
            for src in flowgraph[node].keys():
                for xref_addr in flowgraph[node][src]:
                    g.edge(src, dst, label=hex(xref_addr).replace("L", ""))
        styles = self.get_styles("flowgraph '%s'" % filename)
        g = self.apply_styles(g, styles)

        g.view(directory=GRAPHVIZ_OUTPUT_PATH)

        ''' Not working on Mac 10.15.3
        print(self.function.symbol.name)
        # Function name
        func_name = '{}'.format(self.function.symbol.name)
        print('Function name: {}'.format(func_name))

        # Prepend file path to name
        file_func = "%s-%s" % (os.path.basename(self.bv.file.filename), func_name)
        #filename = "%s-%s" % (os.path.basename(self.bv.file.filename), self.function.symbol.name)
        print('file_func: {}'.format(file_func))

        fullpath = os.path.join(tempfile.gettempdir(), file_func)
        print('Full path: '.format(fullpath))

        graphviz_name = g.render(fullpath)
        print('graphviz_name: {}'.format(graphviz_name))

        output = """
        <html>
        <title></title>
        <body>
        <div align='center'>
            <img src="{}"/>
        </div>
        <body>
        </html>
        """.format(graphviz_name)
        print('output\n{}'.format(output))
        show_html_report("Binoculars Flowgraph (this function)", output)
        '''

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
            pretty_name = self.__get_demangled(function.symbol.name)
            #pretty_name = function.symbol.name

            flowgraph[pretty_name] = []

            for xref in self.bv.get_code_refs(function.symbol.address):
                pretty_name_xref = self.__get_demangled(xref.function.symbol.name)
                #pretty_name_xref = xref.function.symbol.name

                if pretty_name_xref not in flowgraph[pretty_name]:
                    debug and print('pretty_name: {}, before: {}'.format(pretty_name, function.symbol.name))
                    debug and print('pretty_name_xref: {}, before: {}'.format(pretty_name_xref, xref.function.symbol.name))
                    flowgraph[pretty_name].append(pretty_name_xref)

        return flowgraph


    def build_flowgraph_to_function_recursive(self, function, flowgraph):
        if function.symbol.name not in flowgraph.keys():
            pretty_name = self.__get_demangled(function.symbol.name)
            flowgraph[pretty_name] = {}

        for xref in self.bv.get_code_refs(function.symbol.address):
            pretty_name_xref = self.__get_demangled(xref.function.symbol.name)

            if pretty_name_xref not in flowgraph[pretty_name].keys():
                flowgraph[pretty_name][pretty_name_xref] = []

            if xref.address not in flowgraph[pretty_name][pretty_name_xref]:
                flowgraph[pretty_name][pretty_name_xref].append(xref.address)

            self.build_flowgraph_to_function_recursive(xref.function, flowgraph)


    def run(self):
        if self.function == None:
            self.view_flowgraph_to_bin()
        else:
            self.view_flowgraph_to_function()
