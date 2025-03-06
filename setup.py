from platform import system

from setuptools import Extension, setup

setup(
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
