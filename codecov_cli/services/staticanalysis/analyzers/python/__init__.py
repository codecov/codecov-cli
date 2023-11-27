import hashlib

from tree_sitter import Language, Parser

import staticcodecov_languages
from codecov_cli.services.staticanalysis.analyzers.general import BaseAnalyzer
from codecov_cli.services.staticanalysis.analyzers.python.node_wrappers import (
    NodeVisitor,
)
from codecov_cli.services.staticanalysis.types import FileAnalysisRequest

_function_query_str = """
(function_definition
  name: (identifier)
  parameters: (parameters)
) @elemen
"""

_unreachable_code_query_str = """
(function_definition
  body: (block (return_statement) @return_stmt . (_))
)
"""

_executable_lines_query_str = """
(block (_) @elem)
(expression_statement) @elemf
"""

_definitions_query_str = """
(function_definition) @elemc
(class_definition) @elemd
(decorated_definition) @eleme
"""

_imports_query_str = """
(import_statement) @elema
(import_from_statement) @elemb
"""

_wildcard_import_query_str = """
(wildcard_import) @elema
"""


class PythonAnalyzer(BaseAnalyzer):

    condition_statements = [
        "if_statement",
        "while_statement",
        "for_statement",
        "conditional_expression",
    ]
    wrappers = ["class_definition", "function_definition"]

    def __init__(
        self, file_analysis_request: FileAnalysisRequest, actual_code: bytes, **options
    ):
        self.actual_code = actual_code
        self.lines = self.actual_code.split(b"\n")
        self.statements = []
        self.import_lines = set()
        self.definitions_lines = set()
        self.functions = []
        self.path = file_analysis_request.result_filename
        self.PY_LANGUAGE = Language(staticcodecov_languages.__file__, "python")
        self.parser = Parser()
        self.parser.set_language(self.PY_LANGUAGE)
        self.line_surety_ancestorship = {}

    def process(self):
        function_query = self.PY_LANGUAGE.query(_function_query_str)
        definitions_query = self.PY_LANGUAGE.query(_definitions_query_str)
        imports_query = self.PY_LANGUAGE.query(_imports_query_str)
        tree = self.parser.parse(self.actual_code)
        root_node = tree.root_node
        captures = function_query.captures(root_node)
        for node, _ in captures:
            actual_name = self._get_name(node)
            body_node = node.child_by_field_name("body")
            self.functions.append(
                {
                    "identifier": actual_name,
                    "start_line": node.start_point[0] + 1,
                    "end_line": node.end_point[0] + 1,
                    "code_hash": self._get_code_hash(
                        body_node.start_byte, body_node.end_byte
                    ),
                    "complexity_metrics": self._get_complexity_metrics(body_node),
                }
            )
        visitor = NodeVisitor(self)
        visitor.start_visit(tree.root_node)
        self.functions = sorted(self.functions, key=lambda x: x["start_line"])

        self.import_lines = self.get_import_lines(root_node, imports_query)
        self.definitions_lines = self.get_definition_lines(root_node, definitions_query)

        h = hashlib.md5()
        h.update(self.actual_code)
        statements = self.get_statements()
        return {
            "language": "python",
            "empty_lines": [i + 1 for (i, n) in enumerate(self.lines) if not n.strip()],
            "functions": self.functions,
            "hash": h.hexdigest(),
            "number_lines": len(self.lines),
            "statements": statements,
            "definition_lines": sorted(self.definitions_lines),
            "import_lines": sorted(self.import_lines),
        }
