def parse_slug(address: str):
    if 'http' in address:
        return address.split("//")[1].split("/", 1)[1].split(".git")[0]
    
    if '@' in address:
        return address.split(":")[1].split(".git")[0]
    
    raise ValueError("Argument address is not a valid address.")