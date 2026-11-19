import { toMdAst } from './parse.js'

/**
 * Markdown 解析 worker 源码。
 * 由 rspack.worker.config.ts 单独打成 dist/static/js/parse-worker.js（自包含经典脚本）。
 */

type Request = { id: number; text: string; sources?: unknown; disableLink: boolean }

self.onmessage = (event: MessageEvent<Request>) => {
  const { id, text, sources, disableLink } = event.data
  try {
    const ast = toMdAst(text, { sources: sources as never, disableLink })
    ;(self as unknown as Worker).postMessage({ id, ast })
  } catch (error) {
    ;(self as unknown as Worker).postMessage({
      id,
      error: String((error as Error)?.message ?? error),
    })
  }
}
