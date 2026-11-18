import * as db from '../db.js'
import type { Session } from '../types.js'
import { BackupError, fail } from './errors.js'
import type { SessionIndexEntry } from './format.js'
import { INDEX_PATH, MANIFEST_PATH, USER_PATH, parseSessionPath, sessionFilesDir } from './paths.js'
import { checkManifest, readSessionFile, readSessionIndex } from './schema.js'
import { toLocalSession } from './toLocal.js'
import {
  ArchiveError,
  isZipFile,
  readArchive,
  readEntry,
  summarizeArchive,
  type ArchiveEntry,
} from './zipReader.js'
import type { ByteSource } from './source.js'

/** 从原件字节补充图片 MIME；无法识别时为空字符串，图片身份仍由归档的 is_image 决定。 */
const imageType = (bytes: Uint8Array): string => {
  const startsWith = (...prefix: number[]) => prefix.every((byte, index) => bytes[index] === byte)
  const header = new TextDecoder('ascii').decode(bytes.subarray(0, 12))
  if (startsWith(0xff, 0xd8, 0xff)) {
    return 'image/jpeg'
  }
  if (startsWith(0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a)) {
    return 'image/png'
  }
  if (header.startsWith('GIF87a') || header.startsWith('GIF89a')) {
    return 'image/gif'
  }
  if (header.startsWith('RIFF') && header.slice(8, 12) === 'WEBP') {
    return 'image/webp'
  }
  if (startsWith(0x42, 0x4d)) {
    return 'image/bmp'
  }
  if (startsWith(0x49, 0x49, 0x2a, 0) || startsWith(0x4d, 0x4d, 0, 0x2a)) {
    return 'image/tiff'
  }
  if (header.slice(4, 8) === 'ftyp' && ['avif', 'avis'].includes(header.slice(8, 12))) {
    return 'image/avif'
  }
  return ''
}

const readJson = async (entry: ArchiveEntry): Promise<unknown> => {
  const text = await (await readEntry(entry)).text()
  try {
    return JSON.parse(text)
  } catch {
    return fail('backupInvalidJson')
  }
}

/** 导入进度：bytes 是已解压字节，用于把进度按体积加权。 */
export type ImportProgress = {
  done: number
  total: number
  bytes: number
  bytesTotal: number
  sessions: number
  images: number
}

export type ImportResult = { sessions: number; images: number }

/** 攒够一批再写库：每张图片单独开一次事务是旧版导入慢的第二个原因。 */
const FILE_BATCH = 12
const FILE_BATCH_BYTES = 24 * 1024 * 1024
const PROGRESS_INTERVAL_MS = 80

/**
 * 流式导入：manifest → user（不导入）→ 全部会话 JSON → index → 全部图片。
 * 也支持会话与图片交错排列、index 位于末尾的条目顺序。
 * 会话解析后留在内存，图片按批写入暂存，最后一次性回填 MIME 并写会话。
 */
export const importArchive = async (
  input: File | ByteSource,
  onProgress?: (progress: ImportProgress) => void
): Promise<ImportResult> => {
  if (!(await isZipFile(input))) {
    fail('backupUnrecognized')
  }
  const totals = await summarizeArchive(input)
  const sessions = new Map<string, Session>()
  const images = new Map<string, string>()
  /** 已保存的原件：文件 ID → MIME。同一图片出现在多个会话目录时只保存一次。 */
  const stored = new Map<string, string>()
  let manifest = false
  let index: SessionIndexEntry[] | undefined
  let currentSessionId: string | undefined
  let done = 0
  let bytes = 0
  let imagesWritten = 0
  let batch: { id: string; blob: Blob }[] = []
  let batchBytes = 0
  let lastReport = 0

  const report = (force = false) => {
    if (!onProgress) {
      return
    }
    const now = Date.now()
    if (!force && now - lastReport < PROGRESS_INTERVAL_MS) {
      return
    }
    lastReport = now
    onProgress({
      done,
      total: totals.entries,
      bytes,
      bytesTotal: totals.bytes,
      sessions: sessions.size,
      images: imagesWritten,
    })
  }

  const flush = async () => {
    if (!batch.length) {
      return
    }
    const files = batch
    batch = []
    batchBytes = 0
    await db.saveStagingFiles(files)
  }

  const saveImage = async (entry: ArchiveEntry, id: string) => {
    if (stored.has(id)) {
      return
    }
    const data = await entry.bytes()
    const type = imageType(data.subarray(0, 16))
    batch.push({ id, blob: new Blob([data as Uint8Array<ArrayBuffer>], { type }) })
    batchBytes += data.length
    imagesWritten += 1
    stored.set(id, type)
    if (batch.length >= FILE_BATCH || batchBytes >= FILE_BATCH_BYTES) {
      await flush()
    }
  }

  report(true)
  try {
    for await (const entry of readArchive(input)) {
      const { path } = entry
      const sessionId = parseSessionPath(path)
      if (!manifest) {
        if (path !== MANIFEST_PATH) {
          fail('backupUnrecognized')
        }
        checkManifest(await readJson(entry))
        manifest = true
      } else if (path === USER_PATH && !index && sessions.size === 0) {
        // 账号信息（已脱敏）不导入；文件可能缺失。
      } else if (sessionId !== null && !index) {
        const local = toLocalSession(readSessionFile(await readJson(entry)))
        if (local.session.id !== sessionId || sessions.has(sessionId)) {
          fail('backupIncomplete')
        }
        sessions.set(sessionId, local.session)
        currentSessionId = sessionId
        for (const [imagePath, id] of local.images) {
          images.set(imagePath, id)
        }
      } else if (path === INDEX_PATH && !index) {
        index = readSessionIndex(await readJson(entry))
      } else if (
        index
          ? sessions.has(/^chat_sessions\/([^/]+)_files\//.exec(path)?.[1] ?? '')
          : currentSessionId && path.startsWith(sessionFilesDir(currentSessionId))
      ) {
        // 没有被引用的条目不保存，引用了但缺失的图片只展示文件名。
        const id = images.get(path)
        if (id !== undefined) {
          await saveImage(entry, id)
        }
      } else {
        fail('backupIncomplete')
      }
      done += 1
      bytes += entry.size
      report()
    }
  } catch (error) {
    throw error instanceof ArchiveError ? new BackupError('backupIncomplete') : error
  } finally {
    await flush().catch(() => undefined)
  }
  if (!manifest) {
    fail('backupUnrecognized')
  }
  // index 只列出成功写出的会话，与会话文件一一对应。
  const listed = new Set(index?.map((entry) => entry.id))
  if (
    !index ||
    listed.size !== index.length ||
    listed.size !== sessions.size ||
    [...sessions.keys()].some((id) => !listed.has(id))
  ) {
    fail('backupIncomplete')
  }
  // 图片类型此时才齐全：直接在内存里回填，省掉一次全表游标重写。
  for (const session of sessions.values()) {
    for (const message of session.messages) {
      if (message.role !== 'user') {
        continue
      }
      for (const file of message.files) {
        const type = stored.get(file.id) ?? ''
        if (file.mimeType !== type) {
          file.mimeType = type
        }
      }
    }
  }
  await db.addStagingSessions([...sessions.values()])
  report(true)
  return { sessions: sessions.size, images: imagesWritten }
}
