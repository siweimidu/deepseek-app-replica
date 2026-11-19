"""把 ZIP 解压搬到 Web Worker（fflate 的 AsyncInflate 内部就是 worker）。"""

from pathlib import Path

ZIP = Path('src/services/chat/history/zipReader.ts')
src = ZIP.read_text(encoding='utf-8')

src = src.replace("import { Inflate } from 'fflate'", "import { AsyncInflate } from 'fflate'", 1)

OLD = """    const inflate = new Inflate(append)
    for (let offset = 0; offset < entry.compressedSize; offset += INFLATE_CHUNK_BYTES) {
      const end = Math.min(offset + INFLATE_CHUNK_BYTES, entry.compressedSize)
      inflate.push(
        await readBytes(start + offset, end - offset),
        end === entry.compressedSize
      )
      if (entry.compressedSize === 0) {
        break
      }
    }
    if (entry.compressedSize === 0) {
      inflate.push(new Uint8Array(), true)
    }"""
NEW = """    // 解压放到 worker：大包（几十 MB）不会再卡住主线程的滚动与点击
    let inflateError: unknown = null
    const inflate = new AsyncInflate((error: unknown, chunk: Uint8Array) => {
      if (error) {
        inflateError = error
        return
      }
      if (chunk && chunk.length) {
        append(chunk)
      }
    })
    for (let offset = 0; offset < entry.compressedSize; offset += INFLATE_CHUNK_BYTES) {
      const end = Math.min(offset + INFLATE_CHUNK_BYTES, entry.compressedSize)
      inflate.push(
        await readBytes(start + offset, end - offset),
        end === entry.compressedSize
      )
      if (entry.compressedSize === 0) {
        break
      }
    }
    if (entry.compressedSize === 0) {
      inflate.push(new Uint8Array(), true)
    }
    await inflate.terminate()
    if (inflateError) {
      invalid()
    }"""
assert OLD in src, 'inflate block not found'
src = src.replace(OLD, NEW, 1)
ZIP.write_text(src, encoding='utf-8')
print('zip inflate -> worker:', 'AsyncInflate' in src and 'await inflate.terminate()' in src)
