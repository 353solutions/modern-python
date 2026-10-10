# Modern Python

An installable agent plugin containing the `use-modern-python` skill. It helps
coding agents detect a project's minimum supported Python version and apply
modern language and standard-library features without exceeding that version.

The skill is shared by Claude Code and Codex. Its detector script is bundled
with the skill and requires Python 3.8 or newer.

> [!NOTE]
> The version-aware guidance in this skill was inspired by JetBrains’
> [Modern Go guidelines](https://github.com/JetBrains/go-modern-guidelines).
> This skill applies a similar approach to Python.

## Install in Claude Code

Add this repository as a marketplace, then install the plugin:

```text
/plugin marketplace add 353solutions/modern-python
/plugin install modern-python@modern-python-guides
```

Or load the plugin from a local checkout for one session:

```bash
claude --plugin-dir ./plugins/modern-python
```

The skill appears as `/modern-python:use-modern-python`.

## Install in Codex

Add this repository as a plugin marketplace:

```bash
codex plugin marketplace add 353solutions/modern-python
codex plugin add modern-python@modern-python-guides
```

Or open the plugin browser with `codex /plugins`, select
**modern-python-guides**, and install **Modern Python**. The
`use-modern-python` skill is bundled in the plugin and is available when the
plugin is enabled; invoke it with `$use-modern-python`.

For repo-scoped use without installing the plugin, copy
`plugins/modern-python/skills/use-modern-python` into the project's
`.agents/skills/` directory.

## Recommended project instruction

To have the agent use the skill whenever it works on Python files, add an
instruction to the project's rules file.

For Claude Code, add this to `CLAUDE.md`:

```text
When working with Python files, always use the `/modern-python:use-modern-python` skill.
```

For Codex, add the equivalent instruction to `AGENTS.md`:

```text
When working with Python files, always use the `$use-modern-python` skill.
```

## What it does

The skill checks version declarations such as `requires-python`, Poetry,
`setup.cfg`, `setup.py`, and `.python-version`. It treats the lowest supported
version as the compatibility target, then recommends language and standard
library features available at that version. It includes a detector script at
`skills/use-modern-python/scripts/detect_python_version.py`.
