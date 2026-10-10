---
name: use-modern-python
description: Write modern, idiomatic Python that uses every language and stdlib feature available up to the project's minimum supported Python version, and nothing newer. Detects the target version from pyproject.toml (requires-python, Poetry), setup.cfg, setup.py, or .python-version. Use this skill whenever writing, refactoring, reviewing, or modernizing Python code in a repository, including small edits, new modules, tests, and scripts, even if the user doesn't say "modern". Also use when the user asks which Python features they can use, wants to upgrade old idioms, or mentions match statements, type hints, generics, typing, or Python version compatibility.
---

# Modern Python Guidelines

Coding agents tend to write Python as if it were 2019: `Optional[List[Dict[str, Any]]]`, `TypeVar` boilerplate, `os.path` everywhere, `if/elif` towers where a `match` would do. This skill fixes that by pinning a target version and then using everything that version offers.

## Step 1: Find the target version

Run the detector from the project root, using the script bundled beside this skill:

```bash
python3 <skill-directory>/scripts/detect_python_version.py .
```

Replace `<skill-directory>` with the directory containing this `SKILL.md`.

It prints `TARGET=3.X (from ...)` or `TARGET=unknown`. The *floor* of the supported range is the target, because code must run on the oldest interpreter the project claims to support. `requires-python = ">=3.10"` means target 3.10, even if the developer runs 3.14 locally.

Then say one of these out loud before writing code, so the user can correct you early:

- "This project targets Python 3.X, so I'll use modern features up to and including 3.X."
- "I couldn't detect a Python version." Then ask which version to target (offer the currently supported ones: 3.10, 3.11, 3.12, 3.13, 3.14). For a brand-new project with no constraints, suggest the newest stable release.

If the user explicitly names a version, that overrides the detector.

## Step 2: Write code using the rules below

The rules:

- Use **every** feature from the table below up to the target version. When a modern form exists, the old form is wrong for this project.
- Never use a feature newer than the target. A `match` statement in a 3.9 project is a `SyntaxError` for every user on 3.9.
- Match the style of surrounding code for things this skill doesn't cover (naming, layout, framework conventions). Modernize what you touch; don't rewrite untouched files unless asked.
- **Backports via `typing_extensions`**: if the project already depends on `typing_extensions`, newer typing features (`Self`, `override`, `TypeIs`, `ReadOnly`, `deprecated`, `TypeVar` defaults) can be imported from it below their native version. Don't add the dependency yourself without asking.
- **Runtime vs. annotation**: some libraries (Pydantic, FastAPI, dataclasses, attrs, typer) evaluate annotations at runtime. In those contexts, syntax like `int | None` needs the real version (3.10), not just `from __future__ import annotations`.

## Features by version

Each entry: what to use, and what it replaces. Cumulative: a 3.12 project uses everything from 3.12 and below.

### Always (3.8+ baseline; every supported version has these)

- f-strings for formatting, including `f"{value=}"` for debug output. Not `%` or `.format()` (except for logging calls, which should stay lazy: `log.info("x=%s", x)`).
- `pathlib.Path` for filesystem work. Not `os.path.join`, `open(os.path...)`. Use `Path.read_text()` / `write_text()` for whole-file I/O, and pass `encoding="utf-8"` explicitly.
- Walrus `:=` where it removes a duplicated call: `if (m := pattern.match(s)):`, `while (chunk := f.read(8192)):`. Don't use it just to look clever.
- Positional-only params `/` in public APIs whose parameter names aren't part of the contract.
- `dataclasses` for plain data holders, not hand-written `__init__`/`__repr__`/`__eq__`.
- `typing.Literal`, `Final`, `Protocol`, `TypedDict`. Prefer `Protocol` over ABCs for structural interfaces.
- `functools.cached_property`, `math.prod`, `math.isqrt`, `importlib.metadata.version(...)` (not `pkg_resources`).
- Access named regex groups with subscription: `m['year']`, not `m.group('year')`.
- `enumerate`, `zip`, comprehensions, unpacking `first, *rest = items`. No `range(len(x))`.
- `super()` without arguments. No `class Foo(object)`. No `# -*- coding: utf-8 -*-`.

