"""导入完成后在底部弹提示：成功多少条、失败多少条，几秒后自动消失。"""

import re
from pathlib import Path

# ---------- 1) toast 支持「底部 + 自定义时长」 ----------
STATE = Path('src/components/base/toastState.ts')
state = STATE.read_text(encoding='utf-8')
state = state.replace(
    "type ToastState = { id: number; message: LinkedMessage | string | null }\n\nexport const useToast = create<ToastState>(() => ({ id: 0, message: null }))",
    """type ToastPlace = 'top' | 'bottom'

type ToastState = {
  id: number
  message: LinkedMessage | string | null
  place: ToastPlace
}

export const useToast = create<ToastState>(() => ({ id: 0, message: null, place: 'top' }))""",
    1,
)
state = state.replace(
    """export const showToast = (message: LinkedMessage | string) => {
  window.clearTimeout(timer)
  useToast.setState((state) => ({ id: state.id + 1, message }))
  const duration = typeof message !== 'string' && message.link ? LINK_DURATION : DURATION
  timer = window.setTimeout(() => useToast.setState({ message: null }), duration)
}""",
    """export const showToast = (
  message: LinkedMessage | string,
  options?: { duration?: number; place?: ToastPlace }
) => {
  window.clearTimeout(timer)
  useToast.setState((current) => ({
    id: current.id + 1,
    message,
    place: options?.place ?? 'top',
  }))
  const duration =
    options?.duration ?? (typeof message !== 'string' && message.link ? LINK_DURATION : DURATION)
  timer = window.setTimeout(() => useToast.setState({ message: null }), duration)
}""",
    1,
)
STATE.write_text(state, encoding='utf-8')
print('toast: place + duration')

# ---------- 2) Toast 组件读 place ----------
TOAST = Path('src/components/base/Toast.tsx')
toast = TOAST.read_text(encoding='utf-8')
toast = toast.replace(
    "  const { id, message } = useToast()",
    "  const { id, message, place } = useToast()\n  const bottom = place === 'bottom'",
)
toast = toast.replace(
    '<div key={id} className={styles.toast} role="status">',
    '<div key={id} className={clsx(styles.toast, bottom && styles.bottom)} role="status">',
)
toast = toast.replace(
    "className={clsx(styles.toast, error && styles.error)}",
    "className={clsx(styles.toast, error && styles.error, bottom && styles.bottom)}",
)
TOAST.write_text(toast, encoding='utf-8')
print('toast component: bottom variant')

# ---------- 3) 底部样式 ----------
CSS = Path('src/components/base/Toast.module.css')
css = CSS.read_text(encoding='utf-8')
if '.bottom' not in css:
    css += """
/* 底部提示（导入完成这类结果） */
[data-android] .bottom,
.bottom {
  top: auto;
  bottom: calc(32px + env(safe-area-inset-bottom));
  translate: none;
  animation: enter-bottom 0.24s var(--ds-ease-in-out);
}

@keyframes enter-bottom {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}
"""
    CSS.write_text(css, encoding='utf-8')
    print('toast css: bottom')

# ---------- 4) 完成任务后弹底部提示 ----------
JOB = Path('src/services/chat/importJob.ts')
job = JOB.read_text(encoding='utf-8')

job = job.replace(
    "const run = (task: (report: (phase: ImportPhase, value: number) => void) => Promise<void>) => {",
    "const run = (\n  task: (report: (phase: ImportPhase, value: number) => void) => Promise<ImportOutcome>\n) => {",
    1,
)
job = job.replace(
    "import type { ImportPhase } from './backup.js'",
    "import type { ImportOutcome } from './store.js'\nimport type { ImportPhase } from './backup.js'",
    1,
)
job = job.replace(
    """      await task(report)
      // 完成后直接回到 idle：不显示任何「已导入 N 个对话」提示
      useImportJob.setState({ ...IDLE })""",
    """      const outcome = await task(report)
      useImportJob.setState({ ...IDLE })
      // 只弹一条底部结果提示，几秒后自动消失
      const ok = outcome.added + outcome.updated
      const failed = Math.max(0, outcome.sessions - ok)
      showToast(
        failed > 0
          ? { key: 'historyImportDoneMixed', params: { ok, failed } }
          : { key: 'historyImportDone', params: { ok } },
        { duration: 4200, place: 'bottom' }
      )""",
    1,
)
# 两个入口把 outcome 返回出去
job = job.replace(
    """    report('writing', 0.98)
    useImportJob.setState({
      finished: { added: outcome.added, updated: outcome.updated },
      sessions: outcome.sessions,
      images: outcome.images,
    })
  })
}

export const startLinkImport""",
    """    report('writing', 0.98)
    useImportJob.setState({
      finished: { added: outcome.added, updated: outcome.updated },
      sessions: outcome.sessions,
      images: outcome.images,
    })
    return outcome
  })
}

export const startLinkImport""",
    1,
)
job = job.replace(
    """    report('writing', 0.98)
    useImportJob.setState({
      finished: { added: outcome.added, updated: outcome.updated },
      sessions: outcome.sessions,
      images: outcome.images,
    })
  })
}
""",
    """    report('writing', 0.98)
    useImportJob.setState({
      finished: { added: outcome.added, updated: outcome.updated },
      sessions: outcome.sessions,
      images: outcome.images,
    })
    return outcome
  })
}
""",
    1,
)
# 文件导入那条也要返回
job = job.replace(
    """      report('reading', ratio)
    })
    report('writing', 0.98)""",
    """      report('reading', ratio)
    })
    report('writing', 0.98)""",
    1,
)
JOB.write_text(job, encoding='utf-8')
print('import job: bottom result toast')
