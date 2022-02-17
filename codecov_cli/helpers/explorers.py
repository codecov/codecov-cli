import subprocess
from pathlib import Path


def get_file_explorer():
    return GitExplorer()


class GitExplorer(object):
    def get_network_root(self):
        p = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True)
        if p.stdout:
            return Path(p.stdout.decode().rstrip())
        return None


class MercurialExplorer(object):
    def get_network_root(self):
        p = subprocess.run(["hg", "root"], capture_output=True)
        if p.stdout:
            return Path(p.stdout.decode().rstrip())
        return None


class DefaultExplorer(object):
    def get_network_root(self):
        return Path.cwd()
