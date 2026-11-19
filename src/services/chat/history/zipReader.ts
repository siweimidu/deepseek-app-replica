import { inflateInWorker } from './inflateWorker.js'
import { blobSource, type ByteSource } from './source.js'

// 文件读取与解压的分块：一次读 1 MiB，解压时同样按 1 MiB 喂给 fflate。
// 早先 8 KiB 的粒度会把一次导入切成上千次 async 往返，是导入缓慢的主因。
const READ_CHUNK_BYTES = 1024 * 1024
const INFLATE_CHUNK_BYTES = 1024 * 1024

/** ZIP 结构损坏或使用了不支持的特性 */
export class ArchiveError extends Error {
  constructor() {
    super('Invalid or unsupported history archive')
    this.name = 'ArchiveError'
  }
}

const invalid = (): never => {
  throw new ArchiveError()
}

const asSource = (input: File | ByteSource): ByteSource =>
  typeof (input as ByteSource).read === 'function' ? (input as ByteSource) : blobSource(input as File)

/** 本地文件头签名 PK\x03\x04，用于在解析前区分 ZIP 与其他文件。 */
export const isZipFile = async (input: File | ByteSource) => {
  const source = asSource(input)
  if (source.size < 4) {
    return false
  }
  const bytes = await source.read(0, 4)
  return bytes.length === 4 && bytes.every((byte, index) => byte === [0x50, 0x4b, 3, 4][index])
}

const viewOf = (bytes: Uint8Array) => new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength)

const crcTable = Uint32Array.from({ length: 256 }, (_, value) => {
  let crc = value
  for (let bit = 0; bit < 8; bit++) {
    crc = (crc >>> 1) ^ (crc & 1 ? 0xedb88320 : 0)
  }
  return crc >>> 0
})

const crc32 = (bytes: Uint8Array) => {
  const table = crcTable
  let crc = 0xffffffff
  for (let index = 0; index < bytes.length; index++) {
    crc = (crc >>> 8) ^ table[(crc ^ bytes[index]) & 0xff]
  }
  return (crc ^ 0xffffffff) >>> 0
}

// 复用相邻读取，避免逐个 ZIP 字段都发起一次切片读取。
const createReader = (source: ByteSource) => {
  let offset = 0
  let buffer: Uint8Array = new Uint8Array()
  return async (start: number, length: number) => {
    if (start < 0 || length < 0 || start + length > source.size) {
      invalid()
    }
    if (length === 0) {
      return buffer.subarray(0, 0)
    }
    if (start < offset || start + length > offset + buffer.length) {
      const end = Math.min(source.size, start + Math.max(READ_CHUNK_BYTES, length))
      buffer = await source.read(start, end - start)
      if (buffer.length !== end - start) {
        invalid()
      }
      offset = start
    }
    return buffer.subarray(start - offset, start - offset + length)
  }
}

type ReadBytes = ReturnType<typeof createReader>

/** ZIP64、分卷与加密文件不属于导出格式，一律拒绝。 */
const checkExtra = (bytes: Uint8Array) => {
  const view = viewOf(bytes)
  let offset = 0
  while (offset < bytes.length) {
    if (offset + 4 > bytes.length || view.getUint16(offset, true) === 1) {
      invalid()
    }
    offset += 4 + view.getUint16(offset + 2, true)
    if (offset > bytes.length) {
      invalid()
    }
  }
}

const decodePath = (bytes: Uint8Array, flags: number) => {
  // 非 UTF-8 编码的 ZIP 文件名仅接受 ASCII，确保附件路径解码准确。
  if (!(flags & 0x800) && bytes.some((byte) => byte > 0x7f)) {
    invalid()
  }
  const path = new TextDecoder('utf-8', { fatal: true }).decode(bytes).normalize('NFC')
  if (!path || path.includes('\\') || path.includes('\0') || /^[A-Za-z]:/.test(path)) {
    invalid()
  }
  const parts = (path.endsWith('/') ? path.slice(0, -1) : path).split('/')
  if (parts.some((part) => !part || part === '.' || part === '..')) {
    invalid()
  }
  return path
}

type Entry = {
  path: string
  name: Uint8Array
  flags: number
  method: number
  crc: number
  compressedSize: number
  size: number
  offset: number
}

