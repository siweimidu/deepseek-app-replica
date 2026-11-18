import { create } from 'zustand'

/** 语音通话整屏：由聊天页顶栏的电话按钮打开 */
export const useVoiceCall = create(() => ({ open: false }))

export const openVoiceCall = () => useVoiceCall.setState({ open: true })

export const closeVoiceCall = () => useVoiceCall.setState({ open: false })
