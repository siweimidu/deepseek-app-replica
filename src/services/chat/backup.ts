import { formatDate } from '../../utils/format.js'
import * as db from './db.js'
import type { ImportProgress } from './history/importArchive.js'
import type { ByteSource } from './history/source.js'
import { applyImportedHistory, replaceHistory, useChatStore, type ImportOutcome } from './store.js'
import type { Session } from './types.js'

export { BackupError } from './history/errors.js'

// 导入、导出与全部删除串行处理，避免读取归档时数据被清空或两个替换事务交错。
let backupQueue: Promise<unknown> = Promise.resolve()

const enqueueBackup = <T>(run: () => Promise<T>): Promise<T> => {
  const task = backupQueue.then(run)
  backupQueue = task.catch(() => {})
  return task
}

const backupFileName = (date: Date) => `deepseek_data-${formatDate(date)}.zip`

/** 导出为历史会话导出格式的 ZIP，可再次导入。 */
export const exportHistory = (): Promise<{ name: string; blob: Blob }> =>
  enqueueBackup(async () => {
    // 列表和已加载内容保留导出开始时的快照；未打开的会话逐条读取，不填满详情缓存。
    const { sessions, sessionCache } = useChatStore.getState()
    async function* readSessions(): AsyncGenerator<Session> {
      for (const summary of sessions) {
        const session = Object.hasOwn(sessionCache, summary.id)
          ? sessionCache[summary.id]
          : await db.loadSession(summary.id)
        if (!session) {
          throw new Error(`History session disappeared during export: ${summary.id}`)
        }
        // 详情读取期间可能重命名，归档标题与开始时的列表保持一致。
        yield { ...session, ...summary }
      }
    }
    const { exportArchive } = await import('./history/exportArchive.js')
    const now = new Date()
    const blob = await exportArchive(readSessions())
    return { name: backupFileName(now), blob }
  })

/**
 * 导入导出包：流式校验 ZIP 并写入暂存，成功后才合并进正式历史。
 * 已存在的会话按 ID 补齐标题与时间，不会新建、不会重复。
 */
export const importHistory = (
  input: File | ByteSource,
  onProgress?: (progress: ImportProgress) => void
): Promise<ImportOutcome> =>
  enqueueBackup(async () => {
    const { importArchive } = await import('./history/importArchive.js')
    return applyImportedHistory(() => importArchive(input, onProgress))
  })

/** 从导出链接导入：先由原生下载到缓存，再走与选文件完全相同的导入流程。 */
export const importHistoryFromUrl = async (
  url: string,
  onProgress?: (progress: ImportProgress) => void,
  onDownload?: (loaded: number, total: number) => void
): Promise<ImportOutcome> => {
  const { openLinkSource } = await import('./history/linkImport.js')
  const link = await openLinkSource(url, onDownload ?? (() => undefined))
  try {
    return await importHistory(link.source, onProgress)
  } finally {
    link.release()
  }
}

/** 确认删除后调用：以空历史原子替换全部本地会话与附件，保留 API Key 和其他设置。 */
export const clearHistory = (): Promise<void> =>
  enqueueBackup(async () => {
    await replaceHistory(async () => {})
  })
