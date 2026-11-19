import { android } from '../app/android.js'

/**
 * 应用内更新
 *
 * 本项目的 versionName 长期是 0.1.0，只有 versionCode 随构建递增，
 * 所以「有没有新版本」用 APK 文件名里的 buildNN 与已安装 versionCode 比较，
 * 不比较 versionName，避免永远判定为「已是最新」。
 */

export type UpdateInfo = {
  /** 是否有比当前更新的包 */
  available: boolean
  /** 远端构建号 */
  latest: number
  /** 当前安装的构建号 */
  current: number
  tag: string
  notes: string
  url: string
  size: number
}

export type UpdateProgress = { state: 'downloading' | 'progress' | 'ready' | 'error'; percent: number; loaded: number; total: number; message: string }

const REPO = 'siweimidu/deepseek-app-replica'

const buildFromUrl = (url: string) => {
  const match = /build(\d+)/.exec(url)
  return match ? Number(match[1]) : 0
}

export const installedVersionCode = (): number => {
  const info = android?.appVersionInfo?.()
  if (!info) {
    return 0
  }
  const code = Number(info.split('|')[0])
  return Number.isFinite(code) ? code : 0
}

type RawRelease = { tag: string; notes: string; url: string; size: number; error?: string }

const checkNative = (): RawRelease | null => {
  const raw = android?.checkAppUpdate?.()
  if (!raw) {
    return null
  }
  try {
    const parsed = JSON.parse(raw) as { ok: boolean; tag: string; notes: string; url: string; size: number; error?: string }
    if (!parsed.ok) {
      return { tag: parsed.tag ?? '', notes: '', url: '', size: 0, error: parsed.error ?? '查询失败' }
    }
    return { tag: parsed.tag, notes: parsed.notes, url: parsed.url, size: parsed.size }
  } catch {
    return null
  }
}

/** 网页端调试用：直接读 GitHub API（浏览器里受 CORS 限制时会抛错） */
const checkWeb = async (): Promise<RawRelease> => {
  const response = await fetch(`https://api.github.com/repos/${REPO}/releases/latest`, {
    headers: { Accept: 'application/vnd.github+json' },
  })
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  const json = (await response.json()) as {
    tag_name?: string
    body?: string
    assets?: { name: string; size: number; browser_download_url: string }[]
  }
  const asset = (json.assets ?? []).find((item) => item.name.endsWith('.apk'))
  if (!asset) {
    throw new Error('该版本没有 APK 附件')
  }
  return { tag: json.tag_name ?? '', notes: json.body ?? '', url: asset.browser_download_url, size: asset.size }
}

export const checkAppUpdate = async (): Promise<UpdateInfo> => {
  const current = installedVersionCode()
  const native = checkNative()
  const raw = native ?? (await checkWeb())
  if (raw.error || !raw.url) {
    throw new Error(raw.error ?? '没有找到可下载的安装包')
  }
  const latest = buildFromUrl(raw.url)
  return {
    available: latest > current,
    latest,
    current,
    tag: raw.tag,
    notes: raw.notes,
    url: raw.url,
    size: raw.size,
  }
}

/** 让系统下载并弹出安装器；进度通过回调上报 */
export const installAppUpdate = (url: string, onProgress: (progress: UpdateProgress) => void) =>
  new Promise<void>((resolve, reject) => {
    if (!android?.installAppUpdate) {
      reject(new Error('当前环境不支持应用内安装'))
      return
    }
    let settled = false
    const listener = (event: Event) => {
      const detail = (event as CustomEvent<UpdateProgress>).detail
      onProgress(detail)
      if (detail.state === 'ready' && !settled) {
        settled = true
        window.removeEventListener('android-update', listener)
        resolve()
      }
      if (detail.state === 'error' && !settled) {
        settled = true
        window.removeEventListener('android-update', listener)
        reject(new Error(detail.message || '下载失败'))
      }
    }
    window.addEventListener('android-update', listener)
    android.installAppUpdate(url)
  })

/** 打开系统「安装未知应用」授权页 */
export const openInstallPermission = () => android?.openInstallPermission?.()
