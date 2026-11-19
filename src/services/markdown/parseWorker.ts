import { toMdAst } from './parse.js'

/**
 * 复用单例的解析 worker。
 *
 * 产物是 dist/static/js/parse-worker.js（自包含经典脚本，见 rspack.worker.config.ts）。
 * 短文本仍走主线程，避免长列表首次渲染出现闪烁。
 */

export const WORKER_PARSE_THRESHOLD = 600

type Ast = ReturnType<typeof toMdAst>

let worker: Worker | null = null
let sequence = 0
const pending = new Map<number, { resolve: (ast: Ast) => void; reject: (error: Error) => void }>()

const workerUrl = () => new URL('static/js/parse-worker.js', document.baseURI).toString()

const ensureWorker = (): Worker | null => {
  if (worker) {
    return worker
  }
  try {
    worker = new Worker(workerUrl())
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
