def encode_slug(slug: str):
    if "/" not in slug:
        raise ValueError("The provided slug is invalid")
    owner, repo = slug.rsplit("/", 1)
    encoded_owner = ":::".join(owner.split("/"))
    encoded_slug = "::::".join([encoded_owner, repo])
    return encoded_slug
