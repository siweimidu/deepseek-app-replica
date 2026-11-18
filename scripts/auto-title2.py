"""把本地标题逻辑放进 store（那里才有 getSession/updateSession/persist）。"""

import re
from pathlib import Path

TITLE = Path('src/services/chat/title.ts')
if TITLE.exists():
    TITLE.unlink()
    print('title.ts removed')

STORE = Path('src/services/chat/store.ts')
store = STORE.read_text(encoding='utf-8')

# 去掉刚才加的 import（如果加进去了）
store = store.replace("import { ensureLocalTitle } from './title.js'\n", '')

# 在 renameSession 之后插入 buildTitle / ensureLocalTitle
anchor = 'export const renameSession = (id: string, title: string) => {'
assert anchor in store
BLOCK = '''/** 侧边栏标题上限（按字符数，中文一个字算一个） */
const TITLE_LIMIT = 13

/** 从首轮内容里提炼短标题：去代码块、去换行、去多余标点 */
const cleanForTitle = (text: string) =>
  text
    .replace(/```[\\s\\S]*?```/g, ' ')
    .replace(/`[^`]*`/g, ' ')
    .replace(/!?\\[[^\\]]*\\]\\([^)]*\\)/g, ' ')
    .replace(/^[#>*\\-\\s]+/gm, '')
    .replace(/\\s+/g, ' ')
    .trim()

export const buildTitle = (firstUserText: string): string => {
  const text = cleanForTitle(firstUserText)
  if (!text) {
    return ''
  }
  const head = text.split(/[。！？!?；;]/)[0] ?? text
  const source = head.length >= 4 ? head : text
  const chars = Array.from(source)
  if (chars.length <= TITLE_LIMIT) {
    return source.replace(/[，,、：:\\s]+$/, '')
  }
  return `${chars.slice(0, TITLE_LIMIT).join('').replace(/[，,、：:\\s]+$/, '')}…`
}

/**
 * 会话还没有标题时，用第一轮对话在本地生成一个（服务端 title 的兜底）。
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
  if (!session.messages.some((message) => message.role === 'assistant')) {
    return
  }
  const title = buildTitle(firstUser.content)
  if (!title) {
    return
  }
  updateSession(sessionId, (current) => (current.title ? current : { ...current, title }))
  persist(sessionId)
}

'''
store = store.replace(anchor, BLOCK + anchor, 1)
STORE.write_text(store, encoding='utf-8')
print('buildTitle/ensureLocalTitle added to store')

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 49', gradle), encoding='utf-8')
print('versionCode 49')
