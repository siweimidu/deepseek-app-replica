"""Fix the search page against the real store/type APIs."""

import re
from pathlib import Path

PAGE = Path('src/components/search/SessionSearchPage.tsx')
page = PAGE.read_text(encoding='utf-8')

page = page.replace(
    "import { loadSession } from '../../services/chat/db.js'\nimport { useChatStore } from '../../services/chat/store.js'\nimport type { SessionSummary } from '../../services/chat/types.js'",
    "import { loadSession } from '../../services/chat/db.js'\nimport { selectSession, useChatStore } from '../../services/chat/store.js'",
)
page = page.replace(
    "  const selectSession = useChatStore((state) => state.selectSession)\n",
    "",
)
page = page.replace("  const t = useTranslate()\n", "  const t = useTranslate()\n", 1)

# 只搜用户消息里的文本（助手的正文在分段结构里，这里不做深挖）
page = page.replace(
    """        const messageHit = session?.messages.find((message) =>
          (message.role === 'user' || message.role === 'assistant') &&
          (typeof message.content === 'string'
            ? message.content.toLocaleLowerCase().includes(term)
            : false)
        )""",
    """        const messageHit = session?.messages.find(
          (message) => message.role === 'user' && message.content.toLocaleLowerCase().includes(term)
        )""",
)
page = page.replace(
    """        const raw = messageHit?.content
        const text = typeof raw === 'string' ? raw : ''""",
    """        const text = messageHit?.content ?? ''""",
)
page = page.replace("onClick={closeSessionSearch}", "onClick={closeSessionSearch}")
page = page.replace("aria-label={t('back')}", "aria-label=\"返回\"")
page = page.replace("aria-label={t('clear')}", "aria-label=\"清除\"")
PAGE.write_text(page, encoding='utf-8')
print('search page aligned to APIs')

APP = Path('src/app/App.tsx')
app = APP.read_text(encoding='utf-8')
if '<SessionSearchPage />' not in app:
    app = app.replace(
        "      <VoiceCallScreen />",
        "      <SessionSearchPage />\n      <VoiceCallScreen />",
        1,
    )
    APP.write_text(app, encoding='utf-8')
    print('App mounts search page')

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 27', gradle), encoding='utf-8')
print('versionCode 27')
