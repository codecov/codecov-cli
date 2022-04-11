import typing
from enum import Enum, auto

from click import Context, Option, BadParameter


class CircleCIFallbacker(object):
    def get_value(self, fallback_field):
        return "banana"


def get_provider_specific_fallbacker(provider_name):
    if provider_name == "circleci":
        return CircleCIFallbacker()
    return None


class FallbackFieldEnum(Enum):
    commit_sha = auto()
    build_url = auto()
    build_code = auto()
    job_code = auto()
    pull_request_number = auto()


class CodecovOption(Option):
    def __init__(self, *args, **kwargs):
        self.fallback_field = kwargs.pop("fallback_field", None)
        super().__init__(*args, **kwargs)

    def get_default(
        self, ctx: Context, call: bool = True
    ) -> typing.Optional[typing.Union[typing.Any, typing.Callable[[], typing.Any]]]:
        res = super().get_default(ctx, call=call)
        if res is not None:
            return res
        if (
            self.fallback_field is not None
            and ctx.obj.get("fallbacker") is not None
        ):
            return ctx.obj.get("fallbacker").get_value(self.fallback_field)
        raise BadParameter(f"{self.fallback_field.name} needs to be set by either command line or envvars or CI")
