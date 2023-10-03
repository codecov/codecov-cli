with open("VERSION", encoding="utf-8") as f:
    version_number = f.readline().strip()

__version__ = version_number
