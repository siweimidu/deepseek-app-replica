type AndroidBridge = {
  statusInset: () => number
  systemFontScale: () => number
  openAppPermissions: () => void
  openSourcePage: (url: string, dark: boolean, closeLabel: string, browserLabel: string) => void
  readApiKey: () => string | null
  writeApiKey: (value: string | null) => boolean
  setDarkBars: (dark: boolean) => void
  requestRecentPhotos: () => void
  prefetchRecentPhotos: () => void
  requestHistoryExport: (name: string) => void
  writeHistoryExport: (bytes: string) => boolean
  finishHistoryExport: () => boolean
  beginImageSave: (name: string, mime: string) => boolean
  writeImageSave: (bytes: string) => boolean
  finishImageSave: (keep: boolean) => boolean
  requestRecording: () => void
  finishRecording: (keep: boolean) => boolean
  recordingLevel: () => number
  /** 开始下载导出包，返回本次下载的令牌；空字符串表示拒绝。 */
  versionLabel: () => string
  startHistoryDownload: (url: string) => string
  releaseHistoryDownload: (token: string) => void
  /** 查 GitHub 最新 Release，返回 JSON 字符串 */
  checkAppUpdate?: () => string
  /** 下载并交给系统安装器，进度走 android-update 事件 */
  installAppUpdate?: (url: string) => void
  /** "versionCode|versionName" */
  appVersionInfo?: () => string
  /** 打开「安装未知应用」授权页 */
  openInstallPermission?: () => void
}

export const android = (window as Window & { DeepSeekAndroid?: AndroidBridge }).DeepSeekAndroid

const writeAndroidBlob = async (blob: Blob, append: (base64: string) => boolean) => {
  const reader = blob.stream().getReader()
  const chunkSize = 32768
  try {
    for (;;) {
      const { value, done } = await reader.read()
      if (done) {
        return
      }
      for (let offset = 0; offset < value.length; offset += chunkSize) {
        const base64 = btoa(String.fromCharCode(...value.subarray(offset, offset + chunkSize)))
        if (!append(base64)) {
          throw new Error('Unable to write the file')
        }
      }
    }
  } finally {
    reader.releaseLock()
  }
}

export const saveAndroidHistory = async (name: string, blob: Blob) => {
  const device = android
  if (!device) {
    return
  }
  const status = await new Promise<string>((resolve) => {
    window.addEventListener(
      'android-export',
      (event) => resolve((event as CustomEvent<string>).detail),
      { once: true }
    )
    device.requestHistoryExport(name)
  })
  if (status === 'cancelled') {
    return
  }
  if (status !== 'ready') {
    throw new Error('Unable to open the export document')
  }
  let closed = false
  try {
    await writeAndroidBlob(blob, (base64) => device.writeHistoryExport(base64))
    closed = device.finishHistoryExport()
    if (!closed) {
      throw new Error('Unable to close the export document')
    }
  } finally {
    if (!closed) {
      device.finishHistoryExport()
    }
  }
}

export const saveAndroidImage = async (name: string, blob: Blob) => {
  const device = android
  if (!device?.beginImageSave(name, blob.type)) {
    throw new Error('Unable to create the image')
  }
  try {
    await writeAndroidBlob(blob, (base64) => device.writeImageSave(base64))
  } catch (error) {
    device.finishImageSave(false)
    throw error
  }
  if (!device.finishImageSave(true)) {
    throw new Error('Unable to save the image')
  }
}

/** 原生下载器回报的事件：progress 按已下载字节推进，ready 时给出同源地址。 */
type AndroidDownloadEvent = {
  token: string
  state: 'progress' | 'ready' | 'error'
  loaded: number
  total: number
  url: string
  message: string
}

export type AndroidDownload = { url: string; token: string; size: number; release: () => void }

/**
 * 交给原生下载：WebView 里的 fetch 受 CORS 限制，DeepSeek 导出链接不带
 * 跨域头，因此由 Java 侧下载到缓存目录，再以 appassets 同源地址交给前端读取。
 */
/** 多久没有新进展就算超时（大包可能几十 MB，不能按总时长掐） */
const DOWNLOAD_IDLE_TIMEOUT_MS = 90_000

export const downloadAndroidHistory = (
  url: string,
  onProgress: (loaded: number, total: number) => void
): Promise<AndroidDownload> => {
  const device = android
  if (!device?.startHistoryDownload) {
    throw new Error('Download is not available')
  }
  let token = ''
  const download = new Promise<AndroidDownload>((resolve, reject) => {
    const listen = (event: Event) => {
      const detail = (event as CustomEvent<AndroidDownloadEvent>).detail
      if (detail.token !== token) {
        return
      }
      if (detail.state === 'progress') {
        // 每来一块进度就重新计时，46MB 这种大包也不会被误判超时
        armWatchdog()
        onProgress(detail.loaded, detail.total)
        return
      }
      window.removeEventListener('android-download', listen)
      window.clearTimeout(watchdog)
      if (detail.state === 'ready') {
        resolve({
          url: detail.url,
          token,
          size: detail.loaded,
          release: () => device.releaseHistoryDownload(token),
        })
      } else {
        reject(new Error(detail.message || 'Download failed'))
      }
    }
    let watchdog = 0
    const armWatchdog = () => {
      window.clearTimeout(watchdog)
      watchdog = window.setTimeout(() => {
        window.removeEventListener('android-download', listen)
        reject(new Error('下载超时，请检查链接是否过期'))
      }, DOWNLOAD_IDLE_TIMEOUT_MS)
    }
    armWatchdog()
    window.addEventListener('android-download', listen)
    token = device.startHistoryDownload(url)
    if (!token) {
      window.clearTimeout(watchdog)
      window.removeEventListener('android-download', listen)
      reject(new Error('Download is not available'))
    }
  })
  return download
}
