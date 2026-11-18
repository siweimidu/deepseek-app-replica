"""回退"选中项置顶"，改为：顺序不变，打开侧边栏时滚动到当前会话，并让它贴着列表顶部。"""

import re
from pathlib import Path

# ---------- 1) 回退 orderedSessions（顺序保持原样） ----------
SIDER = Path('src/components/sider/Sider.tsx')
tsx = SIDER.read_text(encoding='utf-8')

start = tsx.find('  // 当前会话放到最前：切换回来时它总在最上面')
if start >= 0:
    end = tsx.find('  const groups = useMemo(() => {', start)
    tsx = tsx[:start] + tsx[end:]
    print('orderedSessions removed')

tsx = tsx.replace('groupSessions(orderedSessions, now, t)', 'groupSessions(sessions, now, t)')
tsx = tsx.replace(
    'orderedSessions.filter((session) => pinnedIds.includes(session.id))',
    'sessions.filter((session) => pinnedIds.includes(session.id))',
)
tsx = tsx.replace(
    'orderedSessions.filter((session) => !pinnedIds.includes(session.id))',
    'sessions.filter((session) => !pinnedIds.includes(session.id))',
)
tsx = tsx.replace(
    '}, [androidDrawer, orderedSessions, now, pinnedIds, t])',
    '}, [androidDrawer, sessions, now, pinnedIds, t])',
)

# ---------- 2) 列表容器 ref + 打开时滚到当前会话 ----------
if 'listRef' not in tsx:
    tsx = tsx.replace(
        '  const [now, setNow] = useState(Date.now)',
        '  const listRef = useRef<HTMLDivElement>(null)\n  const [now, setNow] = useState(Date.now)',
        1,
    )
    # 挂 ref 到滚动容器
    tsx = tsx.replace(
        '<div className={styles.list} ref={listRef}>',
        '<div className={styles.list} ref={listRef}>',
    )
    if 'ref={listRef}' not in tsx:
        tsx = tsx.replace(
            "className={styles.list}",
            "className={styles.list}\n          ref={listRef}",
            1,
        )

    # 滚到当前会话：让它的顶部贴住列表可视区顶部（顺序不变，只改滚动位置）
    anchor = '  const groups = useMemo(() => {'
    effect = '''  // 打开侧边栏时把当前会话滚到列表顶部（只改滚动位置，不动顺序）
  useEffect(() => {
    if (!activeId) {
      return
    }
    const list = listRef.current
    if (!list) {
      return
    }
    // 等一帧，确保列表已经渲染出来
    const frame = requestAnimationFrame(() => {
      const row = list.querySelector<HTMLElement>(`[data-session-id="${CSS.escape(activeId)}"]`)
      if (!row) {
        return
      }
      const offset = row.offsetTop - list.offsetTop
      list.scrollTop = Math.max(0, offset)
    })
    return () => cancelAnimationFrame(frame)
  }, [activeId, groups.length])

''' + anchor
    tsx = tsx.replace(anchor, effect, 1)
    SIDER.write_text(tsx, encoding='utf-8')
    print('scroll-to-active wired')

# ---------- 3) 会话行加 data-session-id 锚点 ----------
ITEM = Path('src/components/sider/SessionItem.tsx')
item = ITEM.read_text(encoding='utf-8')
if 'data-session-id' not in item:
    item = re.sub(
        r'(<div\s+className=\{clsx\([^)]*\)\})',
        r'\1\n      data-session-id={session.id}',
        item,
        count=1,
    )
    ITEM.write_text(item, encoding='utf-8')
    print('session row anchor added:', 'data-session-id' in item)

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 50', gradle), encoding='utf-8')
print('versionCode 50')
