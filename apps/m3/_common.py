import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, REPO_ROOT)


def get_input():
    if len(sys.argv) < 2:
        print("you need a file")
        sys.exit(1)
    filename = sys.argv[1]
    ext = os.path.splitext(filename)[1].lower()
    parser = "xml" if ext == ".xml" else "html.parser"
    return filename, parser
