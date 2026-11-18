"""按 V4.1 Flash-1017 校正：窗口 1M，并给模型加可读名称。"""

import re
from pathlib import Path

BUDGET = Path('src/services/chat/context/budget.ts')
budget = BUDGET.read_text(encoding='utf-8')

budget = budget.replace(
    """/** 各模型的窗口大小（token）。数值可在设置里被覆盖。 */
export const MODEL_WINDOWS: Record<ChatModel, number> = {
  'deepseek-flash': 128_000,
  'deepseek-v4-pro': 128_000,
}""",
    """/** 各模型的窗口大小（token） */
export const MODEL_WINDOWS: Record<ChatModel, number> = {
  // V4.1 Flash-1017：100 万上下文
  'deepseek-flash': 1_000_000,
  // V4.1 Pro 的窗口尚未核对，先保守按 128K
  'deepseek-v4-pro': 128_000,
}

/** 界面上展示用的模型名 */
export const MODEL_LABELS: Record<ChatModel, string> = {
  'deepseek-flash': 'DeepSeek V4.1Flash-1017',
  'deepseek-v4-pro': 'DeepSeek V4.1Pro-1017',
}""",
)
BUDGET.write_text(budget, encoding='utf-8')
print('window -> 1M for flash, labels added')

SHEET = Path('src/components/sider/SessionDetailSheet.tsx')
sheet = SHEET.read_text(encoding='utf-8')
sheet = sheet.replace(
    "import { MODEL_WINDOWS } from '../../services/chat/context/budget.js'",
    "import { MODEL_LABELS, MODEL_WINDOWS } from '../../services/chat/context/budget.js'",
)
# 模型行显示可读名称
sheet = sheet.replace(
    """            <Row
              icon={<IconInfoOutline20 />}
              label={t('sessionDetailModel')}
              value={activeModel}
            />""",
    """            <Row
              icon={<IconInfoOutline20 />}
              label={t('sessionDetailModel')}
              value={MODEL_LABELS[activeModel] ?? activeModel}
            />""",
)
SHEET.write_text(sheet, encoding='utf-8')
print('model row uses readable label')

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 67', gradle), encoding='utf-8')
print('versionCode 67')
