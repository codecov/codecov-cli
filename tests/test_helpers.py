def parse_outstreams_into_log_lines(this_data):
    return list(do_parse_outstreams_into_log_lines(this_data))


def do_parse_outstreams_into_log_lines(this_data):
    if isinstance(this_data, bytes):
        this_data = this_data.decode()
    for x in this_data.splitlines():
        prefix_and_asctime, content = x.split(" -- ", 1)
        prefix, asctime = prefix_and_asctime.split(" - ")
        yield (prefix, content)
