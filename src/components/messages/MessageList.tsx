import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'
import { useIsMobile } from '../../app/viewport.js'
import {
  buildMessageVersions,
  getVisibleMessages,
  type MessageVersions,
} from '../../services/chat/branches.js'
import { selectMessageVersion } from '../../services/chat/store.js'
import { clearScrollTarget, useScrollTarget } from '../../services/chat/scrollTarget.js'
import type { Session } from '../../services/chat/types.js'
import { closeSearchPanel } from '../search/searchPanelState.js'
import { AssistantMessage } from './AssistantMessage.js'
import { ScrollToBottomContext } from './scrollContext.js'
import { UserMessage } from './UserMessage.js'
import type { Message } from '../../services/chat/types.js'

/**
 * 会话共用可重试的附件上传失败入口，覆盖当前提问与历史消息中的附件。
 * 点击后按失败的回答重新补传附件并请求。
 */
const getUploadRetryId = (messages: Message[], streaming: boolean) => {
  const last = messages.at(-1)
  return !streaming &&
    last?.role === 'assistant' &&
    last.status === 'error' &&
    last.error?.kind === 'upload' &&
    last.error.retryable
    ? last.id
    : null
}
import styles from './MessageList.module.css'

/** 距底部小于该值时视为在底部，流式内容增长时跟随 */
const STICKY_THRESHOLD = 40
const EMPTY_VERSIONS: MessageVersions = { ids: [], index: -1 }