const readDirectory = async (
  source: ByteSource,
  readBytes: ReadBytes
): Promise<{ entries: Entry[]; offset: number }> => {
  const fileSize = source.size
  if (fileSize < 22) {
    invalid()
  }
  const tailStart = Math.max(0, fileSize - 22 - 0xffff)
  const tail = await readBytes(tailStart, fileSize - tailStart)
  const tailView = viewOf(tail)
  let end = tail.length - 22
  while (
    end >= 0 &&
    (tailView.getUint32(end, true) !== 0x06054b50 ||
      end + 22 + tailView.getUint16(end + 20, true) !== tail.length)
  ) {
    end--
  }
  if (end < 0) {
    invalid()
  }
  const count = tailView.getUint16(end + 10, true)
  const size = tailView.getUint32(end + 12, true)
  const offset = tailView.getUint32(end + 16, true)
  if (
    tailView.getUint16(end + 4, true) !== 0 ||
    tailView.getUint16(end + 6, true) !== 0 ||
    tailView.getUint16(end + 8, true) !== count ||
    count === 0xffff ||
    size === 0xffffffff ||
    offset === 0xffffffff ||
    offset + size !== tailStart + end
  ) {
    invalid()
  }
  const entries: Entry[] = []
  const paths = new Set<string>()
  let cursor = 0
  for (let index = 0; index < count; index++) {
    if (cursor + 46 > size) {
      invalid()
    }
    const view = viewOf(await readBytes(offset + cursor, 46))
    if (view.getUint32(0, true) !== 0x02014b50) {
      invalid()
    }
    const flags = view.getUint16(8, true)
    const method = view.getUint16(10, true)
    const compressedSize = view.getUint32(20, true)
    const entrySize = view.getUint32(24, true)
    const nameLength = view.getUint16(28, true)
    const extraLength = view.getUint16(30, true)
    const next = cursor + 46 + nameLength + extraLength + view.getUint16(32, true)
    const entryOffset = view.getUint32(42, true)
    // 只允许 deflate 选项、data descriptor 与 UTF-8 标志。
    if (
      flags & ~0x80e ||
      (method !== 0 && method !== 8) ||
      compressedSize === 0xffffffff ||
      entrySize === 0xffffffff ||
      (method === 0 && compressedSize !== entrySize) ||
      entryOffset >= offset ||
      view.getUint16(34, true) !== 0 ||
      ((view.getUint32(38, true) >>> 16) & 0xf000) === 0xa000 ||
      next > size
    ) {
      invalid()
    }
    const name = await readBytes(offset + cursor + 46, nameLength)
    const path = decodePath(name, flags)
    // 目录和同名文件也不能互相覆盖。
    const identity = path.endsWith('/') ? path.slice(0, -1) : path
    if (paths.has(identity) || (path.endsWith('/') && entrySize !== 0)) {
      invalid()
    }
    paths.add(identity)
    checkExtra(await readBytes(offset + cursor + 46 + nameLength, extraLength))
    entries.push({
      path,
      name,
      flags,
      method,
      crc: view.getUint32(16, true),
      compressedSize,
      size: entrySize,
      offset: entryOffset,
    })
    cursor = next
  }
  if (cursor !== size) {
    invalid()
  }
  return { entries: entries.sort((a, b) => a.offset - b.offset), offset }
}

const readEntryOffset = async (readBytes: ReadBytes, entry: Entry, boundary: number) => {
  if (entry.offset + 30 > boundary) {
    invalid()
  }
  const view = viewOf(await readBytes(entry.offset, 30))
  const nameLength = view.getUint16(26, true)
  const extraLength = view.getUint16(28, true)
  const start = entry.offset + 30 + nameLength + extraLength
  const end = start + entry.compressedSize
  if (
    view.getUint32(0, true) !== 0x04034b50 ||
    view.getUint16(6, true) !== entry.flags ||
    view.getUint16(8, true) !== entry.method ||
    nameLength !== entry.name.length ||
    end > boundary
  ) {
    invalid()
  }
  for (const [position, expected] of [
    [14, entry.crc],
    [18, entry.compressedSize],
    [22, entry.size],
  ]) {
    const actual = view.getUint32(position, true)
    if (actual !== expected && (!(entry.flags & 8) || actual !== 0)) {
      invalid()
    }
  }
  const metadata = await readBytes(entry.offset + 30, nameLength + extraLength)
  if (entry.name.some((byte, index) => byte !== metadata[index])) {
    invalid()
  }
  checkExtra(metadata.subarray(nameLength))
  if (entry.flags & 8) {
    if (end + 12 > boundary) {
      invalid()
    }
    const descriptor = viewOf(await readBytes(end, Math.min(16, boundary - end)))
    const shift = descriptor.getUint32(0, true) === 0x08074b50 ? 4 : 0
    if (
      shift + 12 > descriptor.byteLength ||
      descriptor.getUint32(shift, true) !== entry.crc ||
      descriptor.getUint32(shift + 4, true) !== entry.compressedSize ||
      descriptor.getUint32(shift + 8, true) !== entry.size
    ) {
      invalid()
    }
  }
  return start
}

