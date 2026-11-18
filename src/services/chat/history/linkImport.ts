import { downloadAndroidHistory } from '../../../app/android.js'
import { blobSource, rangeSource, type ByteSource } from './source.js'

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

/**
 * 打开导出链接：Android 交给原生下载（绕开 CORS 且能显示下载进度），
 * 桌面/浏览器开发态直接下载成 Blob。
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
    return { source: await rangeSource(native.url), release: native.release }
  }
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`download failed: ${response.status}`)
  }
  const blob = await response.blob()
  onProgress(blob.size, blob.size)
  return { source: blobSource(blob), release: () => undefined }
}
