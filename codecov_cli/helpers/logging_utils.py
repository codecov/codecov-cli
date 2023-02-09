import json
import logging

import click

# Heavily inspired on https://github.com/click-contrib/click-log/blob/master/click_log/core.py


class JsonEncoder(json.JSONEncoder):
    """
    A custom encoder extending the default JSONEncoder
    """

    def default(self, obj):
        try:
            return super(JsonEncoder, self).default(obj)
        except TypeError:
            try:
                return str(obj)
            except Exception:
                return None


class ColorFormatter(logging.Formatter):
    colors = {
        "error": dict(fg="red"),
        "exception": dict(fg="red"),
        "critical": dict(fg="red"),
        "debug": dict(fg="blue"),
        "warning": dict(fg="yellow"),
        "info": dict(fg="blue"),
    }

    def format(self, record):
        if not record.exc_info:
            level = record.levelname.lower()
            asctime = self.formatTime(record, self.datefmt)
            msg = record.getMessage()
            if level in self.colors:
                prefix = click.style("{}".format(level), **self.colors[level])
                msg = "\n".join(
                    f"{prefix} - {asctime} -- {x}" for x in msg.splitlines()
                )
            if hasattr(record, "extra_log_attributes"):
                msg += " --- " + json.dumps(
                    record.extra_log_attributes, cls=JsonEncoder
                )
            return msg
        return super().format(record)


class ClickHandler(logging.Handler):
    _use_stderr = True
    formatter = ColorFormatter()

    def emit(self, record):
        try:
            msg = self.format(record)
            click.echo(msg, err=self._use_stderr)
        except Exception:
            self.handleError(record)


def configure_logger(logger: logging.Logger, log_level=logging.INFO):
    # This if exists to avoid an issue where extra handlers would be added by tests that use runner.invoke()
    # Which would cause subsequent tests to failed due to repeated log lines
    if not logger.hasHandlers():
        ch = ClickHandler()
        ch.setFormatter(ColorFormatter())
        logger.addHandler(ch)
    logger.propagate = False
    logger.setLevel(log_level)
