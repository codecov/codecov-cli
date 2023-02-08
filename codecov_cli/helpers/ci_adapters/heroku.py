import os

from codecov_cli.helpers.ci_adapters.base import CIAdapterBase


class HerokuCIAdapter(CIAdapterBase):
    # https://devcenter.heroku.com/articles/heroku-ci#immutable-environment-variables
    def detect(self) -> bool:
        return bool(os.getenv("CI")) and bool(os.getenv("HEROKU_TEST_RUN_BRANCH"))

    def _get_branch(self):
        return os.getenv("HEROKU_TEST_RUN_BRANCH")

    def _get_commit_sha(self):
        return os.getenv("HEROKU_TEST_RUN_COMMIT_VERSION")

    def _get_slug(self):
        return None

    def _get_service(self):
        return "heroku"

    def _get_build_url(self):
        return None

    def _get_build_code(self):
        return os.getenv("HEROKU_TEST_RUN_ID")

    def _get_job_code(self):
        return None

    def _get_pull_request_number(self):
        return None

    def get_service_name(self):
        return "Heroku"
