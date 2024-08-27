from __future__ import annotations

from dataclasses import dataclass
from typing_extensions import Self


@dataclass
class GithubLink:
    host: str
    owner: str
    repo: str

    @classmethod
    def parse(cls, link) -> Self:
        import re

        # gitlab supports names of the form my/repo/name
        supports_subgroups = re.search(r"^https?://gitlab\.", link) is not None
        subgroup_token = "/" if not supports_subgroups else ""
        rx = (
            r"^(?P<host>https?://[^/]+)/"
            r"(?P<owner>[^/]+)/"
            f"(?P<repo>[^#{subgroup_token}]+)/"
        )
        match = re.match(rx, re.sub(r"([^/])$", r"\1/", link))
        if match is None:
            raise ValueError(f"Unable to parse link: {link}")

        return GithubLink(**match.groupdict())


@dataclass
class RepoInfo:
    home: str
    source: str
    issue: str
    user: str

    @classmethod
    def from_link(cls, link: str | GithubLink, branch: "str | None" = None) -> Self:
        if isinstance(link, str):
            gh = GithubLink.parse(link)
        else:
            gh = link

        if branch is None:
            branch = cls.gha_current_branch()

        return cls(
            home=f"{gh.host}/{gh.owner}/{gh.repo}/",
            source=f"{gh.host}/{gh.owner}/{gh.repo}/blob/{branch}/",
            issue=f"{gh.host}/{gh.owner}/{gh.repo}/issues/",
            user=f"{gh.host}/{gh.owner}/",
        )

    def source_link(self, path) -> str:
        return f"{self.source}{path}"

    @classmethod
    def gha_current_branch(cls) -> str:
        import os

        ref = os.environ.get("GITHUB_HEAD_REF", os.environ.get("GITHUB_REF_NAME"))

        if ref is not None:
            return ref

        return "HEAD"
