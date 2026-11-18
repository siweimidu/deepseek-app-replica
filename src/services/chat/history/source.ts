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

const parseContentRange = (header: string | null) => {
  const match = header && /\/(\d+)\s*$/.exec(header)
  return match ? Number(match[1]) : null
}

/**
 * 通过 Range 请求读取远端 ZIP。Android 端的下载器把文件落到缓存后
 * 以 appassets 同源地址暴露，因此这里不必依赖目标站点的 CORS 头。
 */
export const rangeSource = async (url: string): Promise<ByteSource> => {
  const probe = await fetch(url, { headers: { Range: 'bytes=0-0' } })
  if (!probe.ok) {
    throw new Error(`download failed: ${probe.status}`)
  }
  await probe.arrayBuffer()
  const size =
    probe.status === 206
      ? parseContentRange(probe.headers.get('Content-Range'))
      : Number(probe.headers.get('Content-Length'))
  if (!size || !Number.isFinite(size)) {
    throw new Error('download failed: unknown size')
  }
  return {
    size,
    read: async (start, length) => {
      const response = await fetch(url, { headers: { Range: `bytes=${start}-${start + length - 1}` } })
      if (response.status !== 206) {
        throw new Error('download failed: range unsupported')
      }
      return new Uint8Array(await response.arrayBuffer())
    },
  }
}
