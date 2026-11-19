"""把 markdown 恢复为「同步解析 + 分帧渲染」，并删除 worker 相关文件。

保留：workerChunkLoading（zip worker 用 classic 方式更稳）。
"""

from pathlib import Path

for dead in ['src/services/markdown/parseWorker.ts', 'src/services/markdown/parse.worker.ts']:
    p = Path(dead)
    if p.exists():
        p.unlink()
        print('removed', dead)

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
 * 解析没有放 worker：worker 产物在本环境里连脚本都不执行（连启动探针都收不到），
 * 拿不到可靠结论就不上，改成「先渲染前 60 个块、其余按帧补齐」，
 * 让单次 React 提交的工作量有上限，滚动与点击不会被一条超长回复顶住。
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
print('markdown back to sync + chunked render')
