import os

from codecov_cli.helpers.ci_adapters.base import CIAdapterBase


class BuildkiteAdapter(CIAdapterBase):
    # https://buildkite.com/docs/pipelines/environment-variables

    def detect(self) -> bool:
        return bool(os.getenv("BUILDKITE"))

    def _get_branch(self):
        return os.getenv("BUILDKITE_BRANCH")

    def _get_build_code(self):
        return os.getenv("BUILDKITE_BUILD_NUMBER")

    def _get_build_url(self):
        return os.getenv("BUILDKITE_BUILD_URL")

    def _get_commit_sha(self):
        return os.getenv("BUILDKITE_COMMIT")

    def _get_slug(self):
        # https://buildkite.com/docs/pipelines/configure/environment-variables#BUILDKITE_REPO
        repo_url = os.getenv("BUILDKITE_REPO")
        if repo_url:
            slug = self._parse_slug_from_repo(repo_url)
            if slug:
                return slug

        # Fallback to organization and pipeline slugs
        org = os.getenv("BUILDKITE_ORGANIZATION_SLUG")
        repo = os.getenv("BUILDKITE_PIPELINE_SLUG")
        if org and repo:
            return f"{org}/{repo}"
        return None

    def _parse_slug_from_repo(self, repo_url: str):
        """
        TODO: this is relevant: https://stackoverflow.com/questions/31801271/what-are-the-supported-git-url-formats
        supports:
            (protocol://)host.xz/path/to/repo(.git/)
            (protocol://)host.xz:path/to/repo(.git/)
            (protocol://)user@host.xz:path/to/repo(.git/)
            (protocol://)user@host.xz/path/to/repo(.git/)
        """
        if not repo_url:
            return None

        value = repo_url.strip()
        value = value.removesuffix("/")
        value = value.removesuffix(".git")

        value = value.replace(":", "/")
        parts = [p for p in value.split("/") if p]
        if len(parts) >= 2:
            return "/".join(parts[-2:])
        return None

    def _get_service(self):
        return "buildkite"

    def _get_pull_request_number(self):
        pr_number = os.getenv("BUILDKITE_PULL_REQUEST")
        # The number of the pull request, if this branch is a pull request.
        if pr_number != "false":
            return pr_number
        return None

    def _get_job_code(self):
        return os.getenv("BUILDKITE_JOB_ID")

    def get_service_name(self):
        return "BuildKite"
