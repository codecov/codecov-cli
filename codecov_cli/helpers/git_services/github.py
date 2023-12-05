import json

import requests

from codecov_cli.helpers.git_services import PullDict


class Github:
    api_url = "https://api.github.com"
    api_version = "2022-11-28"

    def get_pull_request(self, slug, pr_number) -> PullDict:
        pull_url = f"/repos/{slug}/pulls/{pr_number}"
        url = self.api_url + pull_url
        headers = {"X-GitHub-Api-Version": self.api_version}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            res = json.loads(response.text)
            return {
                "url": res["url"],
                "head": {
                    "sha": res["head"]["sha"],
                    "label": res["head"]["label"],
                    "ref": res["head"]["ref"],
                    "slug": res["head"]["repo"]["full_name"],
                },
                "base": {
                    "sha": res["base"]["sha"],
                    "label": res["base"]["label"],
                    "ref": res["base"]["ref"],
                    "slug": res["base"]["repo"]["full_name"],
                },
            }
        return None
