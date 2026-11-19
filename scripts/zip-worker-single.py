"""zipReader 改用复用单例的 inflate worker（不再每个条目新开 worker）。"""

from pathlib import Path

ZIP = Path('src/services/chat/history/zipReader.ts')
src = ZIP.read_text(encoding='utf-8')

src = src.replace("import { AsyncInflate } from 'fflate'", "import { inflateInWorker } from './inflateWorker.js'", 1)

start = src.index('    // 解压放到 worker：大包（几十 MB）不会再卡住主线程的滚动与点击')
end = src.index('  if (written !== entry.size', start)
NEW = """    // 解压放到 worker：大包（几十 MB）不会再卡住主线程的滚动与点击。
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
"""
src = src[:start] + NEW + src[end:]
ZIP.write_text(src, encoding='utf-8')
print('zipReader uses inflateInWorker:', 'inflateInWorker' in src)

# 顺手：导入结束时释放 worker
JOB = Path('src/services/chat/importJob.ts')
job = JOB.read_text(encoding='utf-8')
if 'disposeInflateWorker' not in job:
    job = job.replace(
        "import type { ImportOutcome } from './store.js'",
        "import { disposeInflateWorker } from './history/inflateWorker.js'\nimport type { ImportOutcome } from './store.js'",
        1,
    )
    job = job.replace(
        "    } finally {\n      running = false\n    }",
        "    } finally {\n      running = false\n      disposeInflateWorker()\n    }",
        1,
    )
    JOB.write_text(job, encoding='utf-8')
print('worker disposed after import:', 'disposeInflateWorker' in job)
