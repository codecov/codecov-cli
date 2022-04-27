from more_itertools import side_effect
import pytest


from unittest.mock import Mock, MagicMock, PropertyMock
from glob import glob

from codecov_cli.plugins.pycoverage import Pycoverage


class TestPycoverage(object):
    def test_coverage_combine_called_if_coverage_data_exist(self, tmp_path, mocker):        
        def combine_subprocess_side_effect(*args, **kwargs):
            try:
                if args[0][1] != 'combine':
                    return MagicMock()
            except IndexError:
                return MagicMock()
            
            
            # path is the same as tmp_path 
            path = kwargs["cwd"]
            
            (path / ".coverage").touch()
            return MagicMock()
        
        
        subprocess_mock = mocker.patch("codecov_cli.plugins.pycoverage.subprocess.run",
                     side_effect=combine_subprocess_side_effect)
        
        
        # test coverage combine is not called if no coverage data exist
        Pycoverage()._generate_XML_report(tmp_path)

        with pytest.raises(AssertionError):
            subprocess_mock.assert_any_call(["coverage", "combine", "-a"], cwd=tmp_path)
            
            
        # test coverage combine is called if coverage data exist
        subprocess_mock.reset_mock()
        coverage_file_names = [".coverage.ac", ".coverage.a", ".coverage.b"]
        for name in coverage_file_names:
            p = tmp_path / name
            p.touch()
        
        
        Pycoverage()._generate_XML_report(tmp_path)
        
        subprocess_mock.assert_any_call(["coverage", "combine", "-a"], cwd=tmp_path)
        assert (tmp_path / ".coverage").exists()
        
            
        
    def test_xml_reports_generated_if_coverage_file_exists(self, tmp_path, mocker):
        def xml_subprocess_side_effect(*args, **kwargs):
            try:
                if args[0][1] != 'xml':
                    return MagicMock()
            except IndexError:
                return MagicMock()
            
            
            # path is the same as tmp_path 
            path = kwargs["cwd"]
            
            (path / "coverage.xml").touch()
            mock = MagicMock()
            mock.stdout = b"Wrote XML report to coverage.xml\n"
            
            return mock
        
        subprocess_mock = mocker.patch("codecov_cli.plugins.pycoverage.subprocess.run",
                     side_effect=xml_subprocess_side_effect)

        
        # test returns false if .coverage file doesn't exist
        assert not Pycoverage()._generate_XML_report(tmp_path)
        subprocess_mock.assert_not_called()
        
        
        # test returns true if .coverage file exist
        (tmp_path / ".coverage").touch()
        assert Pycoverage()._generate_XML_report(tmp_path)
        subprocess_mock.assert_called_with(["coverage", "xml", "-i"], cwd=tmp_path, capture_output=True)
        
        
        
        
        
        
        
        
        
        
        