import pathlib
import subprocess


class GitFileFinder(object):
    def __init__(self, folder_name: pathlib.Path):
        self.folder_name = folder_name

    def find_files(self):
        res = subprocess.run(
            ["git", "-C", str(self.folder_name), "ls-files"], capture_output=True
        )
        return res.stdout.decode().split()
