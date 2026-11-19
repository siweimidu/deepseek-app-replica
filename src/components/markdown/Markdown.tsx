import { memo, useEffect, useMemo, useState } from 'react'
import type { Source } from '../../services/chat/view.js'
import { toMdAst } from '../../services/markdown/parse.js'
import { WORKER_PARSE_THRESHOLD, parseInWorker } from '../../services/markdown/parseWorker.js'
import { useScrollToBottom } from '../messages/scrollContext.js'
import { MarkdownAstRenderer } from './MarkdownAstRenderer.js'
import { useThrottleMarkdownRender } from './useThrottleMarkdownRender.js'
import './markdown.css'
import './highlight.css'

/** 一次渲染多少顶层节点；超过就分帧补齐 */
const FIRST_BATCH = 60
const STEP = 120
/** 超过这个节点数才启用分帧 */
const CHUNK_THRESHOLD = 90

/**
 * 渲染链路：节流 → 解析 AST → 分帧渲染。
 *
 * 长消息（>600 字）的解析交给 worker（dist/static/js/parse-worker.js，自包含经典脚本），
 * 解析期间先显示上一版 AST，避免主线程被一条超长回复顶住；
 * 渲染本身再按帧补齐，单次 React 提交的工作量同样有上限。
 */
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
        if (!cancelled) {
          setWorkerAst(next)
        }
      })
      .catch(() => {
        if (!cancelled) {
          setWorkerAst(toMdAst(throttledMarkdown, { sources, disableLink }))
        }
      })
    return () => {
      cancelled = true
    }
  }, [heavy, throttledMarkdown, sources, disableLink])

  const ast = heavy ? workerAst : syncAst
  const total = ast?.children?.length ?? 0
  const [limit, setLimit] = useState(FIRST_BATCH)

  useEffect(() => {
    setLimit(FIRST_BATCH)
  }, [ast])

  useEffect(() => {
    if (total <= CHUNK_THRESHOLD || limit >= total) {
      return
    }
    const frame = requestAnimationFrame(() => {
      setLimit((value) => Math.min(total, value + STEP))
    })
    return () => cancelAnimationFrame(frame)
  }, [total, limit])

  const visible = useMemo(() => {
    if (!ast || !ast.children) {
      return ast
    }
    if (total <= CHUNK_THRESHOLD || limit >= total) {
      return ast
    }
    return { ...ast, children: ast.children.slice(0, limit) }
  }, [ast, total, limit])

  return visible ? (
    <MarkdownAstRenderer
      key={cacheKey}
      className={className}
      ast={visible}
      loading={loading}
      onUpdate={scrollToBottom}
    />
  ) : null
})
