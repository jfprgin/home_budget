import subprocess


def get_git_version():
    process = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], stdout=subprocess.PIPE)
    git_version = process.stdout.strip().decode('ascii')
    return git_version
