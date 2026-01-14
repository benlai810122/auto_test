import subprocess

BASE_VERSION = "1.0.0"

def get_git_sha():
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).decode().strip()
    except Exception:
        return None

def get_version():
    sha = get_git_sha()
    return f"{BASE_VERSION} & {sha}" if sha else BASE_VERSION

if __name__ == '__main__':
    print(get_version())