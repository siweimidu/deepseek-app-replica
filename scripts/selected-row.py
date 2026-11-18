"""Official selected-row colors + make sure a plain tap always switches sessions."""

import re
from pathlib import Path

# ---------- 1) 选中行配色（取色器实测官方 #283142 / #5f9dff） ----------
ITEM = Path('src/components/sider/SessionItem.module.css')
css = ITEM.read_text(encoding='utf-8')

css = css.replace(
    """  &.active {
    background-color: var(--dsw-specific-sidebar-nav-item-active-accent);
    color: var(--dsw-alias-brand-primary-invert);
  }""",
    """  &.active {
    /* 官方选中行：深藏青底 + 蓝色文字（取色器实测 #283142 / #5f9dff） */
    background-color: #e9efff;
    color: #2f5bd6;
  }""",
    1,
)

# 清掉重复嵌套的 hover 保护
css = re.sub(
    r'@media \(hover: hover\) \{\s*@media \(hover: hover\) \{\s*(&:not\(\.active\):hover \{[^{}]*\})\s*\}\s*\}',
    r'@media (hover: hover) {\n    \1\n  }',
    css,
)

css = css.rstrip() + """

/* 深色下选中行用官方的藏青底与蓝字 */
[data-ds-dark-theme] .item.active {
  background-color: #283142;
  color: #5f9dff;
}
"""
ITEM.write_text(css, encoding='utf-8')
print('selected row colors applied')

# ---------- 2) 点不动会话：拖拽抑制标志必须每次按下都复位 ----------
SIDER = Path('src/components/sider/Sider.tsx')
sider = SIDER.read_text(encoding='utf-8')

OLD_DOWN = """        onPointerDown={(event) => {
          if (!android || !open) {
            return
          }
          drag.current = {"""
NEW_DOWN = """        onPointerDown={(event) => {
          if (!android || !open) {
            return
          }
          // 每次按下都复位：上一次拖拽若被系统打断，标志会一直为真，导致后续点击全被吞掉
          dragged.current = false
          drag.current = {"""
assert OLD_DOWN in sider, 'pointerdown not found'
sider = sider.replace(OLD_DOWN, NEW_DOWN, 1)

OLD_CANCEL = """        onPointerCancel={() => {
          if (drag.current?.horizontal) {
            settle(false)
          }
          drag.current = null
        }}"""
NEW_CANCEL = """        onPointerCancel={() => {
          if (drag.current?.horizontal) {
            settle(false)
          }
          drag.current = null
          dragged.current = false
        }}"""
assert OLD_CANCEL in sider, 'pointercancel not found'
sider = sider.replace(OLD_CANCEL, NEW_CANCEL, 1)

SIDER.write_text(sider, encoding='utf-8')
print('tap suppression reset on every touch')

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 23', gradle), encoding='utf-8')
print('versionCode 23')
