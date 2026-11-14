import re
from pathlib import Path

CRITERION = re.compile(r"^\s*[-*]\s+`?([A-Za-z0-9][\w .-]*?)`?\s*:", re.M)


def rubric_criteria(path):
    """Criterion names, lower case, from rubric lines shaped `- name: what to check`."""
    return {m.group(1).strip().lower() for m in CRITERION.finditer(Path(path).read_text(encoding="utf-8"))}
