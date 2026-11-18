"""Add a context usage row to the session detail sheet (uses the already-loaded session)."""

from pathlib import Path

SHEET = Path('src/components/sider/SessionDetailSheet.tsx')
sheet = SHEET.read_text(encoding='utf-8')

sheet = sheet.replace(
    "import type { SessionSummary } from '../../services/chat/types.js'",
    "import type { SessionSummary } from '../../services/chat/types.js'\nimport { MODEL_WINDOWS } from '../../services/chat/context/budget.js'",
    1,
)

OLD = """          <Row
            icon={<IconIdOutline20 />}
            label={t('sessionDetailId')}"""
NEW = """          {loaded?.contextUsage ? (
            <Row
              icon={<IconInfoOutline20 />}
              label={t('sessionDetailContext')}
              value={[
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
                .join(' · ')}
            />
          ) : null}
          <Row
            icon={<IconIdOutline20 />}
            label={t('sessionDetailId')}"""
assert OLD in sheet, 'id row not found'
sheet = sheet.replace(OLD, NEW, 1)
SHEET.write_text(sheet, encoding='utf-8')
print('detail sheet shows context')

for path, line in (
    (Path('src/i18n/zh.ts'), "  sessionDetailContext: '上下文',\n"),
    (Path('src/i18n/en.ts'), "  sessionDetailContext: 'Context',\n"),
):
    text = path.read_text(encoding='utf-8')
    if 'sessionDetailContext' not in text:
        text = text.replace('  sessionDetailId:', line + '  sessionDetailId:', 1)
        path.write_text(text, encoding='utf-8')
        print('i18n', path)
