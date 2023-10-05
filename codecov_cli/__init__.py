from os import path

here = path.abspath(path.dirname(__file__))


with open(path.join(here, "..", "VERSION"), encoding="utf-8") as f:
    version_number = f.readline().strip()

__version__ = version_number
