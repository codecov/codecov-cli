import hashlib

from tree_sitter import Language, Parser

import staticcodecov_languages

function_query_str = """
(function_declaration) @elemen
"""


class ES6Analyzer(object):
    def __init__(self, path, actual_code, **options):
        self.actual_code = actual_code
        self.lines = self.actual_code.split(b"\n")
        self.executable_lines = set()
        self.functions = []
        self.path = path.result_filename
        self.JS_LANGUAGE = Language(staticcodecov_languages.__file__, "javascript")
        self.parser = Parser()
        self.parser.set_language(self.JS_LANGUAGE)

    def get_code_hash(self, start_byte, end_byte):
        j = hashlib.md5()
        j.update(self.actual_code[start_byte:end_byte].strip())
        return j.hexdigest()

    def process(self):
        # TODO : A lot is obsolete and needs to be updated here
        tree = self.parser.parse(self.actual_code)
        root_node = tree.root_node
        function_query = self.JS_LANGUAGE.query(function_query_str)
        for func_node, _ in function_query.captures(root_node):
            name_node = func_node.child_by_field_name("name")
            actual_name = self.actual_code[
                name_node.start_byte : name_node.end_byte
            ].decode()
            body_node = func_node.child_by_field_name("body")
            self.functions.append(
                {
                    "identifier": actual_name,
                    "start_line": func_node.start_point[0] + 1,
                    "end_line": func_node.end_point[0] + 1,
                    "code_hash": self.get_code_hash(
                        body_node.start_byte, body_node.end_byte
                    ),
                    "complexity_metrics": {},
                }
            )
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
        }
