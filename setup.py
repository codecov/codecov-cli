from platform import system
from os import path

from setuptools import Extension, find_packages, setup

here = path.abspath(path.dirname(__file__))

with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="codecov-cli",
    version="0.1.7",
    packages=find_packages(exclude=["contrib", "docs", "tests*"]),
    description="Codecov Command Line Interface",
    long_description=long_description,
    long_description_content_type='text/markdown',
    author="Codecov",
    author_email="support@codecov.io",
    install_requires=["click", "requests", "PyYAML", "tree_sitter", "httpx"],
    entry_points={
        "console_scripts": [
            "codecovcli = codecov_cli.main:run",
        ],
    },
    ext_modules=[
        Extension(
            "staticcodecov_languages",
            [
                "languages/languages.c",
                "languages/treesitterpython/src/parser.c",
                "languages/treesitterjavascript/src/parser.c",
                "languages/treesitterpython/src/scanner.cc",
                "languages/treesitterjavascript/src/scanner.c",
            ],
            include_dirs=[
                "languages/treesitterpython/src",
                "languages/treesitterjavascript/src",
                "languages/treesitterjavascript/src/tree_sitter",
                "languages/treesitterpython/src/tree_sitter",
            ],
            extra_compile_args=(
                ["-Wno-unused-variable"] if system() != "Windows" else None
            ),
        )
    ],
)
