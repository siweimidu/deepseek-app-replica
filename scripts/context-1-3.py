import re
from pathlib import Path

# ---------- 1) 类型：usage 与锚点卡写到 Session 上 ----------
TYPES = Path('src/services/chat/types.ts')
types = TYPES.read_text(encoding='utf-8')
if 'ContextUsage' not in types:
    types = types.replace(
        """export type Session = {
  id: string
  title: string
  createdAt: number
  updatedAt: number
  /** 包含所有分支的消息，按创建顺序存储。 */
  messages: Message[]
  /** undefined 表示线性消息列表；null 表示空会话。 */
  rootMessageId?: string | null
}""",
        """/** 上一轮的真实用量，用来预测本轮输入规模，比字数估算准得多 */
export type ContextUsage = {
  inputTokens: number
  outputTokens: number
  cacheReadTokens: number
  cacheWriteTokens: number
  updatedAt: number
}

/** 会话锚点卡：把开头内容编译成一页，之后每轮原样放在请求最前面 */
export type SessionAnchor = {
  text: string
  upTo: string
  createdAt: number
}

export type Session = {
  id: string
  title: string
  createdAt: number
  updatedAt: number
  /** 包含所有分支的消息，按创建顺序存储。 */
  messages: Message[]
  /** undefined 表示线性消息列表；null 表示空会话。 */
  rootMessageId?: string | null
  /** 上一轮的 token 用量（含缓存命中情况） */
  contextUsage?: ContextUsage
  /** 开头存档，编译一次后冻结，保证长对话仍记得最初内容 */
  anchor?: SessionAnchor
}""",
        1,
    )
    TYPES.write_text(types, encoding='utf-8')
    print('types extended')

# ---------- 2) store：计量 + 预算窗口 + 锚点卡 ----------
STORE = Path('src/services/chat/store.ts')
store = STORE.read_text(encoding='utf-8')

if 'planContext' not in store:
    store = store.replace(
        "import { useSettings } from '../settings.js'",
        "import { useSettings } from '../settings.js'\nimport { planContext } from './context/budget.js'\nimport { ensureAnchor, withAnchor } from './context/anchor.js'",
        1,
    )

    # 2a. 请求拼装：按预算裁剪 + 拼锚点卡
    store = store.replace(
        """        const messages = toRequestMessages(
          prepared.history,
          prepared.question,
          prepared.prefix,
          initial.thinking ?? false,
          latestReminder
        )""",
        """        // 按预算组窗口：未超触发线时原样发送，前缀保持不变以命中缓存
        const plan = planContext(
          prepared.history,
          initial.model ?? MODEL,
          getSession(sessionId)?.contextUsage?.inputTokens
        )
        if (plan.compacted) {
          contextPlans.set(sessionId, plan)
        }
        const messages = toRequestMessages(
          plan.history,
          prepared.question,
          prepared.prefix,
          initial.thinking ?? false,
          latestReminder
        )""",
        1,
    )
    store = store.replace(
        "            system: SYSTEM_PROMPT,",
        "            system: withAnchor(SYSTEM_PROMPT, getSession(sessionId)?.anchor?.text),",
        1,
    )

    # 2b. 采集 usage
    store = store.replace(
        """        for await (const event of events) {
          receivedContent ||= event.type === 'content_block_start'""",
        """        for await (const event of events) {
          // 真实用量：message_start 带输入（含缓存命中），message_delta 带累计输出
          if (event.type === 'message_start' && event.message.usage) {
            usage = {
              inputTokens: event.message.usage.input_tokens,
              outputTokens: 0,
              cacheReadTokens: event.message.usage.cache_read_input_tokens,
              cacheWriteTokens: event.message.usage.cache_creation_input_tokens,
              updatedAt: Date.now(),
            }
          } else if (event.type === 'message_delta' && event.usage) {
            usage = {
              inputTokens: event.usage.input_tokens || usage?.inputTokens || 0,
              outputTokens: event.usage.output_tokens,
              cacheReadTokens: event.usage.cache_read_input_tokens || usage?.cacheReadTokens || 0,
              cacheWriteTokens:
                event.usage.cache_creation_input_tokens || usage?.cacheWriteTokens || 0,
              updatedAt: Date.now(),
            }
          }
          receivedContent ||= event.type === 'content_block_start'""",
        1,
    )

    store = store.replace(
        """        reply = settleReply(reply, 'done', Date.now())
        break""",
        """        reply = settleReply(reply, 'done', Date.now())
        if (usage) {
          const measured = usage
          updateSession(sessionId, (session) => ({ ...session, contextUsage: measured }))
          persist(sessionId)
        }
        break""",
        1,
    )

    # 2c. 声明局部变量 usage
    store = store.replace(
        """  let reply = initial
  let frame = 0""",
        """  let reply = initial
  let frame = 0
  let usage: import('./types.js').ContextUsage | null = null""",
        1,
    )

    STORE.write_text(store, encoding='utf-8')
    print('store wired')

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 36', gradle), encoding='utf-8')
print('versionCode 36')
