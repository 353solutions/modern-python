#!/usr/bin/env python3
"""Detect the minimum Python version a project supports.

Usage: python3 detect_python_version.py [project_root]

Prints one line the agent can act on, e.g.:
    TARGET=3.11 (from pyproject.toml [project] requires-python = ">=3.11")
or:
    TARGET=unknown

The *floor* of the supported range wins, because code has to run on the
oldest interpreter the project claims to support. .python-version and
similar "dev interpreter" files are only used as a fallback, since they
describe what the developer runs, not what users run.

Written to run on Python 3.8+ (yes, the irony is noted).
"""
import configparser
import os
import re
import sys

try:
    import tomllib  # 3.11+
except ImportError:  # pragma: no cover
    tomllib = None

VERSION_RE = re.compile(r"3\.(\d+)")


def floor_from_spec(spec):
    """Return the lowest 3.x version allowed by a version spec string.

    Handles PEP 440 (>=3.10, ~=3.11, ==3.12.*, >3.9), Poetry (^3.11, ~3.11),
    and bare versions (3.12). Upper bounds (<4, <=3.13) are ignored.
    """
    if not spec:
        return None
    best = None
    for part in re.split(r"[,|]", str(spec)):
        part = part.strip()
        if not part or part.startswith("<") or part.startswith("!="):
            continue
        m = VERSION_RE.search(part)
        if not m:
            continue
        minor = int(m.group(1))
        # ">3.9" means 3.10+ in practice for minor-version purposes
        if part.startswith(">") and not part.startswith(">="):
            exact = re.search(r"3\.\d+(\.\d+)?", part).group(0)
            if exact.count(".") == 1:
                minor += 1
        best = minor if best is None else min(best, minor)
    return None if best is None else "3.%d" % best


def read_toml(path):
    with open(path, "rb") as f:
        raw = f.read()
    if tomllib is not None:
        try:
            return tomllib.loads(raw.decode("utf-8")), raw.decode("utf-8")
        except Exception:
            pass
    return None, raw.decode("utf-8", "replace")


def from_pyproject(root):
    path = os.path.join(root, "pyproject.toml")
    if not os.path.isfile(path):
        return []
    data, text = read_toml(path)
    found = []
    if data is not None:
        rp = data.get("project", {}).get("requires-python")
        if rp:
            found.append((rp, 'pyproject.toml [project] requires-python = "%s"' % rp))
        poetry = data.get("tool", {}).get("poetry", {}).get("dependencies", {}).get("python")
        if poetry:
            found.append((poetry, 'pyproject.toml [tool.poetry.dependencies] python = "%s"' % poetry))
        ruff = data.get("tool", {}).get("ruff", {}).get("target-version")
        if ruff and not found:
            v = re.sub(r"py3(\d+)", r"3.\1", ruff)
            found.append((v, 'pyproject.toml [tool.ruff] target-version = "%s"' % ruff))
        mypy = data.get("tool", {}).get("mypy", {}).get("python_version")
        if mypy and not found:
            found.append((str(mypy), 'pyproject.toml [tool.mypy] python_version = "%s"' % mypy))
    else:  # regex fallback when tomllib is unavailable
        m = re.search(r'requires-python\s*=\s*["\']([^"\']+)["\']', text)
        if m:
            found.append((m.group(1), 'pyproject.toml requires-python = "%s"' % m.group(1)))
    return found


def from_setup_cfg(root):
    path = os.path.join(root, "setup.cfg")
    if not os.path.isfile(path):
        return []
    cp = configparser.ConfigParser()
    try:
        cp.read(path)
        val = cp.get("options", "python_requires", fallback=None)
    except Exception:
        val = None
    return [(val, 'setup.cfg python_requires = "%s"' % val)] if val else []


def from_setup_py(root):
    path = os.path.join(root, "setup.py")
    if not os.path.isfile(path):
        return []
    with open(path, encoding="utf-8", errors="replace") as f:
        m = re.search(r'python_requires\s*=\s*["\']([^"\']+)["\']', f.read())
    return [(m.group(1), 'setup.py python_requires = "%s"' % m.group(1))] if m else []


def from_dev_files(root):
    """Fallback signals: these describe the dev/runtime interpreter."""
    found = []
    for name in (".python-version", "runtime.txt", ".tool-versions"):
        path = os.path.join(root, name)
        if os.path.isfile(path):
            with open(path, encoding="utf-8", errors="replace") as f:
                text = f.read()
            m = VERSION_RE.search(text)
            if m:
                found.append(("3." + m.group(1), "%s (dev interpreter, not a declared floor)" % name))
    pipfile = os.path.join(root, "Pipfile")
    if os.path.isfile(pipfile):
        with open(pipfile, encoding="utf-8", errors="replace") as f:
            m = re.search(r'python_version\s*=\s*["\']([^"\']+)["\']', f.read())
        if m:
            found.append((m.group(1), 'Pipfile python_version = "%s"' % m.group(1)))
    return found


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    declared = from_pyproject(root) + from_setup_cfg(root) + from_setup_py(root)
    candidates = declared or from_dev_files(root)

    results = [(floor_from_spec(spec), source) for spec, source in candidates]
    results = [(v, s) for v, s in results if v]
    if not results:
        print("TARGET=unknown")
        return

    # Lowest floor across declared sources wins.
    target, source = min(results, key=lambda r: int(r[0].split(".")[1]))
    print("TARGET=%s (from %s)" % (target, source))
    others = [s for v, s in results if s != source]
    if others:
        print("OTHER SIGNALS: " + "; ".join(others))


if __name__ == "__main__":
    main()
