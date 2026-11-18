import { streamMessage } from '../../api/client.js'
import { useSettings } from '../../settings.js'
import type { ChatModel, MessageParam } from '../../api/types.js'
import type { Session } from '../types.js'
import { getContextRounds } from '../reply.js'
import { buildReplyView } from '../view.js'

/**
 * 会话锚点卡
 *
 * 会话进行到几轮之后，把「开头到底在聊什么、用户明确要求了什么」编译成一页短卡片，
 * 之后每轮原样拼在 system 末尾。它永远处在请求最前面，所以无论后来压缩多少次，
 * 最初的内容始终在场；同时因为它编译一次就冻结，也不会破坏前缀缓存。
 */

const ANCHOR_MIN_ROUNDS = 3
const ANCHOR_MAX_TOKENS = 700
const ANCHOR_TIMEOUT_MS = 30_000

export const ANCHOR_PROMPT = `你在为一通很长的对话生成"开头存档"。
读取下面这段对话的开头部分，输出一页不超过 350 字的中文卡片，只写以下四类内容：
1) 用户是谁、想达成什么
2) 用户明确提出过的要求、限制、偏好（原话要点，不要改写意思）
3) 已经确定的关键结论或数据
4) 尚未完成的事项
不要写寒暄、不要写过程、不要评价。直接输出卡片正文，不要标题、不要前言。`

/** 卡片正文直接拼到 system 后，保证每轮前缀逐字一致 */
export const withAnchor = (system: string, anchor?: string) =>
  anchor ? `${system}\n\n<session_anchor>\n${anchor}\n</session_anchor>` : system

const collectQuestion = (session: Session, model: ChatModel, signal: AbortSignal) =>
  new Promise<string>((resolve, reject) => {
    const rounds = getContextRounds(session.messages).slice(0, 6)
    const messages: MessageParam[] = []
    for (const [user, reply] of rounds) {
      if (!user.content) {
        continue
      }
      messages.push({ role: 'user', content: [{ type: 'text', text: user.content }] })
      let answer = ''
      try {
        answer = (buildReplyView(reply, false).answer?.text ?? '').slice(0, 1_200)
      } catch {
        answer = ''
      }
      if (answer) {
        messages.push({ role: 'assistant', content: [{ type: 'text', text: answer }] })
      }
    }
    let text = ''
    void (async () => {
      try {
        for await (const event of streamMessage(
          useSettings.getState().apiKey ?? '',
          {
            model,
            system: ANCHOR_PROMPT,
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
        }
        resolve(text.trim())
      } catch (error) {
        reject(error)
      }
    })()
  })

/**
 * 需要时生成锚点卡；已存在或轮数不足则直接跳过。
 * 失败静默（下次再来），不打断正常对话。
 */
export const ensureAnchor = async (session: Session, model: ChatModel): Promise<Session | null> => {
  if (session.anchor?.text) {
    return null
  }
  const rounds = getContextRounds(session.messages)
  if (rounds.length < ANCHOR_MIN_ROUNDS) {
    return null
  }
  const controller = new AbortController()
  const timer = window.setTimeout(() => controller.abort(), ANCHOR_TIMEOUT_MS)
  try {
    const text = await collectQuestion(session, model, controller.signal)
    if (!text) {
      return null
    }
    const trimmed = text.slice(0, ANCHOR_MAX_TOKENS * 2)
    return {
      ...session,
      anchor: {
        text: trimmed,
        upTo: rounds[ANCHOR_MIN_ROUNDS - 1][1].id,
        createdAt: Date.now(),
      },
    }
  } catch {
    return null
  } finally {
    window.clearTimeout(timer)
  }
}
