"""Run the audit steps of .github/workflows/build.yml locally, after `python build_site.py`.

pytest alone misses them: on 2026-10-03 three pushes went red on `check_icons.py` (a new innate slug without art)
while the full pytest was green. Every `run: python …` line and every `python - <<'PY'` block of build.yml runs
here in order; the pip install, pytest and the Pages copy steps are skipped.

    python tools/ci_local.py
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKFLOW = os.path.join(ROOT, ".github", "workflows", "build.yml")
SKIP = ("pip install", "python -m pytest", "build_site.py", "cp ", "mkdir ")


def steps(text):
    """[(name, python source or argv list)] of the workflow's runnable steps."""
    out, name = [], "?"
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"\s*- name:\s*(.+)", line)
        if m:
            name = m.group(1).strip()
        m = re.match(r"\s*run:\s*(python \S.*)$", line)
        if m and not any(s in m.group(1) for s in SKIP):
            out.append((name, m.group(1).split()[1:]))
        if re.match(r"\s*python - <<'PY'\s*$", line):
            indent = len(line) - len(line.lstrip())
            body = []
            i += 1
            while i < len(lines) and lines[i].strip() != "PY":
                body.append(lines[i][indent:])
                i += 1
            out.append((name, "\n".join(body)))
        i += 1
    return out


def untracked_data():
    """Untracked files under data/ — CI never sees them, so a step may fail here only because of them."""
    res = subprocess.run(["git", "status", "--porcelain", "--", "data"], cwd=ROOT, text=True, capture_output=True)
    return [ln[3:] for ln in res.stdout.splitlines() if ln.startswith("??")]


def main():
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    local = untracked_data()
    if local:
        print(f"note: {len(local)} untracked file(s) under data/ that CI doesn't have: {', '.join(local[:8])}")
    failed = []
    for name, step in steps(open(WORKFLOW, encoding="utf-8").read()):
        cmd = [sys.executable] + (step if isinstance(step, list) else ["-"])
        res = subprocess.run(cmd, cwd=ROOT, env=env, text=True, encoding="utf-8", errors="replace",
                             input=None if isinstance(step, list) else step, capture_output=True)
        ok = res.returncode == 0
        print(f"{'OK  ' if ok else 'FAIL'} {name}")
        if not ok:
            failed.append(name)
            print((res.stdout + res.stderr).strip()[-2000:])
    print(f"{len(failed)} failed" if failed else "all CI audit steps passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
