"""Fix the delete hang (no timeout on waitForIdle) and drop the modal backdrop blur."""

from pathlib import Path

STORE = Path('src/services/chat/store.ts')
store = STORE.read_text(encoding='utf-8')
OLD = """const waitForIdle = (sessionId?: string) =>
  new Promise<void>((resolve) => {
    const isIdle = (state: ChatState) =>
      sessionId === undefined
        ? Object.keys(state.streaming).length === 0
        : !Object.hasOwn(state.streaming, sessionId)
    if (isIdle(get())) {
      resolve()
      return
    }
    const unsubscribe = useChatStore.subscribe((state) => {
      if (isIdle(state)) {
        unsubscribe()
        resolve()
      }
    })
  })"""
NEW = """const waitForIdle = (sessionId?: string) =>
  new Promise<void>((resolve) => {
    const isIdle = (state: ChatState) =>
      sessionId === undefined
        ? Object.keys(state.streaming).length === 0
        : !Object.hasOwn(state.streaming, sessionId)
    if (isIdle(get())) {
      resolve()
      return
    }
    let settled = false
    const finish = () => {
      if (settled) {
        return
      }
      settled = true
      unsubscribe()
      window.clearTimeout(timer)
      resolve()
    }
    // 收尾可能因为异常一直不回来；这里必须兜底，否则删除会永远挂住
    const timer = window.setTimeout(finish, 2500)
    const unsubscribe = useChatStore.subscribe((state) => {
      if (isIdle(state)) {
        finish()
      }
    })
  })"""
assert OLD in store, 'waitForIdle not found'
STORE.write_text(store.replace(OLD, NEW, 1), encoding='utf-8')
print('waitForIdle now has a timeout')

MODAL = Path('src/components/base/Modal.module.css')
modal = MODAL.read_text(encoding='utf-8')
modal = modal.replace(
    "  backdrop-filter: blur(2px);\n",
    "  /* 弹层不做实时背景模糊：Android WebView 上每帧回读，删除这类操作会像卡死 */\n",
)
MODAL.write_text(modal, encoding='utf-8')
print('modal blur removed:', 'backdrop-filter' not in modal)
