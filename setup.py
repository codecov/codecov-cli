from setuptools import Extension, find_packages, setup

setup(
    name="codecov-cli",
    version="0.1.0",
    packages=find_packages(exclude=["contrib", "docs", "tests*"]),
    description="Codecov Command Line Interface",
    long_description="",
    author="Codecov",
    author_email="support@codecov.io",
    install_requires=["click", "requests", "PyYAML"],
    entry_points={
        "console_scripts": [
            "codecovcli = codecov_cli.main:run",
        ],
    },
)
