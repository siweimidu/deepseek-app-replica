/** ZIP 解析只依赖「按偏移读一段字节」，File 与远程资源都套用同一层。 */
export type ByteSource = {
  size: number
  read: (start: number, length: number) => Promise<Uint8Array>
}

/** 系统文件选择器返回的 File 可能来自 content URI，切片读取由浏览器代办。 */
export const blobSource = (blob: Blob): ByteSource => ({
  size: blob.size,
  read: async (start, length) => new Uint8Array(await blob.slice(start, start + length).arrayBuffer()),
})
