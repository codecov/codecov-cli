#!/usr/bin/env python3
import subprocess


def command_dump(commands):
    print(f"Dumping {' '.join(commands)}")
    command_docs = subprocess.run(
        [*commands, "--help"], capture_output=True
    ).stdout.decode("utf-8")

    split_docs = command_docs.split("\n")

    try:
        index_of = split_docs.index("Commands:")
    except ValueError:
        return command_docs

    if "Commands:" in split_docs:
        sub_commands = [
            sub_command.strip()
            for sub_command in split_docs[index_of + 1 :]
            if sub_command.strip()
        ]
        for sub_command in sub_commands:
            command_docs = "\n".join(
                [command_docs, command_dump([*commands, sub_command])]
            )

    with open("codecovcli_commands", "w") as f:
        f.write(command_docs)


if __name__ == "__main__":
    command_dump(["codecovcli"])
