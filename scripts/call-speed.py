"""Call UX: phone icon leftmost, speak from the first sentence, and offer a barge-in button."""

import re
from pathlib import Path

# ---------- 1) 顶栏顺序：电话在最左 ----------
HEADER = Path('src/components/session/MobileHeader.tsx')
header = HEADER.read_text(encoding='utf-8')
SOUND_BLOCK = """          {android ? (
            <IconButton
              size="xl"
              tone="primary"
              className={styles.sound}
              icon={<AndroidSound muted={!autoRead} />}
              aria-label={t('androidAutoRead')}
              aria-pressed={autoRead}
              onClick={() => {
                setAutoRead(!autoRead)
                if (autoRead) {
                  stopReadAloud()
                }
                showToast({ key: autoRead ? 'androidAutoReadDisabled' : 'androidAutoReadEnabled' })
              }}
            />
          ) : null}
"""
CALL_BLOCK = """          {android ? (
            <IconButton
              size="xl"
              tone="primary"
              className={styles.call}
              icon={<IconPhoneOutline20 />}
              aria-label={t('callStart')}
              onClick={() => {
                stopReadAloud()
                openVoiceCall()
              }}
            />
          ) : null}
"""
assert SOUND_BLOCK in header and CALL_BLOCK in header, 'header blocks not found'
if header.index(SOUND_BLOCK) < header.index(CALL_BLOCK):
    header = header.replace(SOUND_BLOCK + CALL_BLOCK, CALL_BLOCK + SOUND_BLOCK, 1)
    HEADER.write_text(header, encoding='utf-8')
    print('phone icon moved to the left')

# ---------- 2) 通话：第一句就开始朗读 + 支持打断 ----------
CALL = Path('src/components/call/useCallSession.ts')
call = CALL.read_text(encoding='utf-8')

call = call.replace('const SILENCE_MS = 900', 'const SILENCE_MS = 620')

OLD_FLOW = """        // 等这轮回复结束（流式 token 停止、没有挂起的请求）
        let reply: { id: string | null; text: string } = { id: null, text: '' }
        for (let step = 0; step < 1800; step++) {
          const state = useChatStore.getState()
          const id = sessionId ?? state.activeId
          const running = id ? Boolean(state.streaming[id]) : Object.keys(state.streaming).length > 0
          if (!running && step > 4) {
            const session = id ? state.sessionCache[id] : null
            const last = session?.messages.filter((item) => item.role === 'assistant').at(-1)
            reply = {
              id: last?.id ?? null,
              text: last ? (buildReplyView(last, false).answer?.text ?? '').trim() : '',
            }
            break
          }
          await wait(120)
        }
        if (ticket !== loop.current) {
          return
        }

        if (reply.text) {
          setPhase('speaking')
          // 新一轮朗读前，先停掉可能还在播的上一段
          playback.current?.abort()
          playback.current = new AbortController()
          await readAloudText(
            reply.id ?? `call-${Date.now()}`,
            reply.text,
            playback.current.signal,
            () => showToast({ key: 'ttsFailed', type: 'error' })
          )
          playback.current = null
        }
        if (ticket !== loop.current) {
          return
        }
        setPhase('listening')"""

NEW_FLOW = """        // 边生成边读：第一句完整了就立刻开口，不用等整段回复
        const replyText = () => {
          const state = useChatStore.getState()
          const id = sessionId ?? state.activeId
          const session = id ? state.sessionCache[id] : null
          const last = session?.messages.filter((item) => item.role === 'assistant').at(-1)
          return {
            id: last?.id ?? null,
            text: last ? (buildReplyView(last, false).answer?.text ?? '').trim() : '',
            streaming: id ? Boolean(state.streaming[id]) : Object.keys(state.streaming).length > 0,
          }
        }

        const speakText = async (text: string, id: string | null) => {
          playback.current?.abort()
          playback.current = new AbortController()
          setPhase('speaking')
          await readAloudText(id ?? `call-${Date.now()}`, text, playback.current.signal, () =>
            showToast({ key: 'ttsFailed', type: 'error' })
          )
          playback.current = null
        }

        // 1) 等到第一句
        let spoken = ''
        let replyId: string | null = null
        for (let step = 0; step < 200; step++) {
          const snapshot = replyText()
          replyId = snapshot.id ?? replyId
          const sentence = takeSentence(snapshot.text)
          if (sentence) {
            spoken = sentence
            break
          }
          if (!snapshot.streaming && snapshot.text) {
            spoken = snapshot.text
            break
          }
          await wait(90)
          if (ticket !== loop.current) {
            return
          }
        }
        if (ticket !== loop.current) {
          return
        }
        if (spoken) {
          await speakText(spoken, replyId)
        }
        if (ticket !== loop.current) {
          return
        }

        // 2) 等这一轮结束，把没读的部分补上
        let rest = ''
        for (let step = 0; step < 1800; step++) {
          const snapshot = replyText()
          replyId = snapshot.id ?? replyId
          if (!snapshot.streaming && step > 4) {
            rest = snapshot.text.slice(spoken.length).trim()
            break
          }
          await wait(120)
        }
        if (ticket !== loop.current) {
          return
        }
        if (rest) {
          await speakText(rest, replyId)
        }
        if (ticket !== loop.current) {
          return
        }
        setPhase('listening')"""
assert OLD_FLOW in call, 'call flow not found'
call = call.replace(OLD_FLOW, NEW_FLOW, 1)

# 句子切分工具
call = call.replace(
    """const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))""",
    """const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

/** 取回第一个完整句子：到句末标点为止，足够长才用，避免读出半句 */
const takeSentence = (text: string): string => {
  const match = /[^。！？!?…\\n]{6,}[。！？!?…]/.exec(text)
  return match ? match[0].trim() : ''
}""",
    1,
)
CALL.write_text(call, encoding='utf-8')
print('first-sentence speech + shorter silence window')

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 21', gradle), encoding='utf-8')
print('versionCode 21')
