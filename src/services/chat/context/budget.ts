import type { ChatModel } from '../../api/types.js'
import type { AssistantMessage, Message, UserMessage } from '../types.js'
import { getContextRounds } from '../reply.js'
import { buildReplyView } from '../view.js'

/**
 * 上下文预算
 *
 * 目标不是"塞更多"，而是让每轮请求的 token 数稳定：前缀越稳，命中服务端前缀缓存的比例越高。
 * 因此这里只在「超出触发线」时才裁剪，而且一次裁到目标线以下，
 * 中间几十轮都不再动 —— 裁剪点之间前缀完全一致。
 */

/** 各模型的窗口大小（token） */
export const MODEL_WINDOWS: Record<ChatModel, number> = {
  // V4.1 Flash-1017：100 万上下文
  'deepseek-flash': 1_000_000,
  // V4.1 Pro 的窗口尚未核对，先保守按 128K
  'deepseek-v4-pro': 128_000,
}

/** 界面上展示用的模型名 */
export const MODEL_LABELS: Record<ChatModel, string> = {
  'deepseek-flash': 'DeepSeek V4.1Flash-1017',
  'deepseek-v4-pro': 'DeepSeek V4.1Pro-1017',
}

/** 给输出留的余量 */
export const OUTPUT_RESERVE = 8_000
/** 超过「窗口 - 预留」的这个比例就触发一次压缩 */
export const TRIGGER_RATIO = 0.75
/** 压缩后落到这个比例，留出尽量长的追加空间以减少压缩次数 */
export const TARGET_RATIO = 0.36

/** 粗略估算 token：中日韩字符约 1 字 1 token，拉丁文约 4 字符 1 token。 */
export const estimateTokens = (text: string): number => {
  if (!text) {
    return 0
  }
  let wide = 0
  let narrow = 0
  for (const char of text) {
    const code = char.codePointAt(0) ?? 0
    if (code > 0x2e7f) {
      wide += 1
    } else {
      narrow += 1
    }
  }
  return Math.ceil(wide + narrow / 3.6)
}

/** 附件按固定预算估算，避免为一两个图片反复解析 */
const FILE_TOKENS = 900

const userTokens = (message: UserMessage) =>
  estimateTokens(message.content) + (message.files?.length ?? 0) * FILE_TOKENS

const replyTokens = (message: AssistantMessage) => {
  try {
    return estimateTokens(buildReplyView(message, false).answer?.text ?? '')
  } catch {
    return 0
  }
}

export type BudgetPlan = {
  /** 实际要发的历史（可能被裁剪） */
  history: Message[]
  /** 估算的输入 token */
  estimate: number
  /** 本轮是否发生压缩 */
  compacted: boolean
  /** 被裁掉的轮数 */
  droppedRounds: number
  /** 触发线 / 目标线，供 UI 展示 */
  trigger: number
  target: number
}

export const planContext = (
  history: Message[],
  model: ChatModel,
  lastInputTokens?: number
): BudgetPlan => {
  const window = MODEL_WINDOWS[model] ?? 128_000
  const usable = window - OUTPUT_RESERVE
  const trigger = Math.floor(usable * TRIGGER_RATIO)
  const target = Math.floor(usable * TARGET_RATIO)

  // 上一轮的真实输入 token 是最可信的基线：本轮多出来的只有新的一问一答
  const rounds = getContextRounds(history)
  const measured = lastInputTokens ?? 0
  const estimate =
    measured > 0
      ? measured + rounds.slice(-1).reduce((sum, [user, reply]) => sum + userTokens(user) + replyTokens(reply), 0)
      : rounds.reduce((sum, [user, reply]) => sum + userTokens(user) + replyTokens(reply), 0)

  if (estimate <= trigger || rounds.length <= 2) {
    return { history, estimate, compacted: false, droppedRounds: 0, trigger, target }
  }

  // 压缩：保留首轮（意图锚点）+ 从尾部往回收，直到落到目标线以内
  const keep: Message[] = []
  let total = 0
  const [firstRound] = rounds
  const firstTokens = userTokens(firstRound[0]) + replyTokens(firstRound[1])
  keep.push(firstRound[0], firstRound[1])
  total += firstTokens

  for (let index = rounds.length - 1; index >= 1; index -= 1) {
    const [user, reply] = rounds[index]
    const cost = userTokens(user) + replyTokens(reply)
    if (total + cost > target) {
      break
    }
    keep.splice(2, 0, user, reply)
    total += cost
  }

  return {
    history: keep,
    estimate: total,
    compacted: true,
    droppedRounds: rounds.length - keep.length / 2,
    trigger,
    target,
  }
}
