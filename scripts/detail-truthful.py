"""详情页：上下文窗口取会话真实模型；服务端不返回缓存数据时不显示 0%。"""

import re
from pathlib import Path

SHEET = Path('src/components/sider/SessionDetailSheet.tsx')
sheet = SHEET.read_text(encoding='utf-8')

# 1) 用会话的真实模型 + 更可读的窗口格式
OLD_WINDOW = """                `${Math.round(loaded.contextUsage.inputTokens / 100) / 10}K / ${
                  MODEL_WINDOWS['deepseek-flash'] / 1000
                }K`,"""
NEW_WINDOW = """                `${formatTokens(loaded.contextUsage.inputTokens)} / ${formatWindow(
                  MODEL_WINDOWS[loaded.model ?? 'deepseek-flash'] ?? MODEL_WINDOWS['deepseek-flash']
                )}`,"""
assert OLD_WINDOW in sheet, 'window row not found'
sheet = sheet.replace(OLD_WINDOW, NEW_WINDOW, 1)

# 2) 缓存命中：服务端没给数据就别显示 0%
OLD_CACHE = """  const cache = (() => {
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
  })()"""
NEW_CACHE = """  const cache = (() => {
    const usage = loaded?.contextUsage
    if (!usage) {
      return null
    }
    // 服务端完全没返回缓存字段时，不要谎报 0%
    if (usage.cacheReadTokens + usage.cacheWriteTokens === 0) {
      return { label: '—', detail: '服务端未返回缓存数据' }
    }
    const total = usage.inputTokens + usage.cacheReadTokens + usage.cacheWriteTokens
    if (total <= 0) {
      return null
    }
    return {
      label: `${Math.round((usage.cacheReadTokens / total) * 100)}%`,
      detail: `命中 ${formatTokens(usage.cacheReadTokens)} / 输入 ${formatTokens(total)}`,
    }
  })()"""
assert OLD_CACHE in sheet, 'cache calc not found'
sheet = sheet.replace(OLD_CACHE, NEW_CACHE, 1)

# 3) 行渲染用新字段
sheet = sheet.replace(
    """              value={`${cache.rate}% · ${cache.detail}`}""",
    """              value={`${cache.label} · ${cache.detail}`}""",
    1,
)

# 4) 工具函数
if 'const formatWindow' not in sheet:
    sheet = sheet.replace(
        "const clock =",
        """const formatTokens = (value: number) =>
  value >= 1000 ? `${Math.round(value / 100) / 10}K` : String(value)

/** 128000 → 128K，1000000 → 1M */
const formatWindow = (value: number) =>
  value >= 1_000_000 ? `${Math.round(value / 100_000) / 10}M` : `${Math.round(value / 1000)}K`

const clock =""",
        1,
    )
SHEET.write_text(sheet, encoding='utf-8')
print('detail sheet: real model window + honest cache label')
