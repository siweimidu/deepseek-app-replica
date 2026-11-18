import { useSettings } from '../../settings.js'
import type { ChatModel, MessageParam } from '../../api/types.js'
import { streamMessage } from '../../api/client.js'
import { buildReplyView } from '../view.js'
import { getContextRounds } from '../reply.js'
import type { MemoryBlock, Session } from '../types.js'

/**
 * 事实账本（append-only memory log）
 *
 * 为什么这样设计：
 * 1. 只追加：每块覆盖一段轮次，写入后永不重写 → 请求前缀逐字节稳定，缓存照命。
 * 2. 有结构：事实/决定/偏好/待办，比原始对话更抗噪，压缩损失可控。
 * 3. 与锚点卡分工：锚点卡保「开头要求」，账本保「中段走过的路」；
 *    两者都在 system 里，任何裁剪都碰不到它们。
 * 4. 原文永不删：账本只是给模型看的极简摘要，本地全文仍可用搜索翻回。
 */

/** 每块覆盖多少轮 */
export const MEMORY_BLOCK_ROUNDS = 20
/** 单块字数上限 */
const BLOCK_MAX_CHARS = 620
const BLOCK_TIMEOUT_MS = 30_000

export const MEMORY_PROMPT = `你在为一段很长的对话整理"事实账本"，供之后的对话回顾使用。

只输出四行，不要标题、不要解释、不要代码块：
事实：<这段对话里确定下来的、可复述的客观信息>
决定：<已经做出的决定或结论>
偏好：<用户表达过的偏好、禁忌、风格要求>
待办：<尚未完成或需要继续跟进的事>

要求：
- 每行不超过 40 个字；没有内容就写「无」。
- 只写对话里确实出现过的内容，不要推测、不要编造。
- 用陈述句，不要出现"用户问""AI 答"这类描述。`

/** 账本拼进 system：只按顺序排列，块内文字不会再变 */
export const withMemory = (system: string, blocks?: MemoryBlock[]) => {
  if (!blocks?.length) {
    return system
  }
  const body = blocks.map((block) => `#${block.index}（第 ${block.fromRound}-${block.toRound} 轮）\n${block.text}`).join('\n\n')
  return `${system}\n\n<memory_log>\n${body}\n</memory_log>`
}

/** 已被账本覆盖到的轮次数（账本是连续的，取最后一块的 toRound） */
const coveredRounds = (session: Session) => session.memory?.[session.memory.length - 1]?.toRound ?? 0

const collectRange = (
  session: Session,
  fromRound: number,
  toRound: number,
  model: ChatModel,
  signal: AbortSignal
) =>
  new Promise<string>((resolve, reject) => {
    const rounds = getContextRounds(session.messages).slice(fromRound, toRound)
    const messages: MessageParam[] = []
    for (const [user, reply] of rounds) {
      if (user.content) {
        messages.push({ role: 'user', content: [{ type: 'text', text: user.content.slice(0, 1_500) }] })
      }
      let answer = ''
      try {
        answer = (buildReplyView(reply, false).answer?.text ?? '').slice(0, 1_500)
      } catch {
        answer = ''
      }
      if (answer) {
        messages.push({ role: 'assistant', content: [{ type: 'text', text: answer }] })
      }
    }
    if (!messages.length) {
      resolve('')
      return
    }
    let text = ''
    void (async () => {
      try {
        for await (const event of streamMessage(
          useSettings.getState().apiKey ?? '',
          {
            model,
            system: MEMORY_PROMPT,
            messages,
            thinking: { type: 'disabled' },
            safety_check: { level: 'high' },
            tools: [],
          } as never,
          signal
        )) {
          if (event.type === 'content_block_delta' && 'delta' in event) {
            const delta = event.delta as { type?: string; text?: string }
            if (delta.type === 'text_delta' && delta.text) {
              text += delta.text
            }
          }
          if (event.type === 'message_stop') {
            break
          }
        }
        resolve(text.trim())
      } catch (error) {
        reject(error)
      }
    })()
  })

/** 同一会话同时只跑一个生成，避免并发重复追加 */
const running = new Set<string>()

/**
 * 补一块账本：如果还有未覆盖的轮次达到一块的规模，就为最早的那一段生成。
 * 返回更新后的 session（未变化时返回 null）。
 */
export const ensureMemoryBlock = async (
  sessionId: string,
  getSession: (id: string) => Session | undefined,
  model: ChatModel
): Promise<Session | null> => {
  const session = getSession(sessionId)
  if (!session || running.has(sessionId)) {
    return null
  }
  const rounds = getContextRounds(session.messages).length
  const covered = coveredRounds(session)
  if (rounds - covered < MEMORY_BLOCK_ROUNDS) {
    return null
  }
  const fromRound = covered
  const toRound = covered + MEMORY_BLOCK_ROUNDS
  running.add(sessionId)
  const controller = new AbortController()
  const timer = window.setTimeout(() => controller.abort(), BLOCK_TIMEOUT_MS)
  try {
    const text = await collectRange(session, fromRound, toRound, model, controller.signal)
    if (!text) {
      return null
    }
    const latest = getSession(sessionId)
    if (!latest) {
      return null
    }
    const blocks = latest.memory ?? []
    // 只追加：编号按现有块数递增，旧块一个字都不动
    const block: MemoryBlock = {
      index: blocks.length + 1,
      fromRound,
      toRound,
      text: text.slice(0, BLOCK_MAX_CHARS),
      createdAt: Date.now(),
    }
    return { ...latest, memory: [...blocks, block] }
  } catch {
    return null
  } finally {
    window.clearTimeout(timer)
    running.delete(sessionId)
  }
}
