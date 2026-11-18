"""Wire the full-screen session search page: drawer field opens it, App mounts it."""

import re
from pathlib import Path

# 1) 抽屉里的搜索框改成打开整页搜索
SIDER = Path('src/components/sider/Sider.tsx')
sider = SIDER.read_text(encoding='utf-8')
if 'openSessionSearch' not in sider:
    sider = sider.replace(
        "import { useSessionSearch } from './useSessionSearch.js'",
        "import { openSessionSearch } from '../search/SessionSearchPage.js'",
        1,
    )
    sider = sider.replace(
        """              placeholder={t('androidSearchChats')}""",
        """              placeholder={t('androidSearchChats')}
              readOnly
              onFocus={(event) => {
                event.currentTarget.blur()
                openSessionSearch()
              }}""",
        1,
    )
    SIDER.write_text(sider, encoding='utf-8')
    print('drawer search opens the page')

# 2) App 挂载搜索页
APP = Path('src/app/App.tsx')
app = APP.read_text(encoding='utf-8')
if 'SessionSearchPage' not in app:
    app = app.replace(
        "import { SearchPanel } from '../components/search/SearchPanel.js'",
        "import { SearchPanel } from '../components/search/SearchPanel.js'\nimport { SessionSearchPage } from '../components/search/SessionSearchPage.js'",
        1,
    )
    app = app.replace(
        "      {android ? <ImportStatusBar /> : null}",
        "      {android ? <SessionSearchPage /> : null}\n      {android ? <ImportStatusBar /> : null}",
        1,
    )
    APP.write_text(app, encoding='utf-8')
    print('App mounts the search page')

# 3) 文案
for path, add in (
    (Path('src/i18n/zh.ts'), "  androidSearchEmpty: '没有找到相关对话',\n"),
    (Path('src/i18n/en.ts'), "  androidSearchEmpty: 'No matching conversations',\n"),
):
    text = path.read_text(encoding='utf-8')
    if 'androidSearchEmpty' not in text:
        text = text.replace('  androidSearchChats:', add + '  androidSearchChats:', 1)
        path.write_text(text, encoding='utf-8')
        print('i18n', path)

# 4) 抽屉不再用内嵌搜索（保留 hook 以免影响别处）
GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 27', gradle), encoding='utf-8')
print('versionCode 27')
