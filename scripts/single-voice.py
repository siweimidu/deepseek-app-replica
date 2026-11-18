"""Only ever one TTS audio graph alive: abort and close the previous context before speaking."""

from pathlib import Path

READ = Path('src/services/speech/readAloud.ts')
text = READ.read_text(encoding='utf-8')

OLD_HEAD = """const speak = async (
  messageId: string,
  text: string,
  controller: AbortController,
  context: AudioContext,
  onError: (error: unknown) => void
): Promise<void> => {
  current = { controller, context }"""
NEW_HEAD = """const speak = async (
  messageId: string,
  text: string,
  controller: AbortController,
  context: AudioContext,
  onError: (error: unknown) => void
): Promise<void> => {
  // 上一段朗读如果还在播，必须先掐断并关掉它的 AudioContext：
  // 只 abort 不 close 的话，已经排程的 buffer 会继续出声，听起来像几个人同时说话。
  const previous = current
  if (previous && previous.controller !== controller) {
    previous.controller.abort()
    void previous.context.close().catch(() => undefined)
  }
  current = { controller, context }"""
assert OLD_HEAD in text, 'speak head not found'
text = text.replace(OLD_HEAD, NEW_HEAD, 1)

OLD_FINALLY = """  } finally {
    finish(controller)
  }
}"""
NEW_FINALLY = """  } finally {
    finish(controller)
    // finish 只处理 current 指向自己的情况；无论如何都要把自己的 context 关掉
    if (context.state !== 'closed') {
      void context.close().catch(() => undefined)
    }
  }
}"""
assert OLD_FINALLY in text, 'finally not found'
text = text.replace(OLD_FINALLY, NEW_FINALLY, 1)

READ.write_text(text, encoding='utf-8')
print('single-voice guard added')

# 通话循环：同一时刻只允许一轮朗读
CALL = Path('src/components/call/useCallSession.ts')
call = CALL.read_text(encoding='utf-8')
OLD = """        if (reply.text) {
          setPhase('speaking')
          playback.current = new AbortController()"""
NEW = """        if (reply.text) {
          setPhase('speaking')
          // 新一轮朗读前，先停掉可能还在播的上一段
          playback.current?.abort()
          playback.current = new AbortController()"""
assert OLD in call, 'call speaking block not found'
CALL.write_text(call.replace(OLD, NEW, 1), encoding='utf-8')
print('call loop aborts previous playback')
