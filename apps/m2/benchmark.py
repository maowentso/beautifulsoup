"""Compare the Milestone 2 apps with the Milestone 1 programs.

Usage: python benchmark.py <file> [<file> ...]

For each task, the Milestone 1 program (milestone1/taskN.py, full parse) and
the Milestone 2 program (taskN.py, SoupStrainer / SoupReplacer) are run in
separate processes on the same file, both using the bs4 in this repository.
The script reports wall time, peak memory (max RSS) and whether the two
programs produced the same output.
"""
import ast
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))

# Runs a script the way "python script.py file" would, then reports the time
# and peak memory of the whole process on stderr.
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
        output = proc.stdout
        written = os.path.join(cwd, "output_task6.html")
        if os.path.exists(written):
            with open(written, encoding="utf-8") as f:
                output += f.read()
    line = [l for l in proc.stderr.splitlines() if l.startswith("BENCH ")][-1]
    elapsed, rss = json.loads(line[len("BENCH "):])
    return output, elapsed, rss


def normalize(task, output):
    if task == 3:
        # A printed set has no fixed order.
        return ast.literal_eval(output.split(":", 1)[1].strip())
    return output


def main():
    files = sys.argv[1:]
    if not files:
        print("Usage: python benchmark.py <file> [<file> ...]")
        sys.exit(1)
    print(f"{'file':<12} {'task':<5} {'M1 time':>9} {'M2 time':>9} "
          f"{'M1 peak':>9} {'M2 peak':>9} {'output':>9}")
    for filename in files:
        filename = os.path.abspath(filename)
        for task in (2, 3, 4, 6):
            m1_out, m1_t, m1_rss = run(os.path.join(HERE, "milestone1", f"task{task}.py"), filename)
            m2_out, m2_t, m2_rss = run(os.path.join(HERE, f"task{task}.py"), filename)
            same = normalize(task, m1_out) == normalize(task, m2_out)
            print(f"{os.path.basename(filename):<12} {task:<5} {m1_t:>8.2f}s {m2_t:>8.2f}s "
                  f"{m1_rss / 1e6:>7.0f}MB {m2_rss / 1e6:>7.0f}MB "
                  f"{'same' if same else 'DIFFERENT':>9}")


if __name__ == "__main__":
    main()
