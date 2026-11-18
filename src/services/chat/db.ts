import { openDB, type DBSchema, type IDBPDatabase } from 'idb'
import { toSessionSummary, type Session, type SessionSummary } from './types.js'

/** IndexedDB 存储结构版本；新增或调整存储、索引时递增。 */
const DB_VERSION = 11

/** 文件原件按附件的本地 id 存储，所有引用同一 id 的消息共用一份；用于缩略图、打开查看，以及没有 serverId 时补传。 */
export type StoredFile = {
  id: string
  blob: Blob
}

/** 文件引用留在摘要中，删除会话时通过索引判断原件是否仍被引用。 */
type StoredSessionSummary = SessionSummary & { fileIds: string[] }

interface ChatDB extends DBSchema {
  /** 当前使用的会话，界面读写都在这里 */
  sessions: { key: string; value: Session }
  sessionSummaries: {
    key: string
    value: StoredSessionSummary
    indexes: { fileIds: string }
  }
  /** 当前使用的文件原件 */
  files: { key: string; value: StoredFile }
  /**
   * 历史导入的暂存：导入过程中会话与原件只写入这两个存储，`sessions` / `files` 保持不变；
   * 全部校验通过后在一个事务中替换正式数据并清空暂存，失败时只清空暂存。
   */
  sessionsStaging: { key: string; value: Session }
  filesStaging: { key: string; value: StoredFile }
}

let dbPromise: Promise<IDBPDatabase<ChatDB>> | null = null

const storedSummary = (session: Session): StoredSessionSummary => ({
  ...toSessionSummary(session),
  fileIds: [
    ...new Set(
      session.messages.flatMap((message) =>
        message.role === 'user' ? message.files.map((file) => file.id) : []
      )
    ),
  ],
})

const abortTransaction = (tx: { abort(): void }) => {
  try {
    tx.abort()
  } catch {
    // 事务已因请求失败中止。
  }
}

// 每个操作拿到连接后立即创建事务；IndexedDB 按创建顺序执行范围重叠的事务，读取总能看到之前发起的写入。
const getDB = () =>
  (dbPromise ??= openDB<ChatDB>('chat-demo', DB_VERSION, {
    upgrade(db, _oldVersion, _newVersion, tx) {
      // 初始化当前格式需要的存储与索引，不迁移旧消息。
      for (const name of ['sessions', 'files', 'sessionsStaging', 'filesStaging'] as const) {
        if (!db.objectStoreNames.contains(name)) {
          db.createObjectStore(name, { keyPath: 'id' })
        }
      }
      const summaries = db.objectStoreNames.contains('sessionSummaries')
        ? tx.objectStore('sessionSummaries')
        : db.createObjectStore('sessionSummaries', { keyPath: 'id' })
      if (!summaries.indexNames.contains('fileIds')) {
        summaries.createIndex('fileIds', 'fileIds', { multiEntry: true })
      }
    },
  }).catch((error: unknown) => {
    // 打开失败后允许界面重试，避免一直复用已拒绝的 Promise。
    dbPromise = null
    throw error
  }))

export const loadSessionSummaries = async (): Promise<SessionSummary[]> =>
  (await (await getDB()).getAll('sessionSummaries')).map(toSessionSummary)

export const loadSession = async (id: string): Promise<Session | undefined> =>
  (await getDB()).get('sessions', id)

export const saveSession = async (session: Session, files: StoredFile[] = []): Promise<void> => {
  const summary = storedSummary(session)
  const tx = (await getDB()).transaction(['sessions', 'sessionSummaries', 'files'], 'readwrite')
  await Promise.all([
    (async () => {
      try {
        for (const file of files) {
          await tx.objectStore('files').put(file)
        }
        await tx.objectStore('sessions').put(session)
        await tx.objectStore('sessionSummaries').put(summary)
      } catch (error) {
        abortTransaction(tx)
        throw error
      }
    })(),
    tx.done,
  ])
}

/** 未打开的会话也可重命名，只读取该会话，原子更新详情和列表。 */
export const renameSession = async (id: string, title: string): Promise<void> => {
  const tx = (await getDB()).transaction(['sessions', 'sessionSummaries'], 'readwrite')
  await Promise.all([
    (async () => {
      try {
        const sessions = tx.objectStore('sessions')
        const session = await sessions.get(id)
        if (session) {
          session.title = title
          await sessions.put(session)
          await tx.objectStore('sessionSummaries').put(storedSummary(session))
        }
      } catch (error) {
        abortTransaction(tx)
        throw error
      }
    })(),
    tx.done,
  ])
}

/** 删除会话，仅清理已无会话引用的本地原件；远端文件不删。 */
export const deleteSession = async (sessionId: string): Promise<void> => {
  const tx = (await getDB()).transaction(['sessions', 'sessionSummaries', 'files'], 'readwrite')
  await Promise.all([
    (async () => {
      try {
        const summaries = tx.objectStore('sessionSummaries')
        const summary = await summaries.get(sessionId)
        await tx.objectStore('sessions').delete(sessionId)
        await summaries.delete(sessionId)
        for (const id of summary?.fileIds ?? []) {
          if ((await summaries.index('fileIds').count(id)) === 0) {
            await tx.objectStore('files').delete(id)
          }
        }
      } catch (error) {
        abortTransaction(tx)
        throw error
      }
    })(),
    tx.done,
  ])
}

