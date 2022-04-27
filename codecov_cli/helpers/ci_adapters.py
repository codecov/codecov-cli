from codecov_cli.fallbacks import FallbackFieldEnum


class CircleCIFallbacker(object):
    def get_fallback_value(self, fallback_field: FallbackFieldEnum):
        return "banana"


def get_ci_adapter(provider_name):
    if provider_name == "circleci":
        return CircleCIFallbacker()
    return None
