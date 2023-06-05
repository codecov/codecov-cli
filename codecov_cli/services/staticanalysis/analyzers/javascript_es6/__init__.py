import hashlib

from tree_sitter import Language, Parser

import staticcodecov_languages
from codecov_cli.services.staticanalysis.analyzers.general import BaseAnalyzer

function_query_str = """
(function_declaration) @elemen
(generator_function_declaration) @elemen2
(function) @elemen3
(generator_function) @elemen4
(arrow_function) @elemen5
"""

method_query_str = """
(method_definition) @elemen
"""

imports_query_str = """
(import_statement) @elemen
(import) @elemen
"""


class ES6Analyzer(BaseAnalyzer):
    condition_statements = [
        "if_statement",
        "switch_statement",
        "for_statement",
        "for_in_statement",
        "while_statement",
        "do_statement",
    ]

    wrappers = [
        "class_declaration",
        "function_declaration",
        "generator_function_declaration",
        "function",
        "generator_function",
        "arrow_function",
    ]

    def __init__(self, path, actual_code, **options):
        self.actual_code = actual_code
        self.lines = self.actual_code.split(b"\n")
        self.executable_lines = set()
        self.functions = []
        self.path = path.result_filename
        self.JS_LANGUAGE = Language(staticcodecov_languages.__file__, "javascript")
        self.parser = Parser()
        self.parser.set_language(self.JS_LANGUAGE)
        self.import_lines = set()

    def get_code_hash(self, start_byte, end_byte):
        j = hashlib.md5()
        j.update(self.actual_code[start_byte:end_byte].strip())
        return j.hexdigest()

    def process(self):
        # TODO : A lot is obsolete and needs to be updated here
        tree = self.parser.parse(self.actual_code)
        root_node = tree.root_node
        function_query = self.JS_LANGUAGE.query(function_query_str)
        method_query = self.JS_LANGUAGE.query(method_query_str)
        imports_query = self.JS_LANGUAGE.query(imports_query_str)
        combined_results = function_query.captures(root_node) + method_query.captures(
            root_node
        )
        for func_node, _ in combined_results:
            body_node = func_node.child_by_field_name("body")
            self.functions.append(
                {
                    "identifier": self._get_name(func_node),
                    "start_line": func_node.start_point[0] + 1,
                    "end_line": func_node.end_point[0] + 1,
                    "code_hash": self.get_code_hash(
                        body_node.start_byte, body_node.end_byte
                    ),
                    "complexity_metrics": self._get_complexity_metrics(body_node),
                }
            )

        self.import_lines = self.get_import_lines(root_node, imports_query)

        h = hashlib.md5()
        h.update(self.actual_code)
        return {
            "empty_lines": [i + 1 for (i, n) in enumerate(self.lines) if not n.strip()],
            "executable_lines": sorted(self.executable_lines),
            "functions": self.functions,
            "number_lines": len(self.lines),
            "hash": h.hexdigest(),
            "filename": str(self.path),
            "language": "javascript",
            "import_lines": sorted(self.import_lines),
        }
