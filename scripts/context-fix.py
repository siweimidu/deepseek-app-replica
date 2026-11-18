import re
from pathlib import Path

# ---------- anchor.ts：助手正文统一走回复视图 ----------
ANCHOR = Path('src/services/chat/context/anchor.ts')
anchor = ANCHOR.read_text(encoding='utf-8')
anchor = anchor.replace(
    "import { getContextRounds } from '../reply.js'",
    "import { getContextRounds } from '../reply.js'\nimport { buildReplyView } from '../view.js'",
    1,
)
anchor = anchor.replace(
    """      const answer = reply.segments
        ?.map((segment) => ('text' in segment ? segment.text : ''))
        .join('')
        .slice(0, 1_200)""",
    """      let answer = ''
      try {
        answer = (buildReplyView(reply, false).answer?.text ?? '').slice(0, 1_200)
      } catch {
        answer = ''
      }""",
    1,
)
ANCHOR.write_text(anchor, encoding='utf-8')
print('anchor uses reply view')

# ---------- store.ts ----------
STORE = Path('src/services/chat/store.ts')
store = STORE.read_text(encoding='utf-8')

# 类型导入
store = store.replace("} from './types.js'", "  type ContextUsage,\n} from './types.js'", 1)
store = store.replace(
    "  let usage: import('./types.js').ContextUsage | null = null",
    "  let usage: ContextUsage | null = null",
    1,
)

# 去掉未使用的 contextPlans
store = store.replace("        if (plan.compacted) {\n          contextPlans.set(sessionId, plan)\n        }\n", "", 1)

# usage 采集改成先取局部变量，避免类型收窄问题
store = store.replace(
    """          if (event.type === 'message_start' && event.message.usage) {
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
          }""",
    """          if (event.type === 'message_start') {
            const reported = event.message.usage
            if (reported) {
              usage = {
                inputTokens: reported.input_tokens,
                outputTokens: 0,
                cacheReadTokens: reported.cache_read_input_tokens,
                cacheWriteTokens: reported.cache_creation_input_tokens,
                updatedAt: Date.now(),
              }
            }
          } else if (event.type === 'message_delta') {
            const reported = event.usage
            if (reported) {
              const previous = usage
              usage = {
                inputTokens: reported.input_tokens || previous?.inputTokens || 0,
                outputTokens: reported.output_tokens,
                cacheReadTokens: reported.cache_read_input_tokens || previous?.cacheReadTokens || 0,
                cacheWriteTokens:
                  reported.cache_creation_input_tokens || previous?.cacheWriteTokens || 0,
                updatedAt: Date.now(),
              }
            }
          }""",
    1,
)

# 成功收尾：落 usage + 需要时生成锚点卡
store = store.replace(
    """        if (usage) {
          const measured = usage
          updateSession(sessionId, (session) => ({ ...session, contextUsage: measured }))
          persist(sessionId)
        }
        break""",
    """        if (usage) {
          const measured = usage
          updateSession(sessionId, (session) => ({ ...session, contextUsage: measured }))
          persist(sessionId)
        }
        // 开头存档：攒够几轮后生成一次，之后冻结
        {
          const current = getSession(sessionId)
          if (current && !current.anchor) {
            void ensureAnchor(current, initial.model ?? MODEL)
              .then((next) => {
                if (next) {
                  updateSession(sessionId, () => next)
                  persist(sessionId)
                }
              })
              .catch(() => undefined)
          }
        }
        break""",
    1,
)

STORE.write_text(store, encoding='utf-8')
print('store usage capture fixed')
