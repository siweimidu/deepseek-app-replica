"""修正：工具函数插到组件之前，模型从最后一条助手消息取（Session 本身没有 model）。"""

import re
from pathlib import Path

SHEET = Path('src/components/sider/SessionDetailSheet.tsx')
sheet = SHEET.read_text(encoding='utf-8')

# 1) 工具函数插在样式导入之后（组件之前）
if 'const formatTokens' not in sheet:
    anchor = "import styles from './SessionDetailSheet.module.css'\n"
    assert anchor in sheet, 'styles import not found'
    sheet = sheet.replace(
        anchor,
        anchor
        + """
const formatTokens = (value: number) =>
  value >= 1000 ? `${Math.round(value / 100) / 10}K` : String(value)

/** 128000 → 128K，1000000 → 1M */
const formatWindow = (value: number) =>
  value >= 1_000_000 ? `${Math.round(value / 100_000) / 10}M` : `${Math.round(value / 1000)}K`
""",
        1,
    )

# 2) 模型从最后一条助手消息推导
if 'const activeModel' not in sheet:
    anchor = "  const cache = (() => {"
    sheet = sheet.replace(
        anchor,
        """  // 会话本身不存模型，取最后一条助手消息的模型；没有就按默认
  const activeModel =
    (() => {
      const messages = loaded?.messages ?? []
      for (let index = messages.length - 1; index >= 0; index -= 1) {
        const candidate = messages[index]
        if (candidate.role === 'assistant' && candidate.model) {
          return candidate.model
        }
      }
      return null
    })() ?? 'deepseek-flash'

""" + anchor,
        1,
    )

sheet = sheet.replace(
    """                `${formatTokens(loaded.contextUsage.inputTokens)} / ${formatWindow(
                  MODEL_WINDOWS[loaded.model ?? 'deepseek-flash'] ?? MODEL_WINDOWS['deepseek-flash']
                )}`,""",
    """                `${formatTokens(loaded.contextUsage.inputTokens)} / ${formatWindow(
                  MODEL_WINDOWS[activeModel] ?? MODEL_WINDOWS['deepseek-flash']
                )}`,""",
)
SHEET.write_text(sheet, encoding='utf-8')
print('helpers + activeModel wired')

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 66', gradle), encoding='utf-8')
print('versionCode 66')
