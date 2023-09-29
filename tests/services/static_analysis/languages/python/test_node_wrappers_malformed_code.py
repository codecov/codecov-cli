import pathlib

import pytest
from tree_sitter import Node

from codecov_cli.services.staticanalysis.analyzers.python import PythonAnalyzer
from codecov_cli.services.staticanalysis.analyzers.python.node_wrappers import (
    NodeVisitor,
)
from codecov_cli.services.staticanalysis.exceptions import AnalysisError
from codecov_cli.services.staticanalysis.types import FileAnalysisRequest


class TestMalformedIfStatements(object):
    def test_if_empty_block_raises_analysis_error(self):
        analysis_request = FileAnalysisRequest(
            actual_filepath=pathlib.Path("test_file"), result_filename="test_file"
        )
        # Code for an empty IF. NOT valid python code
        actual_code = b'x = 10\nif x == "batata":\n\n'
        python_analyser = PythonAnalyzer(analysis_request, actual_code=actual_code)
        # Parse the code snippet and get the if_statement node
        tree = python_analyser.parser.parse(actual_code)
        root = tree.root_node
        assert root.type == "module"
        assert root.child_count == 2
        if_statement_node = root.children[1]
        assert if_statement_node.type == "if_statement"
        # Make sure it is indeed an empty if_statement
        if_body = if_statement_node.child_by_field_name("consequence")
        assert if_body.type == "block"
        assert if_body.child_count == 0
        visitor = NodeVisitor(python_analyser)
        with pytest.raises(AnalysisError) as exp:
            visitor.do_visit(if_statement_node)
        assert (
            str(exp.value)
            == "if_statement consequence is empty block @ test_file:2, column 17"
        )

    def test_for_empty_block_raises_analysis_error(self):
        analysis_request = FileAnalysisRequest(
            actual_filepath=pathlib.Path("test_file"), result_filename="test_file"
        )
        # Code for an empty IF. NOT valid python code
        actual_code = b"for x in range(10):\n\n"
        python_analyser = PythonAnalyzer(analysis_request, actual_code=actual_code)
        # Parse the code snippet and get the if_statement node
        tree = python_analyser.parser.parse(actual_code)
        root = tree.root_node
        assert root.type == "module"
        assert root.child_count == 1
        for_statement_node = root.children[0]
        assert for_statement_node.type == "for_statement"
        # Make sure it is indeed an empty if_statement
        if_body = for_statement_node.child_by_field_name("body")
        assert if_body.type == "block"
        assert if_body.child_count == 0
        visitor = NodeVisitor(python_analyser)
        with pytest.raises(AnalysisError) as exp:
            visitor.do_visit(for_statement_node)
        assert (
            str(exp.value)
            == "loop_statement body is empty block @ test_file:1, column 19"
        )
