from setuptools import setup

setup(
    name="cz_conventional_commmits_jira_optional",
    version="1.0.0",
    py_modules=["cz_conventional_commmits_jira_optional"],
    license="MIT",
    long_description="Commitizen configuration to create conventional commits with optional Jira support.",
    install_requires=["commitizen"],
    entry_points={
        "commitizen.plugin": [
            "cz_conventional_commmits_jira_optional = cz_conventional_commmits_jira_optional:ConventionalCommitsJiraOptionalCz"
        ]
    },
)
