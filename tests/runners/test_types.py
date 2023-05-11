from codecov_cli.runners.types import LabelAnalysisRequestResult


class TestLabelAnalysisRequestResult(object):
    def test_creation(self):
        result = LabelAnalysisRequestResult(
            {
                "present_report_labels": ["test_present"],
                "absent_labels": ["test_absent"],
                "present_diff_labels": ["test_diff"],
                "global_level_labels": ["test_global"],
            }
        )
        assert result.present_report_labels == ["test_present"]
        assert result.absent_labels == ["test_absent"]
        assert result.present_diff_labels == ["test_diff"]
        assert result.global_level_labels == ["test_global"]
        assert result["present_report_labels"] == ["test_present"]
