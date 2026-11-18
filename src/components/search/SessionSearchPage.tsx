import { useEffect, useMemo, useRef, useState } from 'react'
import { create } from 'zustand'
import { usePredictiveBack } from '../../app/backGesture.js'
import { useTranslate } from '../../i18n/index.js'
import { loadSession } from '../../services/chat/db.js'
import { buildReplyView } from '../../services/chat/view.js'
import { selectSession, useChatStore } from '../../services/chat/store.js'
import { requestScrollToMessage } from '../../services/chat/scrollTarget.js'
import styles from './SessionSearchPage.module.css'

type SearchState = {
  open: boolean
}

const useSearchPage = create<SearchState>(() => ({ open: false }))

export const openSessionSearch = () => useSearchPage.setState({ open: true })
export const closeSessionSearch = () => useSearchPage.setState({ open: false })

type Hit = {
  /** 列表 key（会话 id + 消息序号），不能拿来查会话 */
  id: string
  /** 真正要跳转的会话 id */
  sessionId: string
  /** 命中的消息 id（用于滚动定位） */
  messageId: string
  title: string
  snippet: string
  updatedAt: number
}

const SNIPPET_LIMIT = 46
const BATCH = 8

type MessageLike = { role: string } & Record<string, unknown>

/** 用户消息是纯文本，助手消息要过一遍回复视图才能拿到正文 */
const messageText = (message: MessageLike) => {
  if (message.role === 'user' && typeof message.content === 'string') {
    return message.content
  }
  try {
    return buildReplyView(message as never, false).answer?.text ?? ''
  } catch {
    return ''
  }
}

/** 把命中的关键词加粗，跟官方一样 */
const highlight = (text: string, term: string) => {
  if (!term) {
    return text
  }
  const parts = text.split(new RegExp(`(${term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi'))
  return parts.map((part, index) =>
    part.toLocaleLowerCase() === term ? <b key={index} className={styles.mark}>{part}</b> : part
  )
}

const clock = (value: number) => {
  const date = new Date(value)
  return `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

const ChatGlyph = () => (
  <svg width="21" height="21" viewBox="0 0 24 24" fill="none" aria-hidden="true">
    <path
      d="M4.6 12.4a7.4 7.4 0 0 1 14.8 0v3.9a3 3 0 0 1-3 3h-2.1"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
    />
    <circle cx="12" cy="12.2" r="3.1" stroke="currentColor" strokeWidth="1.7" />
    <path d="M9.4 16.6 8 19.2" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
  </svg>
)

export const SessionSearchPage = () => {
  const t = useTranslate()
  const open = useSearchPage((state) => state.open)
  const sessions = useChatStore((state) => state.sessions)
  const [query, setQuery] = useState('')
  const [hits, setHits] = useState<Hit[]>([])
  const [searching, setSearching] = useState(false)
  const pageRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const textCache = useRef(new Map<string, { id: string; text: string }[]>())

  useEffect(() => {
    if (!open) {
      return
    }
    setQuery('')
    setHits([])
    const timer = window.setTimeout(() => inputRef.current?.focus(), 60)
    return () => window.clearTimeout(timer)
  }, [open])

  usePredictiveBack(pageRef, closeSessionSearch, open)

  const term = query.trim().toLocaleLowerCase()
  const all = useMemo(() => sessions, [sessions])

  useEffect(() => {
    if (!term) {
      setHits([])
      setSearching(false)
      return
    }
    let active = true
    setSearching(true)
    const timer = window.setTimeout(async () => {
      // 每条命中的消息都是一行结果，和官方一致（同一会话可能命中多次）
      const found: Hit[] = []
      for (let offset = 0; offset < all.length; offset += BATCH) {
        const batch = all.slice(offset, offset + BATCH)
        const loaded = await Promise.all(
          batch.map(
            async (summary) =>
              useChatStore.getState().sessionCache[summary.id] ??
              (await loadSession(summary.id).catch(() => undefined))
          )
        )
        if (!active) {
          return
        }
        for (const [row, summary] of batch.entries()) {
          const session = loaded[row]
          const cached = textCache.current.get(summary.id)
          const rows =
            cached ??
            (session?.messages ?? []).map((message) => ({
              id: message.id,
              text: messageText(message),
            }))
          if (!cached && session) {
            textCache.current.set(summary.id, rows)
          }
          const titleHit = summary.title.toLocaleLowerCase().includes(term)
          for (const [index, row] of rows.entries()) {
            const at = row.text.toLocaleLowerCase().indexOf(term)
            if (at < 0) {
              continue
            }
            const snippet = `${at > 14 ? '…' : ''}${row.text.slice(Math.max(0, at - 14), at + SNIPPET_LIMIT)}`
            found.push({
              id: `${summary.id}-${index}`,
              sessionId: summary.id,
              messageId: row.id,
              title: summary.title,
              snippet: snippet.replace(/\s+/g, ' ').trim(),
              updatedAt: summary.updatedAt,
            })
          }
          if (!rows.some((row) => row.text.toLocaleLowerCase().includes(term)) && titleHit) {
            found.push({
              id: `${summary.id}-title`,
              sessionId: summary.id,
              messageId: '',
              title: summary.title,
              snippet: summary.title,
              updatedAt: summary.updatedAt,
            })
          }
        }
        setHits([...found])
      }
      if (active) {
        setSearching(false)
      }
    }, 120)
    return () => {
      active = false
      window.clearTimeout(timer)
    }
  }, [term, all])

  if (!open) {
    return null
  }

  const pick = (hit: Hit) => {
    // 用真实会话 id 跳转；id 是列表 key（会话 id + 消息序号），不能直接当会话 id
    void selectSession(hit.sessionId)
    if (hit.messageId) {
      requestScrollToMessage(hit.sessionId, hit.messageId, query.trim())
    }
    closeSessionSearch()
  }

  return (
    <div className={styles.page} role="dialog" aria-modal="true" ref={pageRef}>
      <div className={styles.bar}>
        <button type="button" className={styles.back} aria-label="返回" onClick={closeSessionSearch}>
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path d="M14.5 5 8 12l6.5 7" stroke="currentColor" strokeWidth="2.1" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
        <div className={styles.field}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <circle cx="10.8" cy="10.8" r="6.4" stroke="currentColor" strokeWidth="1.9" />
            <path d="m15.6 15.6 4.1 4.1" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" />
          </svg>
          <input
            ref={inputRef}
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder={t('androidSearchChats')}
            aria-label={t('androidSearchChats')}
          />
          {query ? (
            <button type="button" className={styles.clear} aria-label="清除" onClick={() => setQuery('')}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <circle cx="12" cy="12" r="9" fill="currentColor" opacity="0.22" />
                <path d="m9.2 9.2 5.6 5.6M14.8 9.2l-5.6 5.6" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" />
              </svg>
            </button>
          ) : null}
        </div>
      </div>

      <div className={styles.results}>
        {hits.map((hit) => (
          <button key={hit.id} type="button" className={styles.hit} onClick={() => pick(hit)}>
            <span className={styles.glyph} aria-hidden="true">
              <ChatGlyph />
            </span>
            <span className={styles.body}>
              <span className={styles.title}>{hit.title}</span>
              <span className={styles.snippet}>{highlight(hit.snippet, term)}</span>
            </span>
            <span className={styles.time}>{clock(hit.updatedAt)}</span>
          </button>
        ))}
        {term && !hits.length && !searching ? (
          <p className={styles.empty}>{t('androidSearchEmpty')}</p>
        ) : null}
      </div>
    </div>
  )
}
