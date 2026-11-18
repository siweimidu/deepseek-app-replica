"""当前会话置顶显示 + 标题生成兜底。"""

import re
from pathlib import Path

# ---------- 1) 流结束时再兜底一次标题 ----------
STORE = Path('src/services/chat/store.ts')
store = STORE.read_text(encoding='utf-8')
OLD = """    persist(sessionId)
  }
}"""
NEW = """    persist(sessionId)
    // 有些流不发 stop_reason，收尾时再兜底一次
    ensureLocalTitle(sessionId)
  }
}"""
if store.count(OLD) == 1:
    store = store.replace(OLD, NEW, 1)
    STORE.write_text(store, encoding='utf-8')
    print('title fallback in finally')
else:
    print('finally anchor matched', store.count(OLD), 'times — skipped')

# ---------- 2) 侧边栏：当前会话排最前 ----------
SIDER = Path('src/components/sider/Sider.tsx')
tsx = SIDER.read_text(encoding='utf-8')

if 'orderedSessions' not in tsx:
    tsx = tsx.replace(
        "  const groups = useMemo(() => {",
        """  // 当前会话放到最前：切换回来时它总在最上面
  const orderedSessions = useMemo(() => {
    if (!activeId) {
      return sessions
    }
    const index = sessions.findIndex((session) => session.id === activeId)
    if (index <= 0) {
      return sessions
    }
    const copy = [...sessions]
    const [current] = copy.splice(index, 1)
    return [current, ...copy]
  }, [sessions, activeId])

  const groups = useMemo(() => {""",
        1,
    )
    tsx = tsx.replace(
        "    return groupSessions(sessions, now, t)",
        "    return groupSessions(orderedSessions, now, t)",
        1,
    )
    tsx = tsx.replace(
        "    const pinned = sessions.filter((session) => pinnedIds.includes(session.id))",
        "    const pinned = orderedSessions.filter((session) => pinnedIds.includes(session.id))",
        1,
    )
    tsx = tsx.replace(
        "      sessions.filter((session) => !pinnedIds.includes(session.id)),",
        "      orderedSessions.filter((session) => !pinnedIds.includes(session.id)),",
        1,
    )
    tsx = tsx.replace(
        "  }, [androidDrawer, sessions, now, pinnedIds, t])",
        "  }, [androidDrawer, orderedSessions, now, pinnedIds, t])",
        1,
    )
    SIDER.write_text(tsx, encoding='utf-8')
    print('active session ordered first')

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 49', gradle), encoding='utf-8')
print('versionCode 49')
