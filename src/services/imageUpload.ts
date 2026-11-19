/**
 * 发图前的压缩管线（参考上游 imageUpload 的思路）
 *
 * 手机直出的照片动辄 4000×3000、8MB 以上，直接上传会：
 * 1. 占用很大上行带宽，弱网下等到超时
 * 2. 顶到服务端体积上限，直接返回失败
 *
 * 所以超过阈值就先在本地缩到长边 2048 再压一次；
 * 已经够小的图原样返回，不做任何二次编码。
 */

/** 长边上限 */
const MAX_EDGE = 2048
/** 超过这个体积才处理 */
const MAX_BYTES = 2.5 * 1024 * 1024
/** JPEG/WebP 质量 */
const QUALITY = 0.86

const loadBitmap = async (file: File): Promise<ImageBitmap | HTMLImageElement> => {
  if (typeof createImageBitmap === 'function') {
    try {
      return await createImageBitmap(file, { imageOrientation: 'from-image' })
    } catch {
      // 老 WebView 不支持参数或格式，退回 <img>
    }
  }
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file)
    const image = new Image()
    image.onload = () => {
      URL.revokeObjectURL(url)
      resolve(image)
    }
    image.onerror = () => {
      URL.revokeObjectURL(url)
      reject(new Error('image decode failed'))
    }
    image.src = url
  })
}

const sizeOf = (source: ImageBitmap | HTMLImageElement) =>
  source instanceof HTMLImageElement
    ? { width: source.naturalWidth, height: source.naturalHeight }
    : { width: source.width, height: source.height }

/** 需要压缩吗：GIF 与 SVG 不碰（会丢帧或破坏矢量） */
export const needsCompress = (file: File) =>
  file.type.startsWith('image/') &&
  file.type !== 'image/gif' &&
  file.type !== 'image/svg+xml' &&
  file.size > MAX_BYTES

/**
 * 返回可用于上传的文件。
 * 不需要压缩、或压缩后反而变大时，原样返回同一个 File。
 */
export const compressImage = async (file: File): Promise<File> => {
  if (!needsCompress(file)) {
    return file
  }
  try {
    const source = await loadBitmap(file)
    const { width, height } = sizeOf(source)
    if (!width || !height) {
      return file
    }
    const scale = Math.min(1, MAX_EDGE / Math.max(width, height))
    const canvas = document.createElement('canvas')
    canvas.width = Math.max(1, Math.round(width * scale))
    canvas.height = Math.max(1, Math.round(height * scale))
    const context = canvas.getContext('2d')
    if (!context) {
      return file
    }
    context.drawImage(source as CanvasImageSource, 0, 0, canvas.width, canvas.height)
    if (source instanceof ImageBitmap) {
      source.close()
    }
    // PNG 保留 PNG（可能有透明），其余统一走 JPEG；WebP 原样保留 WebP
    const targetType =
      file.type === 'image/png' ? 'image/png' : file.type === 'image/webp' ? 'image/webp' : 'image/jpeg'
    const blob = await new Promise<Blob | null>((resolve) => {
      canvas.toBlob(resolve, targetType, QUALITY)
    })
    if (!blob || blob.size >= file.size) {
      return file
    }
    const base = file.name.replace(/\.[^.]+$/, '')
    const ext = targetType === 'image/png' ? 'png' : targetType === 'image/webp' ? 'webp' : 'jpg'
    return new File([blob], `${base}.${ext}`, { type: targetType, lastModified: Date.now() })
  } catch {
    return file
  }
}
