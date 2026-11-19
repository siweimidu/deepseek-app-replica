/**
 * 图片裁剪：只做「把原图的一块矩形抠出来」这一件事。
 * 坐标一律用**源图像素**，显示尺寸的换算交给界面层。
 */

export type CropRect = { x: number; y: number; width: number; height: number }

export const clampRect = (rect: CropRect, width: number, height: number): CropRect => {
  const clampedWidth = Math.min(rect.width, width)
  const clampedHeight = Math.min(rect.height, height)
  return {
    x: Math.min(Math.max(0, rect.x), width - clampedWidth),
    y: Math.min(Math.max(0, rect.y), height - clampedHeight),
    width: clampedWidth,
    height: clampedHeight,
  }
}

const loadImage = (src: string) =>
  new Promise<HTMLImageElement>((resolve, reject) => {
    const image = new Image()
    image.onload = () => resolve(image)
    image.onerror = () => reject(new Error('image decode failed'))
    image.src = src
  })

const readFileAsUrl = (file: File) =>
  new Promise<string>((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result))
    reader.onerror = () => reject(new Error('read failed'))
    reader.readAsDataURL(file)
  })

export const loadSource = async (input: File | string) =>
  loadImage(typeof input === 'string' ? input : await readFileAsUrl(input))

/**
 * 按源图像素矩形裁剪，并保证长边不超过 maxEdge。
 * 返回 JPEG/PNG 的 File（PNG 源保持 PNG，其余走 JPEG）。
 */
export const cropToFile = async (
  source: HTMLImageElement,
  rect: CropRect,
  options?: { fileName?: string; maxEdge?: number; quality?: number }
): Promise<File> => {
  const maxEdge = options?.maxEdge ?? 2048
  const quality = options?.quality ?? 0.9
  const safe = clampRect(rect, source.naturalWidth, source.naturalHeight)
  const width = Math.max(1, Math.round(safe.width))
  const height = Math.max(1, Math.round(safe.height))
  const scale = Math.min(1, maxEdge / Math.max(width, height))
  const canvas = document.createElement('canvas')
  canvas.width = Math.max(1, Math.round(width * scale))
  canvas.height = Math.max(1, Math.round(height * scale))
  const context = canvas.getContext('2d')
  if (!context) {
    throw new Error('canvas unavailable')
  }
  context.drawImage(
    source,
    Math.round(safe.x),
    Math.round(safe.y),
    Math.round(safe.width),
    Math.round(safe.height),
    0,
    0,
    canvas.width,
    canvas.height
  )
  const isPng = options?.fileName?.toLowerCase().endsWith('.png')
  const type = isPng ? 'image/png' : 'image/jpeg'
  const blob = await new Promise<Blob | null>((resolve) => {
    canvas.toBlob(resolve, type, quality)
  })
  if (!blob) {
    throw new Error('encode failed')
  }
  const base = (options?.fileName ?? 'crop').replace(/\.[^.]+$/, '')
  const ext = isPng ? 'png' : 'jpg'
  return new File([blob], `${base}-crop.${ext}`, { type, lastModified: Date.now() })
}
