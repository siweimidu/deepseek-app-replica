"""Android rows: taller/bigger text, and show the ⋯ action on the active row only."""

import re
from pathlib import Path

ITEM = Path('src/components/sider/SessionItem.module.css')
css = ITEM.read_text(encoding='utf-8')

css = css.replace(
    """[data-android] .item {
  padding-inline: 7px 4px;
  height: 48px;
  user-select: none;""",
    """[data-android] .item {
  /* 官方行更高、字更大、左侧留白更宽 */
  padding-inline: 12px 6px;
  height: 48px;
  font-size: 16px;
  user-select: none;""",
    1,
)

css = css.replace(
    """  .action:focus-within {
    opacity: 1;
    pointer-events: auto;
  }""",
    """  .action:focus-within {
    opacity: 1;
    pointer-events: auto;
  }

  /* 选中行常显「⋯」：官方只在当前会话上露出这个按钮 */
  &.active .action {
    opacity: 1;
    pointer-events: auto;
  }""",
    1,
)

ITEM.write_text(css, encoding='utf-8')
print('row metrics + active dots applied:', '&.active .action' in css)

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 24', gradle), encoding='utf-8')
print('versionCode 24')
