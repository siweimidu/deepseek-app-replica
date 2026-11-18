"""Put the chat card and drawer back on the app's own theme tokens."""

import re
from pathlib import Path

APP = Path('src/app/App.module.css')
app = APP.read_text(encoding='utf-8')
app = app.replace('  background: var(--ds-card-surface, #ffffff);', '  background: var(--dsw-alias-bg-base);')
app = re.sub(
    r'html\[data-android\]:not\(\[data-ds-dark-theme\]\) \.main \{[^}]*\}\n?',
    '',
    app,
)
APP.write_text(app, encoding='utf-8')
print('card -> var(--dsw-alias-bg-base):', 'var(--dsw-alias-bg-base)' in app)

SIDER = Path('src/components/sider/Sider.module.css')
sider = SIDER.read_text(encoding='utf-8')
sider = sider.replace(
    '--drawer-surface: var(--ds-drawer-surface, #ffffff);',
    '--drawer-surface: var(--dsw-specific-sidebar-fill);',
)
sider = sider.replace(
    '--drawer-surface: var(--ds-drawer-surface, #0f0f0f);',
    '--drawer-surface: var(--dsw-specific-sidebar-fill);',
)
SIDER.write_text(sider, encoding='utf-8')
print('drawer -> sidebar-fill:', 'var(--dsw-specific-sidebar-fill);' in sider)

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 15', gradle), encoding='utf-8')
print('versionCode 15')
