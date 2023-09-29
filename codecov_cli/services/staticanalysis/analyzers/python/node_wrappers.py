from tree_sitter import Node

from codecov_cli.services.staticanalysis.exceptions import AnalysisError


class NodeVisitor(object):
    def __init__(self, analyzer):
        self.analyzer = analyzer

    def start_visit(self, node):
        self.visit(node)

    def visit(self, node: Node):
        self.do_visit(node)
        for c in node.children:
            self.visit(c)

    def _is_function_docstring(self, node: Node):
        """Skips docstrings for funtions, such as this one.
        Pytest doesn't include them in the report, so I don't think we should either,
        at least for now.
        """
        # Docstrings have type 'expression_statement
        if node.type != "expression_statement":
            return False
        # Docstrings for a module are OK - they show up in pytest result
        # Docstrings for a class are OK - they show up in pytest result
        # Docstrings for functions are NOT OK - they DONT show up in pytest result
        # Check if it's docstring
        has_single_child = len(node.children) == 1
        only_child_is_string = node.children[0].type == "string"
        # Check if is the first line of a function
        parent_is_block = node.parent.type == "block"
        first_exp_in_block = node.prev_named_sibling is None
        is_in_function_context = (
            parent_is_block and node.parent.parent.type == "function_definition"
        )

        return (
            has_single_child
            and only_child_is_string
            and parent_is_block
            and first_exp_in_block
            and is_in_function_context
        )

    def _get_previous_sibling_that_is_not_comment_not_func_docstring(self, node: Node):
        curr = node.prev_named_sibling
        while curr is not None and (
            curr.type == "comment" or self._is_function_docstring(curr)
        ):
            curr = curr.prev_named_sibling
        return curr

    def do_visit(self, node: Node):
        if node.is_named:
            current_line_number = node.start_point[0] + 1
            if node.type in (
                "expression_statement",
                "return_statement",
                "if_statement",
                "for_statement",
                "while_statement",
            ):
                if self._is_function_docstring(node):
                    # We ignore these
                    return
                closest_named_sibling_not_comment_that_is_in_statements = (
                    self._get_previous_sibling_that_is_not_comment_not_func_docstring(
                        node
                    )
                )
                if closest_named_sibling_not_comment_that_is_in_statements:
                    self.analyzer.line_surety_ancestorship[current_line_number] = (
                        closest_named_sibling_not_comment_that_is_in_statements.start_point[
                            0
                        ]
                        + 1
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
                # Some of the children of a node have a field_name associated to them
                # In the case of an if and elif, "consequence" is the code that is executed in that branch of code
                first_if_statement = node.child_by_field_name("consequence")
                try:
                    if first_if_statement.type == "block":
                        first_if_statement = first_if_statement.children[0]  # BUG
                except IndexError:
                    raise AnalysisError(
                        f"if_statement consequence is empty block @ {self.analyzer.path}:{first_if_statement.start_point[0] + 1}, column {first_if_statement.start_point[1]}"
                    )
                self.analyzer.line_surety_ancestorship[
                    first_if_statement.start_point[0] + 1
                ] = current_line_number
            if node.type in ("for_statement", "while_statement"):
                first_loop_statement = node.child_by_field_name("body")
                try:
                    if first_loop_statement.type == "block":
                        first_loop_statement = first_loop_statement.children[0]
                except IndexError:
                    raise AnalysisError(
                        f"loop_statement body is empty block @ {self.analyzer.path}:{first_loop_statement.start_point[0] + 1}, column {first_loop_statement.start_point[1]}"
                    )
                self.analyzer.line_surety_ancestorship[
                    first_loop_statement.start_point[0] + 1
                ] = current_line_number
                pass
