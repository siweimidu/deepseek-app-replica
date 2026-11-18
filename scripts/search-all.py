"""Search every stored conversation, stream hits in, and keep the drawer transition light."""

import re
from pathlib import Path

PAGE = Path('src/components/search/SessionSearchPage.tsx')
page = PAGE.read_text(encoding='utf-8')

# 1) 去掉扫描与结果数量上限
page = page.replace("const SNIPPET_LIMIT = 46\nconst SCAN_LIMIT = 60", "const SNIPPET_LIMIT = 46\nconst BATCH = 8")
page = page.replace(
    "  const recent = useMemo(() => sessions.slice(0, SCAN_LIMIT), [sessions])",
    "  const all = useMemo(() => sessions, [sessions])",
)

# 2) 文本缓存：同一会话只算一次，连续输入不重复解析
page = page.replace(
    "  const inputRef = useRef<HTMLInputElement>(null)",
    """  const inputRef = useRef<HTMLInputElement>(null)
  const textCache = useRef(new Map<string, string>())""",
)

# 3) 分批并行扫描 + 增量出结果（不再截断）
start = page.index('    const timer = window.setTimeout(async () => {')
end = page.index('    }, 120)', start)
BODY = """    const timer = window.setTimeout(async () => {
      // 所有会话都要扫到；按批并行，命中一条就立刻显示一条
      const found: Hit[] = []
      for (let offset = 0; offset < all.length; offset += BATCH) {
        const batch = all.slice(offset, offset + BATCH)
        const loaded = await Promise.all(
          batch.map(
            async (summary) =>
              useChatStore.getState().sessionCache[summary.id] ??
              (await loadSession(summary.id).catch(() => undefined))
          )
        )
        if (!active) {
          return
        }
        for (const [row, summary] of batch.entries()) {
          const cached = textCache.current.get(summary.id)
          const session = loaded[row]
          const haystack =
            cached ??
            (session ? session.messages.map((message) => messageText(message)).join('\\n') : '')
          if (!cached && session) {
            textCache.current.set(summary.id, haystack)
          }
          const titleHit = summary.title.toLocaleLowerCase().includes(term)
          const bodyHit = haystack.toLocaleLowerCase().includes(term)
          if (!titleHit && !bodyHit) {
            continue
          }
          const at = haystack.toLocaleLowerCase().indexOf(term)
          const snippet =
            at >= 0
              ? `${at > 12 ? '…' : ''}${haystack.slice(Math.max(0, at - 12), at + SNIPPET_LIMIT)}`
              : summary.title
          found.push({
            id: summary.id,
            title: summary.title,
            snippet: snippet.replace(/\\s+/g, ' ').trim(),
            updatedAt: summary.updatedAt,
          })
        }
        setHits([...found])
      }
      if (active) {
        setSearching(false)
      }
"""
page = page[:start] + BODY + page[end:]
page = page.replace("  }, [term, recent])", "  }, [term, all])")
PAGE.write_text(page, encoding='utf-8')
print('search scans everything and streams hits')

# 4) 抽屉/对话切换更快：短过渡 + 结束即撤掉裁剪层
MOTION = Path('src/app/motion.css')
motion = MOTION.read_text(encoding='utf-8')
motion = re.sub(
    r"--motion-drawer:\s*\n?\s*220ms[^;]*;",
    "--motion-drawer: 170ms linear(0, 0.42 10%, 0.85 24%, 0.98 38%, 1.01 52%, 1.004 70%, 1);",
    motion,
)
MOTION.write_text(motion, encoding='utf-8')
print('drawer transition 220ms -> 170ms')

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 28', gradle), encoding='utf-8')
print('versionCode 28')
