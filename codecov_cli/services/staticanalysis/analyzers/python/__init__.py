import hashlib

from tree_sitter import Language, Parser

import staticcodecov_languages
from codecov_cli.services.staticanalysis.analyzers.python.node_wrappers import (
    NodeVisitor,
)

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


class PythonAnalyzer(object):

    condition_statements = [
        "if_statement",
        "while_statement",
        "for_statement",
        "conditional_expression",
    ]

    def __init__(self, path, actual_code, **options):
        self.actual_code = actual_code
        self.lines = self.actual_code.split(b"\n")
        self.statements = []
        self.import_lines = set()
        self.definitions_lines = set()
        self.functions = []
        self.path = path.result_filename
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
        for (a, _) in definitions_query.captures(root_node):
            self.definitions_lines.add(
                (a.start_point[0] + 1, a.end_point[0] - a.start_point[0])
            )
        for (a, _) in imports_query.captures(root_node):
            self.import_lines.add(
                (a.start_point[0] + 1, a.end_point[0] - a.start_point[0])
            )
        h = hashlib.md5()
        h.update(self.actual_code)
        statements = sorted(
            (
                (
                    x["current_line"],
                    {
                        "line_surety_ancestorship": self.line_surety_ancestorship.get(
                            x["current_line"], None
                        ),
                        **dict(
                            (k, v)
                            for (k, v) in x.items()
                            if k not in ["line_surety_ancestorship", "current_line"]
                        ),
                    },
                )
                for x in self.statements
            ),
            key=lambda x: (x[0], x[1]["start_column"]),
        )
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

    def _count_elements(self, node, types):
        count = 0
        for c in node.children:
            count += self._count_elements(c, types)
        if node.type in types:
            count += 1
        return count

    def _get_max_nested_conditional(self, node):
        return (1 if node.type in self.condition_statements else 0) + max(
            (self._get_max_nested_conditional(x) for x in node.children), default=0
        )

    def _get_complexity_metrics(self, body_node):
        number_conditions = self._count_elements(
            body_node,
            [
                "if_statement",
                "while_statement",
                "for_statement",
                "conditional_expression",
            ],
        )
        return {
            "conditions": number_conditions,
            "mccabe_cyclomatic_complexity": number_conditions + 1,
            "returns": self._count_elements(body_node, ["return_statement"]),
            "max_nested_conditional": self._get_max_nested_conditional(body_node),
        }

    def _get_code_hash(self, start_byte, end_byte):
        j = hashlib.md5()
        j.update(self.actual_code[start_byte:end_byte].strip())
        return j.hexdigest()

    def _get_parent_chain(self, node):
        cur = node.parent
        while cur:
            yield cur
            cur = cur.parent

    def _get_name(self, node):
        name_node = node.child_by_field_name("name")
        actual_name = self.actual_code[
            name_node.start_byte : name_node.end_byte
        ].decode()
        try:
            wrapping_class = next(
                x
                for x in self._get_parent_chain(node)
                if x.type in ("class_definition", "function_definition")
            )
        except StopIteration:
            wrapping_class = None
        if wrapping_class is not None:
            class_name_node = wrapping_class.child_by_field_name("name")
            class_name = self.actual_code[
                class_name_node.start_byte : class_name_node.end_byte
            ].decode()
            return f"{class_name}::{actual_name}"
        return actual_name
