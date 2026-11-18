"""Close on any deliberate left move; enlarge the phone glyph; per-message search hits with highlight."""

import re
from pathlib import Path

# ---------- 1) 抽屉关闭判定改成"位移"而不是"进度" ----------
HOOK = Path('src/components/sider/useAndroidDrawerGesture.ts')
hook = HOOK.read_text(encoding='utf-8')
OLD = """    const flick = event.timeStamp - drag.previousTime < 100 && Math.abs(drag.velocity) > 0.32
    const open = cancelled ? drag.startedOpen : flick ? drag.velocity > 0 : drag.current >= 0.22"""
NEW = """    const flick = event.timeStamp - drag.previousTime < 100 && Math.abs(drag.velocity) > 0.32
    // 用"实际移动了多少像素"判断，而不是进度：轻轻一滑只有 30px，按进度算会被判成保持打开
    const travelled = (drag.current - drag.start) * drag.edge
    const open = cancelled
      ? drag.startedOpen
      : flick
        ? drag.velocity > 0
        : drag.startedOpen
          ? travelled > -24
          : travelled > drag.edge * 0.12"""
assert OLD in hook, 'settle decision not found'
HOOK.write_text(hook.replace(OLD, NEW, 1), encoding='utf-8')
print('drawer closes on a 24px left move')

# ---------- 2) 电话图标放大到和音量/加号一样大 ----------
ICONS = Path('src/components/base/appIcons.tsx')
icons = ICONS.read_text(encoding='utf-8')
icons = icons.replace(
    '    <path d="M6.4 3.2h2.5l1.6 3.9-2 1.3a11.8 11.8 0 0 0 5.1 5.1l1.3-2 3.9 1.6v2.5a2.3 2.3 0 0 1-2.5 2.3A17.2 17.2 0 0 1 4.1 5.7 2.3 2.3 0 0 1 6.4 3.2Z" />',
    '    <g transform="translate(12 12) scale(1.16) translate(-12 -12)">\n      <path d="M6.4 3.2h2.5l1.6 3.9-2 1.3a11.8 11.8 0 0 0 5.1 5.1l1.3-2 3.9 1.6v2.5a2.3 2.3 0 0 1-2.5 2.3A17.2 17.2 0 0 1 4.1 5.7 2.3 2.3 0 0 1 6.4 3.2Z" />\n    </g>',
    1,
)
ICONS.write_text(icons, encoding='utf-8')
print('phone glyph scaled 1.16x')

# ---------- 3) 搜索：每条命中的消息各占一行（官方就是这样） ----------
PAGE = Path('src/components/search/SessionSearchPage.tsx')
page = PAGE.read_text(encoding='utf-8')

page = page.replace(
    """type Hit = {
  id: string
  title: string
  snippet: string
  updatedAt: number
}""",
    """type Hit = {
  id: string
  title: string
  snippet: string
  updatedAt: number
}""",
)

start = page.index('    const timer = window.setTimeout(async () => {')
end = page.index("    }, 120)", start)
BODY = """    const timer = window.setTimeout(async () => {
      // 每条命中的消息都是一行结果，和官方一致（同一会话可能命中多次）
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
          const session = loaded[row]
          const cached = textCache.current.get(summary.id)
          const texts =
            cached !== undefined
              ? cached.split('\\u0000')
              : (session?.messages.map((message) => messageText(message)) ?? [])
          if (cached === undefined) {
            textCache.current.set(summary.id, texts.join('\\u0000'))
          }
          const titleHit = summary.title.toLocaleLowerCase().includes(term)
          for (const [index, text] of texts.entries()) {
            const at = text.toLocaleLowerCase().indexOf(term)
            if (at < 0) {
              continue
            }
            const snippet = `${at > 14 ? '…' : ''}${text.slice(Math.max(0, at - 14), at + SNIPPET_LIMIT)}`
            found.push({
              id: `${summary.id}-${index}`,
              title: summary.title,
              snippet: snippet.replace(/\\s+/g, ' ').trim(),
              updatedAt: summary.updatedAt,
            })
          }
          // 只有标题命中、正文没命中时也给一行，方便找到
          if (!texts.some((text) => text.toLocaleLowerCase().includes(term)) && titleHit) {
            found.push({
              id: `${summary.id}-title`,
              title: summary.title,
              snippet: summary.title,
              updatedAt: summary.updatedAt,
            })
          }
        }
        setHits([...found])
      }
      if (active) {
        setSearching(false)
      }
"""
page = page[:start] + BODY + page[end:]

# 关键词高亮
page = page.replace(
    """              <span className={styles.snippet}>{hit.snippet}</span>""",
    """              <span className={styles.snippet}>{highlight(hit.snippet, term)}</span>""",
)
page = page.replace(
    """const clock = (value: number) => {""",
    """/** 把命中的关键词加粗，跟官方一样 */
const highlight = (text: string, term: string) => {
  if (!term) {
    return text
  }
  const parts = text.split(new RegExp(`(${term.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&')})`, 'gi'))
  return parts.map((part, index) =>
    part.toLocaleLowerCase() === term ? <b key={index} className={styles.mark}>{part}</b> : part
  )
}

const clock = (value: number) => {""",
    1,
)
PAGE.write_text(page, encoding='utf-8')
print('per-message hits + highlight')

CSS = Path('src/components/search/SessionSearchPage.module.css')
css = CSS.read_text(encoding='utf-8')
if '.mark' not in css:
    css += """
.mark {
  color: var(--dsw-alias-label-primary);
  font-weight: 600;
}
"""
    CSS.write_text(css, encoding='utf-8')
    print('highlight style added')

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 29', gradle), encoding='utf-8')
print('versionCode 29')
