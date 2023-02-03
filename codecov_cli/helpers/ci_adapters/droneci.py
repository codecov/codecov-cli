import os

from codecov_cli.helpers.ci_adapters.base import CIAdapterBase


class DroneCIAdapter(CIAdapterBase):
    # https://docs.drone.io/pipeline/environment/reference/
    def detect(self) -> bool:
        return bool(os.getenv("DRONE"))

    def _get_branch(self):
        return os.getenv("DRONE_BRANCH")

    def _get_build_code(self):
        return os.getenv("DRONE_BUILD_NUMBER")

    def _get_build_url(self):
        return os.getenv("DRONE_BUILD_LINK")

    def _get_commit_sha(self):
        return os.getenv("DRONE_COMMIT_SHA")

    def _get_slug(self):
        return os.getenv("DRONE_REPO")

    def _get_service(self):
        return "droneci"

    def _get_pull_request_number(self):
        return os.getenv("DRONE_PULL_REQUEST")

    def _get_job_code(self):
        return None

    def get_service_name(self):
        return "DroneCI"
