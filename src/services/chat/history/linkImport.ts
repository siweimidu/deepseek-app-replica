import { downloadAndroidHistory } from '../../../app/android.js'
import { blobSource, type ByteSource } from './source.js'

export type LinkSource = {
  source: ByteSource
  /** 原生下载的缓存文件在导入结束后删除。 */
  release: () => void
}

/** 导出链接只接受 http(s)，并去掉首尾空白与空白字符（从微信/QQ 复制常带）。 */
export const normalizeArchiveUrl = (input: string) => {
  const url = new URL(input.trim().replace(/\s+/g, ''))
  if (url.protocol !== 'https:' && url.protocol !== 'http:') {
    throw new Error('unsupported protocol')
  }
  return url.toString()
}

const decodeBase64 = (value: string) => {
  const binary = atob(value)
  const bytes = new Uint8Array(binary.length)
  for (let index = 0; index < binary.length; index++) {
    bytes[index] = binary.charCodeAt(index)
  }
  return bytes
}

const READ_CHUNK = 512 * 1024

/**
 * 兜底读取：绕过 HTTP 拦截，直接让原生把缓存里的包分块吐回来。
 * WebView 对拦截响应的处理各版本不一（Range/自定义头都可能直接 Failed to fetch），
 * 所以主通道失败时走这里，保证一定能读出来。
 */
const readViaBridge = (token: string, size: number) => {
  const bridge = (
    window as Window & {
      DeepSeekAndroid?: { readHistoryDownload?: (token: string, offset: number, length: number) => string }
    }
  ).DeepSeekAndroid
  if (!bridge?.readHistoryDownload) {
    throw new Error('download failed: no bridge')
  }
  const read = bridge.readHistoryDownload
  const parts: Uint8Array[] = []
  for (let offset = 0; offset < size; offset += READ_CHUNK) {
    const chunk = read.call(bridge, token, offset, READ_CHUNK)
    if (!chunk) {
      throw new Error('download failed: read error')
    }
    parts.push(decodeBase64(chunk))
  }
  return new Blob(parts as BlobPart[], { type: 'application/zip' })
}

/**
 * 打开导出链接：Android 交给原生下载到缓存（绕开 CORS、能显示下载进度），
 * 下载完成后先尝试同源整取，失败再用桥接分块读取。
 */
export const openLinkSource = async (
  input: string,
  onProgress: (loaded: number, total: number) => void
): Promise<LinkSource> => {
  const url = normalizeArchiveUrl(input)
  const native = await downloadAndroidHistory(url, onProgress).catch((error: unknown) => {
    // 没有原生桥（桌面开发态）时回退到 fetch。
    if ((error as Error).message === 'Download is not available') {
      return null
    }
    throw error
  })

  if (native) {
    try {
      const response = await fetch(native.url)
      if (!response.ok) {
        throw new Error('fetch failed')
      }
      return { source: blobSource(await response.blob()), release: native.release }
    } catch {
      // 拦截响应不可用时，直接向原生要字节
      const size = native.size
      if (size > 0) {
        return { source: blobSource(readViaBridge(native.token, size)), release: native.release }
      }
      native.release()
      throw new Error('download failed: read error')
    }
  }

  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`download failed: ${response.status}`)
  }
  const blob = await response.blob()
  onProgress(blob.size, blob.size)
  return { source: blobSource(blob), release: () => undefined }
}
