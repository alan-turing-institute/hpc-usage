import subprocess
import hashlib
import re
import os
from datetime import datetime
import time

# constants
header = "PID, USER, PACKAGE, RUNTIME"
sha256_hash = hashlib.sha256()
outfile = "package-report.txt"
lsof_command = 'lsof | grep "site-packages"'


def user_optout(pid):
    """Check if user set an environment variable to opt out of recording."""
    environ_file = f"/proc/{pid}/environ"
    try:
        with open(environ_file, "rb") as f:
            environ_data = f.read().decode("utf-8").split("\x00")
        for entry in environ_data:
            if entry:
                key, value = entry.split("=", 1)
                if key == "OPTOUT":
                    return value.lower() == "true"
        return False
    except FileNotFoundError:
        return False


def pseudonymize_username(username):
    """Anonymise usernames using a hash. A pepper is set by the opperator as
    an environment variable so usernames cannot be derived."""
    pepper = os.environ.get("PEPPER")
    if pepper is None:
        print("PEPPER NOT SET! Please set an environment variabled called 'PEPPER' with a sufficiently long string for username anonymization.")
        sys.exit(1)
    username_pepper = username + pepper
    hashed = hashlib.sha256(username_pepper.encode()).hexdigest()
    return hashed


def extract_package(input_string):
    """Extract the name of the python package listed as an open file.
    Looks for python files in the 'site-packages' directory."""
    match = re.search(r'site-packages\/(.*?)\/', input_string)
    if match:
        captured_text = match.group(1)
        return captured_text
    return None


def parse_line(line):
    """Extract the process id, username and package from contents of lsof."""
    parsed = [val for val in line.split(" ") if val]
    pid = parsed[1]
    user = pseudonymize_username(parsed[4])
    package = extract_package(parsed[-1])
    if package is not None and user_optout(pid) is False and user != pseudonymize_username("REG"):
        return (pid, user, package)

def sample_lsof():
    """Run lsof and process the output."""
    utc_now = datetime.utcnow()
    execution_time = utc_now.strftime('%Y-%m-%d %H:%M:%S')
    if not os.path.exists(outfile):
        with open(outfile, "w") as f:
            f.write(header + "\n")
    try:
        output = subprocess.check_output(
            lsof_command,
            shell=True,
            universal_newlines=True
        )
    except subprocess.CalledProcessError as e:
        return

    results = []
    for line in output.split("\n"):
        if line:
            vals = parse_line(line)
            if vals:
                results.append(vals + (execution_time, ))

    if len(set(results)) > 0:
        to_append = "\n".join([", ".join(item) for item in set(results)])
        with open(outfile, "a") as f:
            f.write(to_append + "\n")


if __name__ == "__main__":
    duration = 300
    start = time.time()
    while time.time() - start < duration:
        print("Sampling open files")
        sample_lsof()
        time.sleep(10)
