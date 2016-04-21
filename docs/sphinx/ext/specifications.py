from input_algorithms.spec_base import default_specs

from docutils.statemachine import ViewList
from sphinx.util.compat import Directive
from textwrap import dedent
from docutils import nodes
import six

class ShowSpecsDirective(Directive):
    """Directive for outputting all the specs found in input_algorithms.spec_base.default_specs"""
    def run(self):
        section = nodes.section()
        section['ids'].append("default-specs")
        for name, spec in default_specs.items():

            title = nodes.title()
            title += nodes.Text(name)
            section += title

            viewlist = ViewList()
            for line in dedent(spec.__doc__).split("\n"):
                if line:
                    viewlist.append("    {0}".format(line), name)
                else:
                    viewlist.append("", name)
            self.state.nested_parse(viewlist, self.content_offset, section)
        return [section]

def setup(app):
    """Setup the show_specs directive"""
    app.add_directive('show_specs', ShowSpecsDirective)

