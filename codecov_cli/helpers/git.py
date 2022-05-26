def parse_slug(address: str):
    """Extracts a slug from git based urls"""

    """
    URL examples:
        origin    https://github.com/codecov/codecov-cli.git (fetch)
        https://github.com/codecov/codecov-cli.git
        origin  git@github.com:codecov/codecov-cli.git (fetch)
        git@github.com:codecov/codecov-cli.git
    """
    if "http" in address:
        try:
            return address.split("//")[1].split("/", 1)[1].split(".git")[0]
        except IndexError:
            raise ValueError("Argument address is not a valid address")

    if "@" in address:
        try:
            return address.split(":")[1].split(".git")[0]
        except IndexError:
            raise ValueError("Argument address is not a valid address")

    raise ValueError("Argument address is not a valid address")
