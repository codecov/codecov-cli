def parse_slug(address: str):
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
