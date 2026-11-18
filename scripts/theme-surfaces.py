"""Drive drawer/card surfaces from theme.css variables so both themes flip together."""

from pathlib import Path

THEME = Path('src/app/theme.css')
theme = THEME.read_text(encoding='utf-8')
if '--ds-drawer-surface' not in theme:
    theme += """
/* 侧边栏与对话卡片的表面色：跟着主题走，避免深浅混搭 */
body {
  --ds-drawer-surface: #ffffff;
  --ds-card-surface: #ffffff;
}

body[data-ds-dark-theme] {
  --ds-drawer-surface: #0f0f0f;
  --ds-card-surface: #1d1d1d;
}
"""
    THEME.write_text(theme, encoding='utf-8')
    print('theme vars added')

SIDER = Path('src/components/sider/Sider.module.css')
sider = SIDER.read_text(encoding='utf-8')
# 抽屉表面色改为消费主题变量（浅色白 / 深色 #0f0f0f）
sider = sider.replace('--drawer-surface: #ffffff;', '--drawer-surface: var(--ds-drawer-surface, #ffffff);')
sider = sider.replace('--drawer-surface: #0f0f0f;', '--drawer-surface: var(--ds-drawer-surface, #0f0f0f);')
sider = sider.replace(
    """/* 深色：抽屉比对话卡片更黑（取色器实测 #0f0f0f） */
[data-android] body[data-ds-dark-theme] .drawer {""",
    """/* 深色下边界更分明一点 */
[data-android] body[data-ds-dark-theme] .drawer {""",
)
SIDER.write_text(sider, encoding='utf-8')
print('sider surface uses theme var')

APP = Path('src/app/App.module.css')
app = APP.read_text(encoding='utf-8')
app = app.replace(
    """[data-android] .main {
  background: #ffffff;
}

/* 深色：对话卡片比抽屉亮一档（取色器实测 #1d1d1d） */
[data-android] body[data-ds-dark-theme] .main {
  background: #1d1d1d;
}""",
    """[data-android] .main {
  background: var(--ds-card-surface, #ffffff);
}""",
)
APP.write_text(app, encoding='utf-8')
print('card surface uses theme var')

# 底部账号行的三点按钮离屏幕右缘远一点
sider = SIDER.read_text(encoding='utf-8')
if '.settings > svg' not in sider:
    sider += """
/* 底部账号行的三点按钮往左收一点，别贴着屏幕边 */
[data-android] .mobile .settings {
  padding-right: 10px;
}

[data-android] .mobile .settings > svg {
  margin-right: 4px;
  flex-shrink: 0;
}
"""
    SIDER.write_text(sider, encoding='utf-8')
    print('account row padding tuned')
