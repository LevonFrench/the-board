import re
from pathlib import Path

CRITERION = re.compile(r"^[ \t]*[-*][ \t]+`?([A-Za-z0-9][\w.-]*(?:[ \t][\w.-]+){0,3})`?[ \t]*:", re.M)


def rubric_criteria(path):
    """Criterion names, lower case, from rubric lines shaped `- name: what to check`.

    A name is one to four words before the colon, so a prose bullet such as "- Use when the file is X: ..." is not read
    as a criterion.
    """
    return {m.group(1).strip().lower() for m in CRITERION.finditer(Path(path).read_text(encoding="utf-8"))}
