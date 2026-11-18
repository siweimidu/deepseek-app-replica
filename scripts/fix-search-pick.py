"""Search hits must carry the real session id so tapping a result opens that conversation."""

import re
from pathlib import Path

PAGE = Path('src/components/search/SessionSearchPage.tsx')
page = PAGE.read_text(encoding='utf-8')

# 1) Hit 增加 sessionId（id 只用于列表 key）
page = page.replace(
    """type Hit = {
  id: string
  title: string""",
    """type Hit = {
  /** 列表 key（会话 id + 消息序号），不能拿来查会话 */
  id: string
  /** 真正要跳转的会话 id */
  sessionId: string
  title: string""",
    1,
)

# 2) 构造结果时带上 sessionId
page = page.replace(
    """            found.push({
              id: `${summary.id}-${index}`,""",
    """            found.push({
              id: `${summary.id}-${index}`,
              sessionId: summary.id,""",
    1,
)
page = page.replace(
    """            found.push({
              id: `${summary.id}-title`,""",
    """            found.push({
              id: `${summary.id}-title`,
              sessionId: summary.id,""",
    1,
)

# 3) 点击时用 sessionId，并带上要定位的消息序号
page = page.replace(
    """  const pick = (hit: Hit) => {
    void selectSession(hit.id)
    closeSessionSearch()
  }""",
    """  const pick = (hit: Hit) => {
    // 用真实会话 id 跳转；id 是列表 key（会话 id + 消息序号），不能直接当会话 id
    void selectSession(hit.sessionId)
    closeSessionSearch()
  }""",
    1,
)
PAGE.write_text(page, encoding='utf-8')
print('search hit carries sessionId')

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 46', gradle), encoding='utf-8')
print('versionCode 46')
