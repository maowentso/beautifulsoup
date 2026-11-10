"""Compare Milestone 3 task7.py (SoupReplacer attrs_xformer) with the
Milestone 1 task7.py (parse, then find_all("p") and set the class).

Usage: python benchmark.py <file> [<file> ...]

Both programs run in separate processes on the same file, using the bs4 in
this repository. Reports wall time, peak memory (max RSS) and whether the
two output files are identical.
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))

RUNNER = """
import json, os, resource, runpy, sys, time
script, arg = sys.argv[1], sys.argv[2]
sys.path[:0] = [os.path.dirname(script), {root!r}]
sys.argv = [script, arg]
start = time.perf_counter()
runpy.run_path(script, run_name="__main__")
elapsed = time.perf_counter() - start
rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
if sys.platform != "darwin":
    rss *= 1024  # Linux reports KB, macOS bytes
sys.stderr.write("BENCH " + json.dumps([elapsed, rss]) + "\\n")
"""


def run(script, filename):
    with tempfile.TemporaryDirectory() as cwd:
        proc = subprocess.run(
            [sys.executable, "-c", RUNNER.format(root=REPO_ROOT), script, filename],
            cwd=cwd,
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            sys.exit(f"{script} failed:\n{proc.stderr}")
        with open(os.path.join(cwd, "output_task7.html"), encoding="utf-8") as f:
            output = f.read()
    line = [l for l in proc.stderr.splitlines() if l.startswith("BENCH ")][-1]
    elapsed, rss = json.loads(line[len("BENCH "):])
    return output, elapsed, rss


def main():
    files = sys.argv[1:]
    if not files:
        print("Usage: python benchmark.py <file> [<file> ...]")
        sys.exit(1)
    print(f"{'file':<12} {'M1 time':>9} {'M3 time':>9} {'M1 peak':>9} {'M3 peak':>9} {'output':>9}")
    for filename in files:
        filename = os.path.abspath(filename)
        m1_out, m1_t, m1_rss = run(os.path.join(HERE, "milestone1", "task7.py"), filename)
        m3_out, m3_t, m3_rss = run(os.path.join(HERE, "task7.py"), filename)
        same = "same" if m1_out == m3_out else "DIFFERENT"
        print(f"{os.path.basename(filename):<12} {m1_t:>8.2f}s {m3_t:>8.2f}s "
              f"{m1_rss / 1e6:>7.0f}MB {m3_rss / 1e6:>7.0f}MB {same:>9}")


if __name__ == "__main__":
    main()
