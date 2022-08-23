class NodeVisitor(object):
    def __init__(self, analyzer):
        self.analyzer = analyzer

    def start_visit(self, node):
        self.visit(node)

    def visit(self, node):
        self.do_visit(node)
        for c in node.children:
            self.visit(c)

    def do_visit(self, node):
        if node.is_named:
            current_line_number = node.start_point[0] + 1
            if node.type in (
                "expression_statement",
                "return_statement",
                "if_statement",
                "for_statement",
                "while_statement",
            ):
                if node.prev_named_sibling:
                    self.analyzer.line_surety_ancestorship[current_line_number] = (
                        node.prev_named_sibling.start_point[0] + 1
                    )
                self.analyzer.statements.append(
                    {
                        "current_line": current_line_number,
                        "start_column": node.start_point[1],
                        "line_hash": self.analyzer._get_code_hash(
                            node.start_byte, node.end_byte
                        ),
                        "len": node.end_point[0] + 1 - current_line_number,
                        "extra_connected_lines": tuple(),
                    }
                )
            if node.type in ("if_statement", "elif_clause"):
                first_if_statement = node.child_by_field_name("consequence")
                if first_if_statement.type == "block":
                    first_if_statement = first_if_statement.children[0]
                self.analyzer.line_surety_ancestorship[
                    first_if_statement.start_point[0] + 1
                ] = current_line_number
            if node.type in ("for_statement", "while_statement"):
                first_if_statement = node.child_by_field_name("body")
                if first_if_statement.type == "block":
                    first_if_statement = first_if_statement.children[0]
                self.analyzer.line_surety_ancestorship[
                    first_if_statement.start_point[0] + 1
                ] = current_line_number
                pass
