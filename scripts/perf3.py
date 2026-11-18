"""Big-ticket perf: unmount the hidden session list, isolate scroll containers."""

import re
from pathlib import Path

# ---------- 1) 抽屉关闭时不渲染会话列表（行数再多也不影响聊天页） ----------
SIDER = Path('src/components/sider/Sider.tsx')
sider = SIDER.read_text(encoding='utf-8')

sider = sider.replace(
    """  const drag = useRef<{ x: number; y: number; width: number; horizontal: boolean } | null>(null)
  const dragged = useRef(false)""",
    """  const drag = useRef<{ x: number; y: number; width: number; horizontal: boolean } | null>(null)
  const dragged = useRef(false)
  // 关闭后保留一小会儿让滑出动画走完，然后彻底卸载：几百行会话不再常驻
  const [rendered, setRendered] = useState(open)""",
    1,
)

sider = sider.replace(
    """  useEffect(() => {
    if (drawer.current) {
      drawer.current.inert = !open
    }
    if (open) {
      syncWidth()
    }
  }, [open])""",
    """  useEffect(() => {
    if (drawer.current) {
      drawer.current.inert = !open
    }
    if (open) {
      syncWidth()
      setRendered(true)
      return
    }
    const timer = window.setTimeout(() => setRendered(false), 240)
    return () => window.clearTimeout(timer)
  }, [open])""",
    1,
)

sider = sider.replace("""        <Sider mobile />
      </div>""", """        {rendered ? <Sider mobile /> : null}
      </div>""", 1)
SIDER.write_text(sider, encoding='utf-8')
print('hidden session list unmounted')

# ---------- 2) 消息滚动容器独立成层，滚动不牵动整页 ----------
LIST = Path('src/components/messages/MessageList.module.css')
css = LIST.read_text(encoding='utf-8')
if 'contain: content' not in css:
    css = css.replace(
        """.scroll {""",
        """.scroll {
  /* 滚动容器自身独立布局与绘制，滚动时不影响页面其它部分 */
  contain: content;""",
        1,
    )
    LIST.write_text(css, encoding='utf-8')
    print('message list scroll contained')

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 22', gradle), encoding='utf-8')
print('versionCode 22')
