import { inflateSync } from 'fflate'

/**
 * 复用的解压 worker。
 *
 * 之前用过 fflate 的 AsyncInflate，但它每个实例都会新开一个 worker；
 * 导出包有成百上千个条目，光创建销毁 worker 就把时间吃光了。
 * 这里全程只用一个实例，按请求 id 配对回包。
 */

let worker: Worker | null = null
let sequence = 0
const pending = new Map<number, { resolve: (data: Uint8Array) => void; reject: (error: Error) => void }>()

const merge = (chunks: Uint8Array[]) => {
  const total = chunks.reduce((sum, chunk) => sum + chunk.length, 0)
  const merged = new Uint8Array(total)
  let offset = 0
  for (const chunk of chunks) {
    merged.set(chunk, offset)
    offset += chunk.length
  }
  return merged
}

const ensureWorker = (): Worker | null => {
  if (worker) {
    return worker
  }
  try {
    worker = new Worker(new URL('./inflate.worker.js', import.meta.url), { type: 'module' })
    worker.onmessage = (event: MessageEvent<{ id: number; data?: ArrayBuffer; error?: string }>) => {
      const entry = pending.get(event.data.id)
      if (!entry) {
        return
      }
      pending.delete(event.data.id)
      if (event.data.error) {
        entry.reject(new Error(event.data.error))
        return
      }
      entry.resolve(new Uint8Array(event.data.data ?? new ArrayBuffer(0)))
    }
    worker.onerror = () => {
      for (const entry of pending.values()) {
        entry.reject(new Error('inflate worker failed'))
      }
      pending.clear()
      worker = null
    }
  } catch {
    worker = null
  }
  return worker
}

/** 解压一段 deflate 数据；worker 不可用时退回主线程同步解压 */
export const inflateInWorker = async (chunks: Uint8Array[]): Promise<Uint8Array> => {
  const instance = ensureWorker()
  if (!instance) {
    return inflateSync(merge(chunks))
  }
  const id = ++sequence
  return new Promise<Uint8Array>((resolve, reject) => {
    pending.set(id, { resolve, reject })
    const transfer = chunks.map((chunk) => chunk.buffer as ArrayBuffer)
    instance.postMessage({ id, chunks }, transfer)
  })
}

/** 导入结束或失败时释放 worker */
export const disposeInflateWorker = () => {
  worker?.terminate()
  worker = null
  for (const entry of pending.values()) {
    entry.reject(new Error('inflate worker disposed'))
  }
  pending.clear()
}
