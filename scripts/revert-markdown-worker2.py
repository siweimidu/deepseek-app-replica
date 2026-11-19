"""回退 markdown worker，保留 workerChunkLoading（对 zip worker 更稳）。"""

from pathlib import Path

for dead in ['src/services/markdown/parseWorker.ts', 'src/services/markdown/parse.worker.ts']:
    p = Path(dead)
    if p.exists():
        p.unlink()
        print('removed', dead)

MD = Path('src/components/markdown/Markdown.tsx')
MD.write_text('''import { memo, useMemo } from 'react'
import type { Source } from '../../services/chat/view.js'
import { toMdAst } from '../../services/markdown/parse.js'
import { useScrollToBottom } from '../messages/scrollContext.js'
import { MarkdownAstRenderer } from './MarkdownAstRenderer.js'
import { useThrottleMarkdownRender } from './useThrottleMarkdownRender.js'
import './markdown.css'
import './highlight.css'

/**
 * 渲染链路：节流 → 解析 AST → 渲染。
 *
 * 解析没有放到 worker：一是 parse.ts 依赖 katex / mermaid / highlight 这类浏览器专用模块；
 * 二是实测 worker（含 importScripts 版本）收不到回包，无法确认可用。
 * 长消息的刷新频率由 useThrottleMarkdownRender 控制。
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
''', encoding='utf-8')
print('markdown reverted (sync)')
