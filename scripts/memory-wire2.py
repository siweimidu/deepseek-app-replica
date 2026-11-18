"""接入事实账本（干净版）：类型字段 + 请求 system + 回复结束后补块。"""

import re
from pathlib import Path

# 1) 类型
TYPES = Path('src/services/chat/types.ts')
types = TYPES.read_text(encoding='utf-8')
if 'MemoryBlock' not in types:
    types = types.replace(
        "export type Session = {",
        """/** 事实账本的一块：覆盖一段轮次，写入后永不重写（保证前缀缓存） */
export type MemoryBlock = {
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

# 2) store
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
    store = store.replace(
        """    // 有些流不发 stop_reason，收尾时再兜底一次
    ensureLocalTitle(sessionId)""",
        """    // 有些流不发 stop_reason，收尾时再兜底一次
    ensureLocalTitle(sessionId)
    // 每满 20 轮补一块事实账本（只追加，旧块绝不重写）
    void ensureMemoryBlock(sessionId, getSession, initial.model ?? MODEL).then((next) => {
      if (next) {
        updateSession(sessionId, () => next)
        persist(sessionId)
      }
    })""",
        1,
    )
STORE.write_text(store, encoding='utf-8')
print('store wired:', 'withMemory' in store and 'ensureMemoryBlock' in store)
