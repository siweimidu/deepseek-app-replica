"""长消息分帧渲染：把大 AST 分批交给渲染器，避免一次性渲染卡住主线程。"""

from pathlib import Path

MD = Path('src/components/markdown/Markdown.tsx')
MD.write_text('''import { memo, useEffect, useMemo, useState } from 'react'
import type { Source } from '../../services/chat/view.js'
import { toMdAst } from '../../services/markdown/parse.js'
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
 * 解析没有放 worker（parse.ts 依赖浏览器专用模块，且实测 worker 收不到回包），
 * 长消息改为「先渲染前 60 个块，其余按帧补齐」，
 * 这样一次 React 提交的工作量有上限，滚动和点击不会被一条超长回复顶住。
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
  const ast = useMemo(
    () => (throttledMarkdown ? toMdAst(throttledMarkdown, { sources, disableLink }) : null),
    [throttledMarkdown, sources, disableLink]
  )

  const total = ast?.children?.length ?? 0
  const [limit, setLimit] = useState(FIRST_BATCH)

  // 内容变了就回到首批，避免上一轮的限制卡住新内容
  useEffect(() => {
    setLimit(FIRST_BATCH)
  }, [throttledMarkdown])

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
''', encoding='utf-8')
print('progressive render written')
