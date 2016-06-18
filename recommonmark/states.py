"""Implement statemachine and state that are needed to Generate Derivatives."""
from docutils.statemachine import StateMachineWS
from docutils.parsers.rst import languages
from docutils.parsers.rst.states import Struct, RSTState, Inliner
from docutils.parsers.rst.roles import role
from docutils.parsers.rst.directives import directive


class DummyStateMachine(StateMachineWS):

    """A dummy state machine that mimicks the property of statemachine.

    This state machine cannot be used for parsing, it is only used to generate
    directive and roles. Usage:
    - Call `reset` to reset the state
    - Then call `run_directive` or `run_role` to generate the node.
    """

    def __init__(self):
        self.memo = Struct(title_styles=[],
                           inliner=None)
        self.state = RSTState(self)
        self.input_offset = 0

    def reset(self, document, parent, level):
        """Reset the state of state machine.

        After reset, self and self.state can be used to
        passed to docutils.parsers.rst.Directive.run

        Parameters
        ----------
        document: docutils document
            Current document of the node.
        parent: parent node
            Parent node that will be used to interpret role and directives.
        level: int
            Current section level.
        """
        self.language = languages.get_language(
            document.settings.language_code)
        # setup memo
        self.memo.document = document
        self.memo.reporter = document.reporter
        self.memo.language = self.language
        self.memo.section_level = level
        # setup inliner
        if self.memo.inliner is None:
            self.memo.inliner = Inliner()
            self.memo.inliner.init_customizations(document.settings)
        inliner = self.memo.inliner
        inliner.reporter = document.reporter
        inliner.document = document
        inliner.language = self.language
        inliner.parent = parent
        # setup self
        self.document = document
        self.reporter = self.memo.reporter
        self.node = parent
        self.state.runtime_init()
        self.input_lines = document['source']

    def run_directive(self, name,
                      arguments=None,
                      options=None,
                      content=None):
        """Generate directive node given arguments.

        Parameters
        ----------
        name : str
            name of directive.
        arguments : list
            list of positional arguments.
        options : dict
            key value arguments.
        content : content
            content of the directive

        Returns
        -------
        node : docutil Node
            Node generated by the arguments.
        """
        if options is None:
            options = {}
        if content is None:
            content = []
        if arguments is None:
            arguments = []
        direc, msg = directive(name,
                               self.language,
                               self.document)
        direc = direc(name=name,
                      arguments=arguments,
                      options=options,
                      content=content,
                      lineno=self.node.line,
                      content_offset=0,
                      block_text='Dummy BlockText',
                      state=self.state,
                      state_machine=self)
        return direc.run()

    def run_role(self, name,
                 options=None,
                 content=None):
        """Generate a role node.

        options : dict
            key value arguments.
        content : content
            content of the directive

        Returns
        -------
        node : docutil Node
            Node generated by the arguments.
        """
        if options is None:
            options = {}
        if content is None:
            content = []
        role_fn, msg = role(name,
                            self.language,
                            self.node.line,
                            self.reporter)
        # add decode from utf-8
        content = content.encode('utf-8')
        content = content.decode('utf-8')
        vec, msg = role_fn(name,
                           rawtext=content,
                           text=content,
                           lineno=self.node.line,
                           inliner=self.memo.inliner,
                           options=options,
                           content=content)
        assert len(vec) == 1, 'only support one list in role'
        return vec[0]

    def get_source_and_line(self, lineno=None):
        if lineno:
            return (self.document['source'], lineno)
        else:
            return (self.document['source'], self.node.line)
