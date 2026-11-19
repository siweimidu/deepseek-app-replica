import { inflateSync } from 'fflate'

/**
 * 解压 worker：整个导入过程复用同一个实例。
 * 每条目的压缩数据在这里解压后整块回传（transferable，零拷贝）。
 */

type Request = { id: number; chunks: Uint8Array[] }

self.onmessage = (event: MessageEvent<Request>) => {
  const { id, chunks } = event.data
  try {
    const total = chunks.reduce((sum, chunk) => sum + chunk.length, 0)
    const merged = new Uint8Array(total)
    let offset = 0
    for (const chunk of chunks) {
      merged.set(chunk, offset)
      offset += chunk.length
    }
    const data = inflateSync(merged)
    const payload = data.buffer.slice(0)
    ;(self as unknown as Worker).postMessage({ id, data: payload }, [payload])
  } catch (error) {
    ;(self as unknown as Worker).postMessage({ id, error: String(error) })
  }
}
