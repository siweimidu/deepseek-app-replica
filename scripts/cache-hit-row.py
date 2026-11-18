"""Show the cache hit rate as its own row in the session detail sheet (and nowhere else)."""

import re
from pathlib import Path

SHEET = Path('src/components/sider/SessionDetailSheet.tsx')
sheet = SHEET.read_text(encoding='utf-8')

# 1) 上下文那一行不再夹带命中率
OLD_VALUE = """              value={[
                `${Math.round(loaded.contextUsage.inputTokens / 100) / 10}K / ${
                  MODEL_WINDOWS['deepseek-flash'] / 1000
                }K`,
                loaded.contextUsage.cacheReadTokens
                  ? `${Math.round(
                      (loaded.contextUsage.cacheReadTokens /
                        Math.max(
                          1,
                          loaded.contextUsage.cacheReadTokens + loaded.contextUsage.inputTokens
                        )) *
                        100
                    )}% 命中缓存`
                  : '',
                loaded.anchor ? '已存档开头' : '',
              ]
                .filter(Boolean)
                .join(' · ')}"""
NEW_VALUE = """              value={[
                `${Math.round(loaded.contextUsage.inputTokens / 100) / 10}K / ${
                  MODEL_WINDOWS['deepseek-flash'] / 1000
                }K`,
                loaded.anchor ? '已存档开头' : '',
              ]
                .filter(Boolean)
                .join(' · ')}"""
assert OLD_VALUE in sheet, 'context row not found'
sheet = sheet.replace(OLD_VALUE, NEW_VALUE, 1)

# 2) 新增独立的缓存命中率行
anchor_row = """          <Row
            icon={<IconChatOutline20 />}
            label={t('sessionDetailMessages')}
            value={loaded ? loaded.messages.length : '—'}
          />"""
NEW_ROW = anchor_row + """
          {cache ? (
            <Row
              icon={<IconCopyOutline20 />}
              label={t('sessionDetailCacheHit')}
              value={`${cache.rate}% · ${cache.detail}`}
            />
          ) : null}"""
sheet = sheet.replace(anchor_row, NEW_ROW, 1)

# 3) 计算命中率
sheet = sheet.replace(
    "  const [shown, setShown] = useState(false)",
    """  const [shown, setShown] = useState(false)
  // 缓存命中率：命中的缓存 token 占本轮输入侧总量的比例（只在详情里展示）
  const cache = (() => {
    const usage = loaded?.contextUsage
    if (!usage) {
      return null
    }
    const total = usage.inputTokens + usage.cacheReadTokens + usage.cacheWriteTokens
    if (total <= 0) {
      return null
    }
    const rate = Math.round((usage.cacheReadTokens / total) * 100)
    const kilo = (value: number) =>
      value >= 1000 ? `${Math.round(value / 100) / 10}K` : String(value)
    return {
      rate,
      detail: `命中 ${kilo(usage.cacheReadTokens)} / 输入 ${kilo(total)}`,
    }
  })()""",
    1,
)
SHEET.write_text(sheet, encoding='utf-8')
print('detail row added')

for path, line in (
    (Path('src/i18n/zh.ts'), "  sessionDetailCacheHit: '缓存命中率',\n"),
    (Path('src/i18n/en.ts'), "  sessionDetailCacheHit: 'Cache hit rate',\n"),
):
    text = path.read_text(encoding='utf-8')
    if 'sessionDetailCacheHit' not in text:
        text = text.replace('  sessionDetailMessages:', line + '  sessionDetailMessages:', 1)
        path.write_text(text, encoding='utf-8')
        print('i18n', path.name)

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 37', gradle), encoding='utf-8')
print('versionCode 37')
