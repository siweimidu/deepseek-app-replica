"""② 再试一次：让 worker 用 importScripts 加载子 chunk，然后恢复 markdown worker。"""

from pathlib import Path

# 1) rspack: worker 内部用 importScripts（经典 worker 才能加载）
CFG = Path('rspack.config.ts')
cfg = CFG.read_text(encoding='utf-8')
if 'workerChunkLoading' not in cfg:
    cfg = cfg.replace(
        '  output: {',
        "  output: {\n    // worker 里的子 chunk 用 importScripts 加载：\n    // 默认按 ESM import 生成，Worker 以经典方式创建时会直接语法错误\n    workerChunkLoading: 'import-scripts',",
        1,
    )
    CFG.write_text(cfg, encoding='utf-8')
print('workerChunkLoading:', 'workerChunkLoading' in cfg)

# 2) 恢复 parse worker
Path('src/services/markdown/parse.worker.ts').write_text('''import { toMdAst } from './parse.js'

/** Markdown 解析 worker：长消息的解析放到这里，避免卡住主线程 */

type Request = { id: number; text: string; sources?: unknown; disableLink: boolean }

self.onmessage = (event: MessageEvent<Request>) => {
  const { id, text, sources, disableLink } = event.data
  try {
    const ast = toMdAst(text, { sources: sources as never, disableLink })
    ;(self as unknown as Worker).postMessage({ id, ast })
  } catch (error) {
    ;(self as unknown as Worker).postMessage({ id, error: String(error) })
  }
}
''', encoding='utf-8')

Path('src/services/markdown/parseWorker.ts').write_text('''import { toMdAst } from './parse.js'

/** 复用单例的解析 worker；短文本仍走主线程，长文本才转过去 */

export const WORKER_PARSE_THRESHOLD = 600

type Ast = ReturnType<typeof toMdAst>

let worker: Worker | null = null
let sequence = 0
const pending = new Map<number, { resolve: (ast: Ast) => void; reject: (error: Error) => void }>()

const ensureWorker = (): Worker | null => {
  if (worker) {
    return worker
  }
  try {
    worker = new Worker(new URL('./parse.worker.js', import.meta.url))
    worker.onmessage = (event: MessageEvent<{ id: number; ast?: Ast; error?: string }>) => {
      const entry = pending.get(event.data.id)
      if (!entry) {
        return
      }
      pending.delete(event.data.id)
      if (event.data.error || !event.data.ast) {
        entry.reject(new Error(event.data.error ?? 'parse failed'))
        return
      }
      entry.resolve(event.data.ast)
    }
    worker.onerror = () => {
      for (const entry of pending.values()) {
        entry.reject(new Error('parse worker failed'))
      }
      pending.clear()
      worker = null
    }
  } catch {
    worker = null
  }
  return worker
}

export const parseInWorker = (
  text: string,
  options: { sources?: unknown; disableLink: boolean }
): Promise<Ast> => {
  const instance = ensureWorker()
  if (!instance) {
    return Promise.resolve(toMdAst(text, options as never))
  }
  const id = ++sequence
  return new Promise<Ast>((resolve, reject) => {
    pending.set(id, { resolve, reject })
    instance.postMessage({ id, text, sources: options.sources, disableLink: options.disableLink })
  })
}

export const disposeParseWorker = () => {
  worker?.terminate()
  worker = null
  for (const entry of pending.values()) {
    entry.reject(new Error('parse worker disposed'))
  }
  pending.clear()
}
''', encoding='utf-8')

# 3) Markdown 组件用 worker（长文本）
MD = Path('src/components/markdown/Markdown.tsx')
MD.write_text('''import { memo, useEffect, useMemo, useState } from 'react'
import type { Source } from '../../services/chat/view.js'
import { toMdAst } from '../../services/markdown/parse.js'
import { WORKER_PARSE_THRESHOLD, parseInWorker } from '../../services/markdown/parseWorker.js'
import { useScrollToBottom } from '../messages/scrollContext.js'
import { MarkdownAstRenderer } from './MarkdownAstRenderer.js'
import { useThrottleMarkdownRender } from './useThrottleMarkdownRender.js'
import './markdown.css'
import './highlight.css'

/** 渲染链路：节流 → 解析 AST → 渲染。短消息主线程解析，长消息交给 worker。 */
export const Markdown = memo(function Markdown({
  content,
  loading,
  cacheKey,
  className,
  disableLink,
  sources,
}: {
  content: string
  loading: boolean
  cacheKey: string
  className?: string
  disableLink: boolean
  sources?: Source[]
}) {
  const scrollToBottom = useScrollToBottom()
  const throttledMarkdown = useThrottleMarkdownRender(content, loading)
  const heavy = (throttledMarkdown?.length ?? 0) > WORKER_PARSE_THRESHOLD
  const [workerAst, setWorkerAst] = useState<ReturnType<typeof toMdAst> | null>(null)

  const syncAst = useMemo(
    () => (throttledMarkdown && !heavy ? toMdAst(throttledMarkdown, { sources, disableLink }) : null),
    [throttledMarkdown, heavy, sources, disableLink]
  )

  useEffect(() => {
    if (!heavy || !throttledMarkdown) {
      setWorkerAst(null)
      return
    }
    let cancelled = false
    void parseInWorker(throttledMarkdown, { sources, disableLink })
      .then((next) => {
        if (!cancelled) setWorkerAst(next)
      })
      .catch(() => {
        if (!cancelled) setWorkerAst(toMdAst(throttledMarkdown, { sources, disableLink }))
      })
    return () => {
      cancelled = true
    }
  }, [heavy, throttledMarkdown, sources, disableLink])

  const ast = heavy ? workerAst : syncAst
  return ast ? (
    <MarkdownAstRenderer
      key={cacheKey}
      className={className}
      ast={ast}
      loading={loading}
      onUpdate={scrollToBottom}
    />
  ) : null
})
''', encoding='utf-8')
print('markdown worker restored')
