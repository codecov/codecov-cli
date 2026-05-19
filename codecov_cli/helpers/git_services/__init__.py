from typing import TypedDict


class CommitInfo(TypedDict):
    sha: str
    label: str
    ref: str
    slug: str


class PullDict(TypedDict):
    url: str
    head: CommitInfo
    base: CommitInfo
