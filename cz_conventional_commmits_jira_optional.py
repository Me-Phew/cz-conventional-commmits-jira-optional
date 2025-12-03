import os
import re
from typing import TypedDict

from commitizen import defaults
from commitizen.cz import exceptions
from commitizen.cz.base import BaseCommitizen
from commitizen.cz.utils import multiple_line_breaker, required_validator
from commitizen.question import CzQuestion

__all__ = ["ConventionalCommitsJiraOptionalCz"]


def _parse_scope(text: str) -> str:
    return "-".join(text.strip().split())


def _parse_subject(text: str) -> str:
    return required_validator(text.strip(".").strip(), msg="Subject is required.")


def _parse_jira_issues(text: str) -> str:
    issues = " ".join(text.strip().split())

    if not all(re.match(r"^[A-Z]{2,}-\d+$", issue) for issue in issues.split()):
        raise exceptions.AnswerRequiredError("Enter valid Jira issue keys (e.g., JRA-123).")

    return issues


class ConventionalCommitsAnswers(TypedDict):
    jira_issues: str
    jira_workflow: str
    jira_time: str
    jira_comment: str
    prefix: str
    scope: str
    subject: str
    body: str
    footer: str
    is_breaking_change: bool


class ConventionalCommitsJiraOptionalCz(BaseCommitizen):
    bump_pattern = defaults.BUMP_PATTERN
    bump_map = defaults.BUMP_MAP  # type: ignore
    bump_map_major_version_zero = defaults.BUMP_MAP_MAJOR_VERSION_ZERO  # type: ignore
    commit_parser = r"^((?P<change_type>feat|fix|refactor|perf|BREAKING CHANGE)(?:\((?P<scope>[^()\r\n]*)\)|\()?(?P<breaking>!)?|\w+!):\s(?P<message>.*)?"
    change_type_map = {
        "feat": "Feat",
        "fix": "Fix",
        "refactor": "Refactor",
        "perf": "Perf",
    }
    changelog_pattern = defaults.BUMP_PATTERN

    def questions(self) -> list[CzQuestion]:
        return [
            {
                "type": "input",
                "name": "jira_issues",
                "message": "Jira Issue ID(s) separated by spaces (optional):\n",
                "filter": _parse_jira_issues,
            },
            {
                "type": "input",
                "name": "jira_workflow",
                "message": "Workflow command (testing, closed, etc.) (optional):\n",
                "filter": lambda x: "#" + x.strip().replace(" ", "-") if x else "",
            },
            {
                "type": "input",
                "name": "jira_time",
                "message": "Time spent (i.e. 3h 15m) (optional):\n",
                "filter": lambda x: "#time " + x if x else "",
            },
            {
                "type": "input",
                "name": "jira_comment",
                "message": "Jira comment (optional):\n",
                "filter": lambda x: "#comment " + x if x else "",
            },
            {
                "type": "list",
                "name": "prefix",
                "message": "Select the type of change you are committing",
                "choices": [
                    {
                        "value": "fix",
                        "name": "fix: A bug fix. Correlates with PATCH in SemVer",
                        "key": "x",
                    },
                    {
                        "value": "feat",
                        "name": "feat: A new feature. Correlates with MINOR in SemVer",
                        "key": "f",
                    },
                    {
                        "value": "docs",
                        "name": "docs: Documentation only changes",
                        "key": "d",
                    },
                    {
                        "value": "style",
                        "name": (
                            "style: Changes that do not affect the "
                            "meaning of the code (white-space, formatting,"
                            " missing semi-colons, etc)"
                        ),
                        "key": "s",
                    },
                    {
                        "value": "refactor",
                        "name": ("refactor: A code change that neither fixes " "a bug nor adds a feature"),
                        "key": "r",
                    },
                    {
                        "value": "perf",
                        "name": "perf: A code change that improves performance",
                        "key": "p",
                    },
                    {
                        "value": "test",
                        "name": ("test: Adding missing or correcting existing tests"),
                        "key": "t",
                    },
                    {
                        "value": "build",
                        "name": (
                            "build: Changes that affect the build system or "
                            "external dependencies (example scopes: pip, docker, npm)"
                        ),
                        "key": "b",
                    },
                    {
                        "value": "chore",
                        "name": ("chore: Other changes that don't modify src or test " "files"),
                        "key": "c",
                    },
                    {
                        "value": "ci",
                        "name": ("ci: Changes to CI configuration files and " "scripts (example scopes: GitLabCI)"),
                        "key": "i",
                    },
                ],
            },
            {
                "type": "input",
                "name": "scope",
                "message": ("What is the scope of this change? (class or file name): (press [enter] to skip)\n"),
                "filter": _parse_scope,
            },
            {
                "type": "input",
                "name": "subject",
                "filter": _parse_subject,
                "message": ("Write a short and imperative summary of the code changes: (lower case and no period)\n"),
            },
            {
                "type": "input",
                "name": "body",
                "message": (
                    "Provide additional contextual information about the code changes: (press [enter] to skip)\n"
                ),
                "filter": multiple_line_breaker,
            },
            {
                "type": "confirm",
                "name": "is_breaking_change",
                "message": "Is this a BREAKING CHANGE? Correlates with MAJOR in SemVer",
                "default": False,
            },
            {
                "type": "input",
                "name": "footer",
                "message": (
                    "Footer. Information about Breaking Changes and "
                    "reference issues that this commit closes: (press [enter] to skip)\n"
                ),
            },
        ]

    def message(self, answers: ConventionalCommitsAnswers) -> str:  # type: ignore[override]
        jira_issues = answers["jira_issues"]
        jira_workflow = answers["jira_workflow"]
        jira_time = answers["jira_time"]
        jira_comment = answers["jira_comment"]

        prefix = answers["prefix"]
        scope = answers["scope"]
        subject = answers["subject"]
        body = answers["body"]
        footer = answers["footer"]
        is_breaking_change = answers["is_breaking_change"]

        formatted_scope = f"({scope})" if scope else ""
        title = f"{prefix}{formatted_scope}"

        if is_breaking_change and self.config.settings.get("breaking_change_exclamation_in_title", False):
            title = f"{title}!"

        if jira_issues:
            title = f"{title}: {jira_issues} {subject}"
        else:
            title = f"{title}: {subject}"

        formatted_body = f"\n\n{body}" if body else ""

        jira_parts = [x for x in [jira_workflow, jira_time, jira_comment] if x]
        formatted_jira = f"\n\n{' '.join(jira_parts)}" if jira_parts else ""

        if is_breaking_change:
            footer = f"BREAKING CHANGE: {footer}"

        formatted_footer = f"\n\n{footer}" if footer else ""

        return f"{title}{formatted_body}{formatted_jira}{formatted_footer}"

    def example(self) -> str:
        return (
            "fix: correct minor typos in code\n"
            "\n"
            "see the issue for details on the typos fixed\n"
            "\n"
            "closes issue #12"
        )

    def schema(self) -> str:
        return (
            "<type>(<scope>): <jira_issues> <subject>\n"
            "<BLANK LINE>\n"
            "<body>\n"
            "<BLANK LINE>\n"
            "<jira_workflow> <jira_time> <jira_comment>\n"
            "(BREAKING CHANGE: )<footer>"
        )

    def schema_pattern(self) -> str:
        change_types = (
            "build",
            "bump",
            "chore",
            "ci",
            "docs",
            "feat",
            "fix",
            "perf",
            "refactor",
            "revert",
            "style",
            "test",
        )

        jira_issues_pattern = r"([A-Z]{2,}-\d+( [A-Z]{2,}-\d+)*)?"
        jira_metadata_pattern = r"(?:\s#\w+(?: [^\s#]+)?)?"

        return (
            r"(?s)"  # Explicitly make . match new line
            r"(" + "|".join(change_types) + r")"  # type
            r"(\(\S+\))?"  # Optional scope
            r"!?"
            r": "
            + jira_issues_pattern  # Jira issues
            + r"\s*([^\n\r]+)?"  # Subject
            + r"(\n\n.*)?"  # Optional body
            + r"("
            + jira_metadata_pattern
            + r")*"  # Optional Jira metadata repeated
            + r"$"
        )

    def info(self) -> str:
        dir_path = os.path.dirname(os.path.realpath(__file__))
        filepath = os.path.join(dir_path, "cz_conventional_commmits_jira_optional_info.txt")
        with open(filepath, encoding=self.config.settings["encoding"]) as f:  # type: ignore
            return f.read()
