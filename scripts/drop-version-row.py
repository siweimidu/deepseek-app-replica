"""Drop the version row from About; keep only the terms entry."""

import re
from pathlib import Path

SETTINGS = Path('src/components/settings/AndroidSettings.tsx')
text = SETTINGS.read_text(encoding='utf-8')

ROW = "              <Row label={tr('版本信息', 'Version')} value={appVersion} icon={<Info />} />\n"
assert ROW in text, 'version row not found'
text = text.replace(ROW, '')

# 一并清掉只为这一行服务的变量
text = text.replace("const nativeVersion = android?.versionLabel?.()\n", '')
text = re.sub(
    r"const appVersion = nativeVersion \?\? document\.querySelector<HTMLMetaElement>\([\s\S]*?\)\?\.content \?\? ''\n",
    '',
    text,
)
SETTINGS.write_text(text, encoding='utf-8')
print('version row removed:', '版本信息' not in text)

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 19', gradle), encoding='utf-8')
print('versionCode 19')
