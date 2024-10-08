import pytest

from quartodoc.repo_info import GithubLink, RepoInfo


@pytest.mark.parametrize(
    "src, host, owner, repo",
    [
        (
            "https://github.com/machow/quartodoc",
            "https://github.com",
            "machow",
            "quartodoc",
        ),
        (
            "https://gitlab.com/machow/quartodoc",
            "https://gitlab.com",
            "machow",
            "quartodoc",
        ),
        (
            "https://gitlab.com/machow/some/pkgs/etc",
            "https://gitlab.com",
            "machow",
            "some/pkgs/etc",
        ),
    ],
)
def test_github_link_parse(src, host, owner, repo):
    gh = GithubLink.parse(src)
    assert gh.host == host
    assert gh.owner == owner
    assert gh.repo == repo


def test_repo_info_from_link():
    repo = RepoInfo.from_link(GithubLink("abc", "def", "xyz"), "a_branch")
    base = "abc/def/xyz"

    assert repo.home == f"{base}/"
    assert repo.source == f"{base}/blob/a_branch/"
    assert repo.issue == f"{base}/issues/"
    assert repo.user == "abc/def/"
