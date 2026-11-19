import { create } from 'zustand'
import { translate } from '../../i18n/index.js'
import { showToast } from '../../components/base/toastState.js'
import { BackupError } from './history/errors.js'
import { importHistory, importHistoryFromUrl } from './backup.js'
import { disposeInflateWorker } from './history/inflateWorker.js'
import type { ImportOutcome } from './store.js'

export type ImportPhase = 'idle' | 'downloading' | 'reading' | 'writing' | 'done' | 'error'

type ImportJobState = {
  phase: ImportPhase
  /** 0..1，供顶部状态条与进度环使用 */
  percent: number
  sessions: number
  images: number
  loaded: number
  total: number
  startedAt: number
  finished: { added: number; updated: number } | null
  failure: string | null
}

/** 导入进度存在模块级 store 里：离开数据管理页后任务照常推进，进度也照常读取。 */
export const useImportJob = create<ImportJobState>(() => ({
  phase: 'idle',
  percent: 0,
  sessions: 0,
  images: 0,
  loaded: 0,
  total: 0,
  startedAt: 0,
  finished: null,
  failure: null,
}))

const IDLE: ImportJobState = {
  phase: 'idle',
  percent: 0,
  sessions: 0,
  images: 0,
  loaded: 0,
  total: 0,
  startedAt: 0,
  finished: null,
  failure: null,
}

const DOWNLOAD_SHARE = 0.15
const READ_SHARE = 0.75

let running = false

const describe = (error: unknown) =>
  error instanceof BackupError
    ? translate(error.key)
    : error instanceof Error
      ? error.message
      : String(error)

export const isImportRunning = () => running

/** 开始导入后立刻返回，进度通过 useImportJob 订阅；页面卸载不会中断任务。 */
const run = (
  task: (report: (phase: ImportPhase, value: number) => void) => Promise<ImportOutcome>
) => {
  if (running) {
    return
  }
  running = true
  useImportJob.setState({ ...IDLE, phase: 'downloading', startedAt: Date.now() })
  const report = (phase: ImportPhase, percent: number) =>
    useImportJob.setState((state) =>
      state.phase === 'error' ? state : { phase, percent: Math.min(1, Math.max(0, percent)) }
    )
  void (async () => {
    try {
      const outcome = await task(report)
      useImportJob.setState({ ...IDLE })
      // 只弹一条底部结果提示，几秒后自动消失
      const ok = outcome.added + outcome.updated
      const failed = Math.max(0, outcome.sessions - ok)
      showToast(
        failed > 0
          ? { key: 'historyImportDoneMixed', params: { ok, failed } }
          : { key: 'historyImportDone', params: { ok } },
        { duration: 4200, place: 'bottom' }
      )
    } catch (error) {
      const message = describe(error)
      useImportJob.setState({ phase: 'error', failure: message })
      showToast({ key: 'historyImportFailedDetail', params: { message }, type: 'error' })
    } finally {
      running = false
      disposeInflateWorker()
    }
  })()
}

/** 收起顶部进度条：结果提示留在数据管理页。 */
export const dismissImportJob = () => {
  if (!running) {
    useImportJob.setState(IDLE)
  }
}

export const startFileImport = (file: File) => {
  run(async (report) => {
    report('reading', 0)
    const outcome = await importHistory(file, (progress) => {
      const ratio = progress.bytesTotal ? progress.bytes / progress.bytesTotal : progress.done / Math.max(1, progress.total)
      useImportJob.setState({
        phase: 'reading',
        sessions: progress.sessions,
        images: progress.images,
        percent: Math.min(1, ratio),
      })
      report('reading', ratio)
    })
    report('writing', 0.98)
    useImportJob.setState({
      finished: { added: outcome.added, updated: outcome.updated },
      sessions: outcome.sessions,
      images: outcome.images,
    })
    return outcome
  })
}

export const startLinkImport = (url: string) => {
  run(async (report) => {
    report('downloading', 0)
    const outcome = await importHistoryFromUrl(
      url,
      (progress) => {
        const ratio = progress.bytesTotal ? progress.bytes / progress.bytesTotal : progress.done / Math.max(1, progress.total)
        report('reading', DOWNLOAD_SHARE + ratio * READ_SHARE)
        useImportJob.setState({
          sessions: progress.sessions,
          images: progress.images,
          phase: 'reading',
          percent: DOWNLOAD_SHARE + ratio * READ_SHARE,
        })
      },
      (loaded, total) => {
        useImportJob.setState({
          phase: 'downloading',
          loaded,
          total,
          percent: total ? (loaded / total) * DOWNLOAD_SHARE : 0,
        })
      }
    )
    report('writing', 0.98)
    useImportJob.setState({
      finished: { added: outcome.added, updated: outcome.updated },
      sessions: outcome.sessions,
      images: outcome.images,
    })
    return outcome
  })
}
