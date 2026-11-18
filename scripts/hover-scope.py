"""Touch devices keep :hover stuck after a tap; scope hover styles to real pointers."""

import re
from pathlib import Path

TARGETS = [
    'src/components/sider/Sider.module.css',
    'src/components/sider/SessionItem.module.css',
    'src/components/base/Menu.module.css',
    'src/components/settings/AndroidSettings.module.css',
]

# 匹配形如 "  &:hover { ... }" 或 ".foo:hover { ... }" 的块（单层大括号）
PATTERN = re.compile(r'(?P<indent>[ \t]*)(?P<selector>[^\n{}]*:hover[^\n{}]*)\{[^{}]*\}', re.M)


def guard(match: re.Match) -> str:
    indent = match.group('indent')
    block = match.group(0)
    body = block.strip()
    return f"{indent}@media (hover: hover) {{\n{indent}  {body}\n{indent}}}"


changed = 0
for path in TARGETS:
    file = Path(path)
    text = file.read_text(encoding='utf-8')
    new = PATTERN.sub(guard, text)
    if new != text:
        file.write_text(new, encoding='utf-8')
        changed += 1
        print('guarded', path)

print('files changed', changed)
