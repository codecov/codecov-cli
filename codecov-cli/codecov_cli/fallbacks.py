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
    job_name = auto()


_FIELDS_WITH_VERSIONING_FALLBACK = frozenset(
    {
        FallbackFieldEnum.branch,
        FallbackFieldEnum.commit_sha,
        FallbackFieldEnum.slug,
        FallbackFieldEnum.git_service,
    }
)


class CodecovOption(click.Option):
    fallback_fields: typing.Optional[tuple[FallbackFieldEnum, ...]]

    def __init__(self, *args, **kwargs):
        fallback_fields = kwargs.pop("fallback_fields", None)
        fallback_field = kwargs.pop("fallback_field", None)
        if fallback_fields is not None:
            self.fallback_fields = tuple(fallback_fields)
        elif fallback_field is not None:
            self.fallback_fields = (fallback_field,)
        else:
            self.fallback_fields = None
        super().__init__(*args, **kwargs)

    def get_default(
        self, ctx: click.Context, call: bool = True
    ) -> typing.Optional[typing.Union[typing.Any, typing.Callable[[], typing.Any]]]:
        res = super().get_default(ctx, call=call)
        if res is not None:
            return res
        if self.fallback_fields is not None:
            for field in self.fallback_fields:
                if ctx.obj.get("ci_adapter") is not None:
                    res = ctx.obj.get("ci_adapter").get_fallback_value(field)
                    if res is not None:
                        return res
                if (
                    ctx.obj.get("versioning_system") is not None
                    and field in _FIELDS_WITH_VERSIONING_FALLBACK
                ):
                    res = ctx.obj.get("versioning_system").get_fallback_value(field)
                    if res is not None:
                        return res
        return None


class BrandedOption(click.Option):
    def resolve_envvar_value(self, ctx: click.Context) -> typing.Optional[str]:
        actual_var = self.envvar
        self.envvar = [
            f"{brand.value.upper()}_{actual_var}" for brand in ctx.obj["branding"]
        ]
        res = super().resolve_envvar_value(ctx)
        self.envvar = actual_var
        return res


class BrandedCodecovOption(CodecovOption, BrandedOption):
    pass
