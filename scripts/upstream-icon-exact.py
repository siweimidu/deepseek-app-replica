"""图标与按钮参数完全按上游来。"""

import re
from pathlib import Path

SIDER = Path('src/components/sider/Sider.tsx')
sider = SIDER.read_text(encoding='utf-8')

start = sider.index('        {androidDrawer && !selecting ? (')
end = sider.index('        ) : null}', start) + len('        ) : null}\n')
OLD = sider[start:end]

NEW = """        {androidDrawer && !selecting ? (
          <IconButton
            className={styles.selectChats}
            icon={
              <svg
                width="18"
                height="18"
                viewBox="0 0 18 18"
                fill="none"
                stroke="currentColor"
                aria-hidden="true"
              >
                <circle cx="4" cy="5" r="1.6" />
                <circle cx="4" cy="13" r="1.6" />
                <path d="M8 5h7M8 13h7" strokeWidth="1.2" />
              </svg>
            }
            aria-label={t('androidSelectChats')}
            onClick={() => setSelecting(true)}
          />
        ) : null}
"""
sider = sider[:start] + NEW + sider[end:]
SIDER.write_text(sider, encoding='utf-8')
print('icon + props now match upstream')

# CSS 与上游一致（不加 [data-android] 作用域）
CSS = Path('src/components/sider/Sider.module.css')
css = CSS.read_text(encoding='utf-8')
css = re.sub(
    r"/\* 「选择对话」入口[^\n]*\n\[data-android\] \.selectChats \{[\s\S]*?\n\}\n",
    """.selectChats {
  position: absolute;
  top: 6px;
  right: 1px;
  z-index: 25;
}
""",
    css,
)
CSS.write_text(css, encoding='utf-8')
print('selectChats css matches upstream')

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 59', gradle), encoding='utf-8')
print('versionCode 59')