const putFiles = async (store: 'files' | 'filesStaging', files: StoredFile[]) => {
  const tx = (await getDB()).transaction(store, 'readwrite')
  await Promise.all([...files.map((file) => tx.store.put(file)), tx.done])
}

export const saveFiles = (files: StoredFile[]): Promise<void> => putFiles('files', files)

export const loadFile = async (id: string): Promise<Blob | undefined> =>
  (await (await getDB()).get('files', id))?.blob

/** 清空导入暂存：开始导入前清除上次中断（如关闭页面）遗留的数据，导入失败后清除本次写入。 */
export const clearStaging = async (): Promise<void> => {
  const tx = (await getDB()).transaction(['sessionsStaging', 'filesStaging'], 'readwrite')
  await Promise.all([
    tx.objectStore('sessionsStaging').clear(),
    tx.objectStore('filesStaging').clear(),
    tx.done,
  ])
}

/** 批量写入暂存会话：一次事务写完全部会话，避免每个会话一次独立事务。 */
export const addStagingSessions = async (sessions: Session[]): Promise<void> => {
  if (!sessions.length) {
    return
  }
  const tx = (await getDB()).transaction('sessionsStaging', 'readwrite')
  for (const session of sessions) {
    void tx.store.put(session)
  }
  await tx.done
}

export const saveStagingFiles = (files: StoredFile[]): Promise<void> =>
  putFiles('filesStaging', files)

/** replace：整包替换（清空历史）；merge：按会话 ID 合并，保留本地多出来的消息。 */
export type CommitMode = 'replace' | 'merge'

export type CommitResult = { summaries: SessionSummary[]; added: number; updated: number }

/** 同一次导入重复执行时，用导出包的标题与时间补齐，消息取并集，不新建会话。 */
const mergeSession = (local: Session, incoming: Session): Session => {
  const known = new Set(local.messages.map((message) => message.id))
  const extra = incoming.messages.filter((message) => !known.has(message.id))
  return {
    ...local,
    ...incoming,
    messages: [...local.messages, ...extra].sort((left, right) => left.createdAt - right.createdAt),
  }
}

// 分块读取暂存：块内请求不 await，只 await 读取本身，事务因此不会提前提交。
const STAGING_CHUNK = 200

/**
 * 把暂存写入正式数据并清空暂存。merge 模式下先读出同 ID 的本地会话再合并，
 * 会话、摘要、原件三个存储在同一事务内完成，失败整体回滚。
 */
export const commitStaging = async (mode: CommitMode = 'replace'): Promise<CommitResult> => {
  const db = await getDB()
  const tx = db.transaction(
    ['sessions', 'sessionSummaries', 'files', 'sessionsStaging', 'filesStaging'],
    'readwrite'
  )
  const sessions = tx.objectStore('sessions')
  const summaries = tx.objectStore('sessionSummaries')
  const files = tx.objectStore('files')
  const stagedSessions = tx.objectStore('sessionsStaging')
  const stagedFiles = tx.objectStore('filesStaging')
  let added = 0
  let updated = 0
  try {
    if (mode === 'replace') {
      void sessions.clear()
      void summaries.clear()
      void files.clear()
    }
    for (let lower: string | undefined = undefined; ; ) {
      const batch = await stagedSessions.getAll(
        lower === undefined ? undefined : IDBKeyRange.lowerBound(lower, true),
        STAGING_CHUNK
      )
      if (!batch.length) {
        break
      }
      const locals =
        mode === 'merge' ? await Promise.all(batch.map((item) => sessions.get(item.id))) : []
      for (const [index, session] of batch.entries()) {
        const local = locals[index]
        const merged = local ? mergeSession(local, session) : session
        void sessions.put(merged)
        void summaries.put(storedSummary(merged))
        if (local) {
          updated += 1
        } else {
          added += 1
        }
      }
      lower = batch[batch.length - 1].id
    }
    for (let lower: string | undefined = undefined; ; ) {
      const batch = await stagedFiles.getAll(
        lower === undefined ? undefined : IDBKeyRange.lowerBound(lower, true),
        STAGING_CHUNK
      )
      if (!batch.length) {
        break
      }
      for (const file of batch) {
        void files.put(file)
      }
      lower = batch[batch.length - 1].id
    }
    void stagedSessions.clear()
    void stagedFiles.clear()
    await tx.done
  } catch (error) {
    // 同步抛出的错误不会让事务自动回滚，需显式中止，避免只提交清空和部分移入。
    abortTransaction(tx)
    throw error
  }
  const all = await db.getAll('sessionSummaries')
  return { summaries: all.map(toSessionSummary), added, updated }
}

/** 本地存储失败不打断对话，只在控制台留痕 */
export const reportStorageError = (action: string) => (error: unknown) => {
  // eslint-disable-next-line no-console
  console.error(`[storage] ${action} failed`, error)
}