### 3.9+

- Built-in generics in annotations: `list[int]`, `dict[str, Any]`, `tuple[int, ...]`, `type[Foo]`. Not `typing.List`, `Dict`, `Tuple`, `Type`.
- `collections.abc.Iterable`, `Callable`, `Mapping`, etc. for annotations. Not the deprecated `typing` aliases.
- Dict merge: `merged = a | b`, `config |= overrides`. Not `{**a, **b}` or `.update()` on a copy.
- `str.removeprefix()` / `removesuffix()`. Not `s[len(p):] if s.startswith(p)`. (Note: `lstrip("abc")` strips characters, not a prefix; it's a classic bug.)
- `functools.cache` instead of `lru_cache(maxsize=None)`.
- `asyncio.to_thread()` to run blocking I/O without blocking the event loop.
- `zoneinfo.ZoneInfo("Europe/London")` instead of `pytz`.
- `typing.Annotated` for metadata on types (Pydantic, FastAPI, typer all use it).
- `graphlib.TopologicalSorter` for dependency ordering. `math.lcm`.

### 3.10+

- Union syntax: `int | None`, `str | bytes`. Not `Optional[int]` or `Union[str, bytes]`. Also works in `isinstance(x, int | str)`.
- Structural pattern matching `match`/`case` for dispatching on shape, type, or literal values:
  ```python
  match command:
      case {"action": "move", "x": int(x), "y": int(y)}:
          move(x, y)
      case {"action": "quit"}:
          quit()
      case _:
          raise ValueError(f"unknown command: {command!r}")
  ```
  Use it when it replaces `isinstance` chains or nested dict/tuple unpacking. Don't use it for a simple two-way `if`.
- `zip(a, b, strict=True)` when lengths must match (they usually should).
- Parenthesized context managers:
  ```python
  with (
      open(src) as fin,
      open(dst, "w") as fout,
  ):
  ```
- `@dataclass(slots=True, kw_only=True)` where it fits.
- `typing.TypeAlias`, `ParamSpec` (for decorators that preserve signatures), `TypeGuard`, `Concatenate`.
- `itertools.pairwise`, `bisect` with `key=`, `int.bit_count()`, `aiter()` / `anext()`.

### 3.11+

- `typing.Self` for methods returning their own class. Not `TypeVar("T", bound="Foo")`.
- `asyncio.TaskGroup` for concurrent tasks. Not bare `gather()` with manual cancellation.
- `asyncio.timeout(5)` as a context manager. Not `wait_for`.
- `asyncio.timeout_at(deadline)` when nested operations should share one absolute deadline.
- `ExceptionGroup` and `except*` when handling multiple concurrent failures (e.g. from a `TaskGroup`).
- `err.add_note("context")` to attach context to an exception instead of wrapping it in a new one.
- `tomllib` for reading TOML. Not the `toml` / `tomli` packages.
- `enum.StrEnum` instead of `class Color(str, Enum)`.
- `datetime.UTC` (alias for `timezone.utc`).
- `typing.Never`, `assert_never()` for exhaustiveness checks in `match`, `LiteralString`, `Required` / `NotRequired` in `TypedDict`, `TypeVarTuple` / `Unpack` for variadic generics.
- `contextlib.chdir()`.

### 3.12+

- PEP 695 type parameter syntax. This is the big one:
  ```python
  # Old
  T = TypeVar("T")
  def first(items: list[T]) -> T: ...
  class Box(Generic[T]): ...
  Pair: TypeAlias = tuple[T, T]

  # New
  def first[T](items: list[T]) -> T: ...
  class Box[T]: ...
  type Pair[T] = tuple[T, T]
  ```
  Bounds and constraints: `def f[T: Hashable](x: T)`, `def g[S: (str, bytes)](x: S)`.
- `@typing.override` on methods that override a parent method.
- f-strings can nest the same quotes and span lines (PEP 701): `f"{d["key"]}"` is legal now.
- `itertools.batched(items, 100)` instead of hand-rolled chunking.
- `Path.walk()` instead of `os.walk()`.
- `**kwargs: Unpack[MyTypedDict]` to type keyword arguments precisely.
- Don't use `datetime.utcnow()` / `utcfromtimestamp()` (deprecated). Use `datetime.now(UTC)`.
- `distutils` is gone. Use `setuptools` or `packaging`.

### 3.13+

- `warnings.deprecated` decorator to mark deprecated APIs (type checkers see it, too).
- `typing.TypeIs` instead of `TypeGuard` for narrowing (it narrows in both branches).
- Type parameter defaults: `class Box[T = int]:`.
- `typing.ReadOnly` for `TypedDict` keys.
- `copy.replace(obj, field=new)` works on dataclasses, namedtuples, and more.
- `itertools.batched(items, size, strict=True)` when a short final batch should raise `ValueError`.
- Dead batteries removed (PEP 594): no `cgi`, `cgitb`, `crypt`, `telnetlib`, `imghdr`, `pipes`, `nntplib`, `audioop`, and friends. Use third-party replacements.

### 3.14+

- Annotations are evaluated lazily (PEP 649/749). Forward references just work: no `from __future__ import annotations`, no quoted `"ClassName"` hints. Remove the future import in new 3.14+ code. Use `annotationlib` to introspect annotations.
- `except ValueError, TypeError:` without parentheses is allowed (when there's no `as`). Use parentheses anyway if the codebase does; consistency beats novelty here.
- Template strings `t"..."` (PEP 750, `string.templatelib`) for safe interpolation into SQL, HTML, shell commands, and similar. Prefer them over f-strings when building anything that needs escaping, provided the consuming library supports templates.
- `return` / `break` / `continue` in `finally` now warns (PEP 765). Don't write it.
- `compression.zstd` for Zstandard. `uuid.uuid7()` for time-ordered IDs (great for DB keys).
- `Path.copy()`, `Path.move()` instead of `shutil` for single paths.
- `map(fn, a, b, strict=True)`.
- `heapq.heappush_max` and friends: no more negating values for a max-heap.
- Free-threaded (no-GIL) builds are officially supported. Don't assume the GIL protects shared mutable state in new concurrent code.

### 3.15+ (verify against the official "What's New" if precision matters)

- `lazy import heavy_module` to defer import cost, for CLIs and big apps with slow startup.
- UTF-8 is the default encoding. Still pass `encoding=` explicitly if the code must also run on older versions.
- `frozendict` builtin for immutable mappings.
- `profiling` package (`profiling.sampling` statistical profiler; `profiling.tracing` replaces direct `cProfile` use).
- `typing.TypeForm` for annotating values that are themselves type expressions.

## Patterns that are outdated at every supported version

Fix these whenever you touch the code. All of them are wrong in any Python a project could still target:

- Mutable default arguments: `def f(x=[])`. Use `None` and create inside.
- Bare `except:` or `except Exception: pass`. Catch what you mean, and log or re-raise.
- `type(x) == Foo`. Use `isinstance`.
- Manual `open()`/`close()`. Use `with`.
- `"%s" % x` or string concatenation in loops for building output. Use f-strings or `"".join(...)`.
- `dict.keys()` in membership tests: `if k in d.keys()`. Just `if k in d`.
- Use `re.fullmatch()` when the entire string must match; use `re.escape()` when inserting literal text into a regex pattern.
- `requests.get(...)` with no `timeout=`.
- `print` debugging left in library code. Use `logging`.
- `assert` for runtime validation of user input (it's stripped with `-O`).

## Step 3: Verify (optional but recommended)

If `ruff` is available, its pyupgrade rules catch most version-gated idioms automatically:

```bash
ruff check --select UP --target-version py3XX .
```

Replace `3XX` with the target (e.g. `py312`). This is a good final check after writing code, and a fast way to modernize an existing file the user asked you to upgrade. If the project already configures ruff, use its config rather than overriding it.
