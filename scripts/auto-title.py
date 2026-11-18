"""新会话自动命名（本地兜底）+ 侧边栏把当前会话顶到最上面。"""

import re
from pathlib import Path

# ---------- 1) 本地标题生成 ----------
TITLE = Path('src/services/chat/title.ts')
TITLE.write_text("""import { getSession, updateSession } from './store.js'
import { db } from './db.js'

/** 侧边栏标题上限（按字符数，中文一个字算一个） */
const TITLE_LIMIT = 13

/** 从首轮内容里提炼一个短标题：去代码块、去换行、去多余标点 */
const clean = (text: string) =>
  text
    .replace(/```[\\s\\S]*?```/g, ' ')
    .replace(/`[^`]*`/g, ' ')
    .replace(/!?\\[[^\\]]*\\]\\([^)]*\\)/g, ' ')
    .replace(/^[#>*\\-\\s]+/gm, '')
    .replace(/\\s+/g, ' ')
    .trim()

export const buildTitle = (firstUserText: string): string => {
  const text = clean(firstUserText)
  if (!text) {
    return ''
  }
  // 优先在句读处断开，避免半句话
  const head = text.split(/[。！？!?；;\\n]/)[0] ?? text
  const source = head.length >= 4 ? head : text
  const chars = Array.from(source)
  if (chars.length <= TITLE_LIMIT) {
    return source.replace(/[，,、：:\\s]+$/, '')
  }
  return `${chars.slice(0, TITLE_LIMIT).join('').replace(/[，,、：:\\s]+$/, '')}…`
}

/**
 * 会话还没有标题时，用第一轮对话生成一个。
 * 服务端会返回 title，但并非所有后台都支持，这里做本地兜底。
 */
export const ensureLocalTitle = (sessionId: string) => {
  const session = getSession(sessionId)
  if (!session || session.title.trim()) {
    return
  }
  const firstUser = session.messages.find((message) => message.role === 'user')
  if (!firstUser || firstUser.role !== 'user') {
    return
  }
  const hasReply = session.messages.some((message) => message.role === 'assistant')
  if (!hasReply) {
    return
  }
  const title = buildTitle(firstUser.content)
  if (!title) {
    return
  }
  updateSession(sessionId, (current) => (current.title ? current : { ...current, title }))
  void db.renameSession(sessionId, title).catch(db.reportStorageError('title session'))
}
""", encoding='utf-8')
print('title module created')

# ---------- 2) 流式结束后调用 ----------
STORE = Path('src/services/chat/store.ts')
store = STORE.read_text(encoding='utf-8')
if 'ensureLocalTitle' not in store:
    store = store.replace(
        "import { ensureAnchor, withAnchor } from './context/anchor.js'",
        "import { ensureAnchor, withAnchor } from './context/anchor.js'\nimport { ensureLocalTitle } from './title.js'",
        1,
    )
    # 在与 done 结算同一处触发
    store = store.replace(
        """          reply = applyEvent(reply, event, Date.now(), blockIndexes)
          if (document.visibilityState === 'hidden') {
            flush()""",
        """          if (event.type === 'message_delta' && event.delta?.stop_reason) {
            ensureLocalTitle(sessionId)
          }
          reply = applyEvent(reply, event, Date.now(), blockIndexes)
          if (document.visibilityState === 'hidden') {
            flush()""",
        1,
    )
STORE.write_text(store, encoding='utf-8')
print('ensureLocalTitle wired into stream')

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 49', gradle), encoding='utf-8')
print('versionCode 49')
