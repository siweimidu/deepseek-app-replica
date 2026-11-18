"""Show context usage (tokens, cache hit rate, compaction) in the session detail sheet."""

from pathlib import Path

SHEET = Path('src/components/sider/SessionDetailSheet.tsx')
sheet = SHEET.read_text(encoding='utf-8')

sheet = sheet.replace(
    "import type { SessionSummary } from '../../services/chat/types.js'",
    "import type { SessionSummary } from '../../services/chat/types.js'\nimport { MODEL_WINDOWS } from '../../services/chat/context/budget.js'",
    1,
)

if 'contextUsage' not in sheet:
    # 在组件内取到完整会话，读 usage / anchor
    marker = "export const SessionDetailSheet = ({"
    anchor_line = sheet.index(marker)
    body_start = sheet.index('{', anchor_line) + 1
    sheet = (
        sheet[:body_start]
        + """
  const session = useChatStore((state) => (summary ? state.sessionCache[summary.id] : undefined))
"""
        + sheet[body_start:]
    )

    # 在会话 ID 行之前插入上下文行
    old_row = "      <Row icon={<IconIdOutline20 />} label={t('sessionDetailId')}"
    new_row = """      {session?.contextUsage ? (
        <Row
          icon={<IconInfoOutline20 />}
          label={t('sessionDetailContext')}
          value={`${Math.round(session.contextUsage.inputTokens / 100) / 10}K / ${
            MODEL_WINDOWS[session.model ?? 'deepseek-flash'] / 1000
          }K${
            session.contextUsage.cacheReadTokens
              ? ` · ${Math.round(
                  (session.contextUsage.cacheReadTokens /
                    Math.max(
                      1,
                      session.contextUsage.cacheReadTokens + session.contextUsage.inputTokens
                    )) *
                    100
                )}% 命中缓存`
              : ''
          }${session.anchor ? ` · 已存档开头` : ''}`}
        />
      ) : null}
      <Row icon={<IconIdOutline20 />} label={t('sessionDetailId')}"""
    assert old_row in sheet, 'id row not found'
    sheet = sheet.replace(old_row, new_row, 1)
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
