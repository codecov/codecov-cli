import hashlib
from collections import deque


class BaseAnalyzer(object):
    def __init__(self, filename, actual_code):
        pass

    def process(self):
        return {}

    def _count_elements(self, node, types):
        count = 0
        for c in node.children:
            count += self._count_elements(c, types)
        if node.type in types:
            count += 1
        return count

    def _get_max_nested_conditional(self, head):
        """Iterates over all nodes in a function body and returns the max nested conditional depth.
        Uses BFS to avoid recursion calls (so we don't throw RecursionError)
        """
        nodes_to_visit = deque()
        nodes_to_visit.append([head, int(head.type in self.condition_statements)])
        max_nested_depth = 0

        while nodes_to_visit:
            curr_node, curr_depth = nodes_to_visit.popleft()
            max_nested_depth = max(max_nested_depth, curr_depth)
            # Here is where the depth might change
            # If the current node is a conditional
            is_curr_conditional = curr_node.type in self.condition_statements

            # Enqueue all child nodes of the curr_node
            for child in curr_node.children:
                nodes_to_visit.append([child, curr_depth + is_curr_conditional])

        return max_nested_depth

    def _get_complexity_metrics(self, body_node):
        number_conditions = self._count_elements(
            body_node,
            self.condition_statements,
        )
        return {
            "conditions": number_conditions,
            "mccabe_cyclomatic_complexity": number_conditions + 1,
            "returns": self._count_elements(body_node, ["return_statement"]),
            "max_nested_conditional": self._get_max_nested_conditional(body_node),
        }

    def _get_name(self, node):
        name_node = node.child_by_field_name("name")
        body_node = node.child_by_field_name("body")
        actual_name = (
            self.actual_code[name_node.start_byte : name_node.end_byte].decode()
            if name_node
            else f"Anonymous_{body_node.start_point[0] + 1}_{body_node.end_point[0] - body_node.start_point[0]}"
        )
        wrapping_classes = [
            x for x in self._get_parent_chain(node) if x.type in self.wrappers
        ]
        wrapping_classes.reverse()
        if wrapping_classes:
            parents_actual_names = ""

            for x in wrapping_classes:
                name = x.child_by_field_name("name")
                body = x.child_by_field_name("body")
                class_name = (
                    self.actual_code[name.start_byte : name.end_byte].decode()
                    if name
                    else f"Anonymous_{body.start_point[0] + 1}_{body.end_point[0] - body.start_point[0]}"
                )
                parents_actual_names = parents_actual_names + class_name + "::"
            return f"{parents_actual_names}{actual_name}"
        return actual_name

    def _get_parent_chain(self, node):
        cur = node.parent
        while cur:
            yield cur
            cur = cur.parent

    def get_import_lines(self, root_node, imports_query):
        import_lines = set()
        for a, _ in imports_query.captures(root_node):
            import_lines.add((a.start_point[0] + 1, a.end_point[0] - a.start_point[0]))
        return import_lines

    def get_definition_lines(self, root_node, definitions_query):
        definition_lines = set()
        for a, _ in definitions_query.captures(root_node):
            definition_lines.add(
                (a.start_point[0] + 1, a.end_point[0] - a.start_point[0])
            )
        return definition_lines

    def _get_code_hash(self, start_byte, end_byte):
        j = hashlib.md5()
        j.update(self.actual_code[start_byte:end_byte].strip())
        return j.hexdigest()

    def get_statements(self):
        return sorted(
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