export const MessageList = ({
  session,
  streaming,
  footer,
}: {
  session: Session
  streaming: boolean
  footer: React.ReactNode
}) => {
  const isMobile = useIsMobile()
  const scrollRef = useRef<HTMLDivElement>(null)
  const contentRef = useRef<HTMLDivElement>(null)
  const stickyRef = useRef(true)
  const scrollTopRef = useRef(0)
  const restoreScrollRef = useRef<{ messageId: string; top: number } | null>(null)
  const messages = getVisibleMessages(session)
  const [previousVersions, setPreviousVersions] = useState(() =>
    buildMessageVersions(session, new Map())
  )
  const versions = useMemo(
    () => buildMessageVersions(session, previousVersions),
    [session, previousVersions]
  )
  if (versions !== previousVersions) {
    setPreviousVersions(versions)
  }
  const lastMessageId = messages.at(-1)?.id
  const scrollToBottom = useCallback(() => {
    const el = scrollRef.current
    if (el && stickyRef.current) {
      el.scrollTop = el.scrollHeight
      scrollTopRef.current = el.scrollTop
    }
  }, [])
  const stopFollowing = useCallback(() => {
    stickyRef.current = false
  }, [])
  const scrollControls = useMemo(
    () => ({ scrollToBottom, stopFollowing }),
    [scrollToBottom, stopFollowing]
  )

  // 内容、键盘和输入框高度变化时，继续遵循当前跟随状态。
  useLayoutEffect(() => {
    const content = contentRef.current
    const scroll = scrollRef.current
    if (!content || !scroll) {
      return
    }
    const observer = new ResizeObserver(scrollToBottom)
    observer.observe(content)
    observer.observe(scroll)
    return () => observer.disconnect()
  }, [isMobile, scrollToBottom])

  // 切换版本后将选择器留在原位置，避免回答长短变化导致操作区跳出视口。
  // 订阅跳转目标：同一会话里再次搜索时，deps 可能不变，必须靠它触发
  const scrollTarget = useScrollTarget((state) => state.target)

  useLayoutEffect(() => {
    const anchor = restoreScrollRef.current
    const scroll = scrollRef.current
    if (anchor && scroll) {
      const switcher = scroll.querySelector<HTMLElement>(
        `[data-message-version="${CSS.escape(anchor.messageId)}"]`
      )
      if (switcher) {
        scroll.scrollTop += switcher.getBoundingClientRect().top - anchor.top
      }
      restoreScrollRef.current = null
      return
    }
    // 搜索点击后：滚到关键词所在的**那段文字**，并把关键词标出来
    if (scrollTarget && scrollTarget.sessionId === session.id && scroll) {
      const scroller = scroll
      const { messageId, term } = scrollTarget
      stickyRef.current = false
      clearScrollTarget()

      /** 在消息里找到关键词对应的 Range（跨节点也能定位） */
      const findRange = (root: HTMLElement): Range | null => {
        if (!term) {
          return null
        }
        const needle = term.toLocaleLowerCase()
        const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT)
        const nodes: { node: Text; start: number }[] = []
        let text = ''
        let current: Node | null = walker.nextNode()
        while (current) {
          const textNode = current as Text
          nodes.push({ node: textNode, start: text.length })
          text += textNode.data
          current = walker.nextNode()
        }
        const index = text.toLocaleLowerCase().indexOf(needle)
        if (index < 0 || nodes.length === 0) {
          return null
        }
        const locate = (offset: number) => {
          for (let i = nodes.length - 1; i >= 0; i -= 1) {
            if (offset >= nodes[i].start) {
              return { node: nodes[i].node, offset: offset - nodes[i].start }
            }
          }
          return { node: nodes[0].node, offset: 0 }
        }
        const from = locate(index)
        const to = locate(index + needle.length)
        const range = document.createRange()
        try {
          range.setStart(from.node, Math.min(from.offset, from.node.data.length))
          range.setEnd(to.node, Math.min(to.offset, to.node.data.length))
        } catch {
          return null
        }
        return range
      }

      /** 用 CSS Highlight API 标出关键词（不支持就跳过，不影响定位） */
      const highlight = (range: Range) => {
        const api = (window as unknown as { CSS?: { highlights?: Map<string, unknown> }; Highlight?: unknown })
        if (!api.CSS?.highlights || !api.Highlight) {
          return
        }
        try {
          api.CSS.highlights.set('dsh-search-hit', new (api.Highlight as new (r: Range) => unknown)(range))
          window.setTimeout(() => api.CSS?.highlights?.delete('dsh-search-hit'), 2600)
        } catch {
          // 忽略
        }
      }

      const anchorRect = () => {
        const node = scroller.querySelector<HTMLElement>(
          `[data-message-id="${CSS.escape(messageId)}"]`
        )
        if (!node) {
          return null
        }
        const range = findRange(node)
        if (range) {
          highlight(range)
          const box = range.getBoundingClientRect()
          if (box.height > 0) {
            return { rect: box, node }
          }
        }
        return { rect: node.getBoundingClientRect(), node }
      }

      const align = () => {
        if (!scroller.isConnected) {
          return
        }
        const found = anchorRect()
        if (!found) {
          return
        }
        if (!found.node.classList.contains(styles.flash)) {
          found.node.classList.add(styles.flash)
          window.setTimeout(() => found.node.classList.remove(styles.flash), 2000)
        }
        const box = scroller.getBoundingClientRect()
        const { rect } = found
        // 让关键词落在视口中部偏上（1/3 处），确保它一定可见
        const desired = box.top + box.height * 0.32
        const top = scroller.scrollTop + (rect.top - desired)
        const max = scroller.scrollHeight - scroller.clientHeight
        const next = Math.max(0, Math.min(max, top))
        if (Math.abs(scroller.scrollTop - next) > 2) {
          scroller.scrollTo({ top: next, behavior: 'smooth' })
          scrollTopRef.current = next
        }
      }

      ;[0, 80, 200, 400, 700, 1100, 1600].forEach((delay) => window.setTimeout(align, delay))
    }
    stickyRef.current = true
    scrollToBottom()
    return undefined
  }, [session.id, lastMessageId, scrollToBottom, scrollTarget])

  useEffect(closeSearchPanel, [session.id, lastMessageId])

  const selectVersion = useCallback(
    (messageId: string, anchorTop: number) => {
      if (streaming) {
        return
      }
      restoreScrollRef.current = { messageId, top: anchorTop }
      stickyRef.current = false
      closeSearchPanel()
      selectMessageVersion(session.id, messageId)
    },
    [session.id, streaming]
  )

  // 跨移动端断点时切换滚动层，并保持输入框及当前阅读位置。
  useLayoutEffect(() => {
    const el = scrollRef.current
    if (!el) {
      return
    }
    if (stickyRef.current) {
      scrollToBottom()
    } else {
      el.scrollTop = scrollTopRef.current
    }
    const onScroll = () => {
      const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < STICKY_THRESHOLD
      // 仅在用户向上滚动时停止跟随底部，布局或内容增高时保持跟随状态。
      if (nearBottom) {
        stickyRef.current = true
      } else if (el.scrollTop < scrollTopRef.current) {
        stickyRef.current = false
      }
      scrollTopRef.current = el.scrollTop
    }
    el.addEventListener('scroll', onScroll, { passive: true })
    return () => el.removeEventListener('scroll', onScroll)
  }, [isMobile, scrollToBottom])

  const lastIndex = messages.length - 1
  const uploadRetryId = getUploadRetryId(messages, streaming)
  return (
    <ScrollToBottomContext.Provider value={scrollControls}>
      <div ref={isMobile ? undefined : scrollRef} className={styles.container}>
        <div ref={isMobile ? scrollRef : undefined} className={styles.scroll}>
          <div ref={contentRef} className={styles.column}>
            {messages.map((message, index) =>
              message.role === 'user' ? (
                <UserMessage
                  key={message.id}
                  sessionId={session.id}
                  message={message}
                  retryUploadId={uploadRetryId}
                  isFirst={index === 0}
                  isLast={index === lastIndex || index === lastIndex - 1}
                  busy={streaming}
                  versions={versions.get(message.id) ?? EMPTY_VERSIONS}
                  onSelectVersion={selectVersion}
                />
              ) : (
                <AssistantMessage
                  key={message.id}
                  sessionId={session.id}
                  message={message}
                  isLast={index === lastIndex}
                  streaming={streaming && index === lastIndex}
                  busy={streaming}
                  versions={versions.get(message.id) ?? EMPTY_VERSIONS}
                  onSelectVersion={selectVersion}
                />
              )
            )}
          </div>
        </div>
        {footer}
      </div>
    </ScrollToBottomContext.Provider>
  )
}
