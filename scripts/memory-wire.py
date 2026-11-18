"""接入事实账本：类型字段 + 请求 system + 回复结束后补块。"""

import re
from pathlib import Path

# 1) 类型
TYPES = Path('src/services/chat/types.ts')
types = TYPES.read_text(encoding='utf-8')
if 'MemoryBlock' not in types:
    types = types.replace(
        """export type Session = {""",
        """/** 事实账本的一块：覆盖一段时间，写入后永不重写（保证前缀缓存） */
export type MemoryBlock = {
  /** 递增编号，从 1 开始 */
  index: number
  fromRound: number
  toRound: number
  text: string
  createdAt: number
}

export type Session = {""",
        1,
    )
    types = types.replace(
        """  /** 开头存档，编译一次后冻结，保证长对话仍记得最初内容 */
  anchor?: SessionAnchor""",
        """  /** 开头存档，编译一次后冻结，保证长对话仍记得最初内容 */
  anchor?: SessionAnchor
  /** 事实账本：只追加，覆盖中段对话，裁剪也不会丢 */
  memory?: MemoryBlock[]""",
        1,
    )
    TYPES.write_text(types, encoding='utf-8')
print('types updated:', 'MemoryBlock' in types)

# 2) store：请求 system 拼上账本；回复结束后补块
STORE = Path('src/services/chat/store.ts')
store = STORE.read_text(encoding='utf-8')

if 'withMemory' not in store:
    store = store.replace(
        "import { ensureAnchor, withAnchor } from './context/anchor.js'",
        "import { ensureAnchor, withAnchor } from './context/anchor.js'\nimport { ensureMemoryBlock, withMemory } from './context/memory.js'",
        1,
    )
    store = store.replace(
        "            system: withAnchor(SYSTEM_PROMPT, getSession(sessionId)?.anchor?.text),",
        "            system: withMemory(\n"
        "              withAnchor(SYSTEM_PROMPT, getSession(sessionId)?.anchor?.text),\n"
        "              getSession(sessionId)?.memory\n"
        "            ),",
        1,
    )
    # 回复结束后补一块（和标题兜底同一处）
    store = store.replace(
        """    // 有些流不发 stop_reason，收尾时再兜底一次
    ensureLocalTitle(sessionId)""",
        """    // 有些流不发 stop_reason，收尾时再兜底一次
    ensureLocalTitle(sessionId)
    // 每满 20 轮补一块事实账本（只追加，不重写旧块）
    void ensureMemoryBlock(sessionId, getSession, get().sessionCache[sessionId]?.messages.length
      ? (get().sessionCache[sessionId]?.messages.length ? (initial.model ?? MODEL) : (initial.model ?? MODEL))
      : (initial.model ?? MODEL)).then((next) => {
      if (next) {
        updateSession(sessionId, () => next)
        persist(sessionId)
      }
    })""",
        1,
    )
STORE.write_text(store, encoding='utf-8')
print('store wired:', 'withMemory' in store and 'ensureMemoryBlock' in store)
