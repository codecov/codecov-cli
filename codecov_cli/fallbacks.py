import typing
from enum import Enum, auto

import click


class FallbackFieldEnum(Enum):
    branch = auto()
    build_code = auto()
    build_url = auto()
    commit_sha = auto()
    git_service = auto()
    job_code = auto()
    pull_request_number = auto()
    service = auto()
    slug = auto()


class CodecovOption(click.Option):
    def __init__(self, *args, **kwargs):
        self.fallback_field = kwargs.pop("fallback_field", None)
        super().__init__(*args, **kwargs)

    def get_default(
        self, ctx: click.Context, call: bool = True
    ) -> typing.Optional[typing.Union[typing.Any, typing.Callable[[], typing.Any]]]:
        res = super().get_default(ctx, call=call)
        if res is not None:
            return res
        if self.fallback_field is not None:
            if ctx.obj.get("ci_adapter") is not None:
                res = ctx.obj.get("ci_adapter").get_fallback_value(self.fallback_field)
                if res is not None:
                    return res
            if ctx.obj.get("versioning_system") is not None:
                res = ctx.obj.get("versioning_system").get_fallback_value(
                    self.fallback_field
                )
                if res is not None:
                    return res
        return None
