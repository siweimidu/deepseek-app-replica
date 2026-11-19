import { memo, useMemo } from 'react'
import type { Source } from '../../services/chat/view.js'
import { toMdAst } from '../../services/markdown/parse.js'
import { useScrollToBottom } from '../messages/scrollContext.js'
import { MarkdownAstRenderer } from './MarkdownAstRenderer.js'
import { useThrottleMarkdownRender } from './useThrottleMarkdownRender.js'
import './markdown.css'
import './highlight.css'

/**
 * 渲染链路：节流 → 解析 AST → 渲染。
 * 传入 sources 时把正文里的 [citation:N] 渲染为角标。
 *
 * 说明：解析没有放到 worker —— parse.ts 依赖 katex / mermaid / highlight
 * 这些浏览器专用模块，worker 里加载即失败（实测 worker 收到请求从不回包）。
 * 长消息的卡顿由 useThrottleMarkdownRender 控制刷新频率来缓解。
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
