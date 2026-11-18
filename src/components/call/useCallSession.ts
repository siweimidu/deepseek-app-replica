import { useCallback, useEffect, useRef, useState } from 'react'
import { transcribe } from '../../services/api/speech.js'
import { setDraftText } from '../../services/chat/drafts.js'
import { sendMessage, useChatStore } from '../../services/chat/store.js'
import { buildReplyView } from '../../services/chat/view.js'
import { readAloudText } from '../../services/speech/readAloud.js'
import { startRecording, type Recording } from '../../services/speech/recorder.js'
import { useSettings } from '../../services/settings.js'
import { showToast } from '../base/toastState.js'

export type CallPhase = 'listening' | 'thinking' | 'speaking' | 'muted'

/** 说完后安静这么久就算一轮结束 */
const SILENCE_MS = 620
/** 至少说了这么久才允许判定结束，避免一开口就掐断 */
const MIN_SPEECH_MS = 260
/** 音量阈值，与录音器的归一化电平对齐 */
const SPEECH_LEVEL = 0.045

const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))


/**
 * 通话主循环：录一轮（静音判停）→ 转写 → 发消息 → 等回复 → 朗读 → 继续录。
 * 用递增的 ticket 作废整轮，静音/挂断/离开页面时只需 +1 就能让所有 await 失效。
 */
export const useCallSession = (active: boolean) => {
  const [phase, setPhase] = useState<CallPhase>('listening')
  const [level, setLevel] = useState(0)
  const [seconds, setSeconds] = useState(0)
  const [round, setRound] = useState(0)
  const recording = useRef<Recording | null>(null)
  const playback = useRef<AbortController | null>(null)
  const loop = useRef(0)

  const stopAll = useCallback(() => {
    loop.current += 1
    recording.current?.cancel()
    recording.current = null
    playback.current?.abort()
    playback.current = null
    setLevel(0)
  }, [])

  useEffect(() => {
    if (!active) {
      return stopAll
    }
    const ticket = ++loop.current
    setPhase('listening')
    setSeconds(0)
    setLevel(0)

    /** 录到用户停止说话，返回这段音频 */
    const recordTurn = () =>
      new Promise<Blob | null>((resolve) => {
        void (async () => {
          let current: Recording
          try {
            current = await startRecording(() => undefined)
          } catch {
            showToast({ key: 'androidMicPermissionDenied', type: 'error' })
            setPhase('muted')
            resolve(null)
            return
          }
          if (ticket !== loop.current) {
            current.cancel()
            resolve(null)
            return
          }
          recording.current = current
          let spokeAt = 0
          let quietSince = 0
          const tick = () => {
            if (ticket !== loop.current || recording.current !== current) {
              resolve(null)
              return
            }
            const value = current.level?.() ?? 0
            setLevel(value)
            const now = Date.now()
            if (value > SPEECH_LEVEL) {
              spokeAt = now
              quietSince = 0
            } else if (spokeAt && now - spokeAt > 220 && !quietSince) {
              quietSince = now
            }
            if (
              quietSince &&
              now - quietSince > SILENCE_MS &&
              now - spokeAt > MIN_SPEECH_MS
            ) {
              recording.current = null
              setLevel(0)
              void current
                .stop()
                .then((audio) => audio)
                .catch(() => null)
                .then((audio) => {
                  current.cancel()
                  resolve(audio)
                })
              return
            }
            requestAnimationFrame(tick)
          }
          requestAnimationFrame(tick)
        })()
      })

    const run = async () => {
      while (ticket === loop.current) {
        const audio = await recordTurn()
        if (!audio || ticket !== loop.current) {
          return
        }
        let text = ''
        try {
          text = (await transcribe(useSettings.getState().apiKey ?? '', audio)).trim()
        } catch {
          showToast({ key: 'voiceInputFailed', type: 'error' })
        }
        if (ticket !== loop.current) {
          return
        }
        if (!text) {
          continue
        }

        const sessionId = useChatStore.getState().activeId
        setPhase('thinking')
        setDraftText(sessionId, text)
        if (!sendMessage(sessionId)) {
          setPhase('listening')
          continue
        }

        // 边生成边读：第一句完整了就立刻开口，不用等整段回复
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

        // 等这一轮回复生成完，整段一次性朗读：分句朗读会出现听到的和看到的对不上
        let spokenText = ''
        let replyId: string | null = null
        for (let step = 0; step < 1800; step++) {
          const snapshot = replyText()
          replyId = snapshot.id ?? replyId
          if (!snapshot.streaming && step > 4) {
            spokenText = snapshot.text
            break
          }
          await wait(120)
          if (ticket !== loop.current) {
            return
          }
        }
        if (ticket !== loop.current) {
          return
        }
        if (spokenText.trim()) {
          await speakText(spokenText, replyId)
        }
        if (ticket !== loop.current) {
          return
        }
        setPhase('listening')
      }
    }

    void run()
    return stopAll
  }, [active, round, stopAll])

  useEffect(() => {
    if (!active) {
      return
    }
    const started = Date.now()
    const timer = setInterval(() => setSeconds(Math.floor((Date.now() - started) / 1000)), 500)
    return () => clearInterval(timer)
  }, [active])

  const toggleMute = useCallback(() => {
    if (phase !== 'muted') {
      stopAll()
      setPhase('muted')
      return
    }
    setPhase('listening')
    // 换一个 round 让主循环重新起一轮
    setRound((value) => value + 1)
  }, [phase, stopAll])

  /** 打断当前朗读，立刻回到收音 */
  const interrupt = useCallback(() => {
    playback.current?.abort()
    playback.current = null
    setPhase('listening')
    setRound((value) => value + 1)
  }, [])

  return { phase, level, seconds, toggleMute, interrupt, endCall: stopAll }
}
