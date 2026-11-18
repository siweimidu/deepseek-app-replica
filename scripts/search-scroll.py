"""点击搜索结果后，聊天区精确滚到命中的那条消息并短暂高亮。"""

import json
import re
from pathlib import Path

# ---------- 1) 目标消息的全局状态 ----------
STATE = Path('src/services/chat/scrollTarget.ts')
STATE.write_text("""import { create } from 'zustand'

/** 需要滚动定位到的消息（由搜索点击设置，消息列表消费） */
type Target = { sessionId: string; messageId: string } | null

export const useScrollTarget = create<{ target: Target }>(() => ({ target: null }))

export const requestScrollToMessage = (sessionId: string, messageId: string) =>
  useScrollTarget.setState({ target: { sessionId, messageId } })

export const clearScrollTarget = () => useScrollTarget.setState({ target: null })
""", encoding='utf-8')
print('scroll target store created')

# ---------- 2) 消息根节点加 data-message-id 锚点 ----------
USER = Path('src/components/messages/UserMessage.tsx')
user = USER.read_text(encoding='utf-8')
user = user.replace(
    "    <div className={clsx(styles.container, isFirst && styles.isFirst)}>",
    "    <div className={clsx(styles.container, isFirst && styles.isFirst)} data-message-id={message.id}>",
    1,
)
USER.write_text(user, encoding='utf-8')

ASSISTANT = Path('src/components/messages/AssistantMessage.tsx')
assistant = ASSISTANT.read_text(encoding='utf-8')
assistant = assistant.replace(
    "    <div className={styles.message}>",
    "    <div className={styles.message} data-message-id={message.id}>",
    1,
)
ASSISTANT.write_text(assistant, encoding='utf-8')
print('message anchors added')

# ---------- 3) 搜索结果携带 messageId ----------
PAGE = Path('src/components/search/SessionSearchPage.tsx')
page = PAGE.read_text(encoding='utf-8')

page = page.replace(
    """  /** 真正要跳转的会话 id */
  sessionId: string""",
    """  /** 真正要跳转的会话 id */
  sessionId: string
  /** 命中的消息 id（用于滚动定位） */
  messageId: string""",
    1,
)

# 缓存改为 [{id,text}]，才能带回 messageId
page = page.replace(
    "  const textCache = useRef(new Map<string, string>())",
    "  const textCache = useRef(new Map<string, { id: string; text: string }[]>())",
    1,
)

old_scan = page[page.index('          const cached = textCache.current.get(summary.id)'):page.index('        setHits([...found])')]
new_scan = """          const cached = textCache.current.get(summary.id)
          const rows =
            cached ??
            (session?.messages ?? []).map((message) => ({
              id: message.id,
              text: messageText(message),
            }))
          if (!cached && session) {
            textCache.current.set(summary.id, rows)
          }
          const titleHit = summary.title.toLocaleLowerCase().includes(term)
          for (const [index, row] of rows.entries()) {
            const at = row.text.toLocaleLowerCase().indexOf(term)
            if (at < 0) {
              continue
            }
            const snippet = `${at > 14 ? '…' : ''}${row.text.slice(Math.max(0, at - 14), at + SNIPPET_LIMIT)}`
            found.push({
              id: `${summary.id}-${index}`,
              sessionId: summary.id,
              messageId: row.id,
              title: summary.title,
              snippet: snippet.replace(/\\s+/g, ' ').trim(),
              updatedAt: summary.updatedAt,
            })
          }
          if (!rows.some((row) => row.text.toLocaleLowerCase().includes(term)) && titleHit) {
            found.push({
              id: `${summary.id}-title`,
              sessionId: summary.id,
              messageId: '',
              title: summary.title,
              snippet: summary.title,
              updatedAt: summary.updatedAt,
            })
          }
        }
"""
page = page.replace(old_scan, new_scan, 1)

page = page.replace(
    """  const pick = (hit: Hit) => {
    // 用真实会话 id 跳转；id 是列表 key（会话 id + 消息序号），不能直接当会话 id
    void selectSession(hit.sessionId)
    closeSessionSearch()
  }""",
    """  const pick = (hit: Hit) => {
    // 用真实会话 id 跳转；id 是列表 key（会话 id + 消息序号），不能直接当会话 id
    void selectSession(hit.sessionId)
    if (hit.messageId) {
      requestScrollToMessage(hit.sessionId, hit.messageId)
    }
    closeSessionSearch()
  }""",
    1,
)
page = page.replace(
    "import { selectSession, useChatStore } from '../../services/chat/store.js'",
    "import { selectSession, useChatStore } from '../../services/chat/store.js'\nimport { requestScrollToMessage } from '../../services/chat/scrollTarget.js'",
    1,
)
PAGE.write_text(page, encoding='utf-8')
print('search hits carry messageId')

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 48', gradle), encoding='utf-8')
print('versionCode 48')
