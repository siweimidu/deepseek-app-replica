import { create } from 'zustand'

/** 需要滚动定位到的消息（由搜索点击设置，消息列表消费） */
type Target = { sessionId: string; messageId: string } | null

export const useScrollTarget = create<{ target: Target }>(() => ({ target: null }))

export const requestScrollToMessage = (sessionId: string, messageId: string) =>
  useScrollTarget.setState({ target: { sessionId, messageId } })

export const clearScrollTarget = () => useScrollTarget.setState({ target: null })