export type ArchiveEntry = {
  path: string
  size: number
  /** 读完整个条目：精确分配缓冲区，一次 CRC 校验。不需要的条目不必调用。 */
  bytes: () => Promise<Uint8Array>
}

/** 条目在归档中的体积，用于把进度按字节加权（图片占绝大部分）。 */
export type ArchiveTotals = { entries: number; bytes: number }

/** 只读中央目录，得到条目数与解压后总字节数；用于进度条分母。 */
export const summarizeArchive = async (input: File | ByteSource): Promise<ArchiveTotals> => {
  const source = asSource(input)
  const directory = await readDirectory(source, createReader(source))
  return {
    entries: directory.entries.length,
    bytes: directory.entries.reduce((total, entry) => total + entry.size, 0),
  }
}

const readEntryBytes = async (
  readBytes: ReadBytes,
  entry: Entry,
  start: number
): Promise<Uint8Array> => {
  const output = new Uint8Array(entry.size)
  let written = 0
  const append = (chunk: Uint8Array) => {
    if (written + chunk.length > output.length) {
      invalid()
    }
    output.set(chunk, written)
    written += chunk.length
  }
  if (entry.method === 0) {
    for (let offset = 0; offset < entry.compressedSize; offset += READ_CHUNK_BYTES) {
      append(
        await readBytes(start + offset, Math.min(READ_CHUNK_BYTES, entry.compressedSize - offset))
      )
    }
  } else {
    // 解压放到 worker：大包（几十 MB）不会再卡住主线程的滚动与点击。
    // 同一份 worker 全程复用，避免按条目反复创建。
    const compressed: Uint8Array[] = []
    const totalChunks = Math.max(1, Math.ceil(entry.compressedSize / INFLATE_CHUNK_BYTES))
    for (let index = 0; index < totalChunks; index += 1) {
      const offset = index * INFLATE_CHUNK_BYTES
      const size = Math.min(INFLATE_CHUNK_BYTES, entry.compressedSize - offset)
      if (size <= 0) {
        continue
      }
      compressed.push(await readBytes(start + offset, size))
    }
    const inflated = await inflateInWorker(compressed)
    if (inflated.length) {
      append(inflated)
    }
  }
  if (written !== entry.size || crc32(output) !== entry.crc) {
    invalid()
  }
  return output
}

/**
 * 按条目在文件中的物理顺序逐条产出；条目数据在调用 bytes() 时才解压，
 * 因此跳过不关心的条目不再需要先下载并解压一遍。
 */
export async function* readArchive(input: File | ByteSource): AsyncGenerator<ArchiveEntry> {
  const source = asSource(input)
  const readBytes = createReader(source)
  const directory = await readDirectory(source, readBytes)
  for (const [index, entry] of directory.entries.entries()) {
    if (entry.path.endsWith('/')) {
      continue
    }
    const boundary = directory.entries[index + 1]?.offset ?? directory.offset
    const start = await readEntryOffset(readBytes, entry, boundary)
    yield {
      path: entry.path,
      size: entry.size,
      bytes: () => readEntryBytes(readBytes, entry, start),
    }
  }
}

/** 读出整个条目为 Blob：会话 JSON 需要完整解析，图片需要整张保存。 */
export const readEntry = async (entry: ArchiveEntry): Promise<Blob> => {
  const bytes = await entry.bytes()
  return new Blob([bytes as Uint8Array<ArrayBuffer>])
}
