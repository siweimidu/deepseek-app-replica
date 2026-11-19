import { create } from 'zustand'

/** 全屏看图：同一时间只有一张 */
type ViewerState = {
  open: boolean
  src: string | null
  /** 便于返回时还原滚动位置等场景使用 */
  origin: string | null
}

export const useImageViewer = create<ViewerState>(() => ({ open: false, src: null, origin: null }))

export const openImageViewer = (src: string, origin?: string) =>
  useImageViewer.setState({ open: true, src, origin: origin ?? null })

export const closeImageViewer = () =>
  useImageViewer.setState({ open: false, src: null, origin: null })
