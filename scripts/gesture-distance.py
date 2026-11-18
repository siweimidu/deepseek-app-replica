"""保留上游手势结构，补一条位移判定：横移超过 60px 就按方向切换（轻滑也能用）。"""

import re
from pathlib import Path

HOOK = Path('src/components/sider/useAndroidDrawerGesture.ts')
hook = HOOK.read_text(encoding='utf-8')

OLD = """    const velocity = releaseVelocity(drag.samples, event.timeStamp)
    const flick = Math.abs(velocity) >= minFlingVelocity
    const open = cancelled ? drag.startedOpen : flick ? velocity > 0 : drag.current >= 0.5"""
NEW = """    const velocity = releaseVelocity(drag.samples, event.timeStamp)
    const flick = Math.abs(velocity) >= minFlingVelocity
    // 相对起点移动了多少（正=往右=打开，负=往左=关闭）
    const travelled = drag.current - drag.start
    const farEnough = Math.abs(travelled) * drag.edge >= toggleDistance
    const open = cancelled
      ? drag.startedOpen
      : flick
        ? velocity > 0
        : farEnough
          ? travelled > 0
          : drag.current >= 0.5"""
assert OLD in hook, 'settle decision not found'
hook = hook.replace(OLD, NEW, 1)

# 位移阈值常量
hook = hook.replace(
    "const minFlingVelocity = 0.33",
    "const minFlingVelocity = 0.33\n/** 横移超过这个距离就按方向切换，轻滑也能生效（不必拖过 50% 宽度） */\nconst toggleDistance = 56",
    1,
)
HOOK.write_text(hook, encoding='utf-8')
print('distance-based toggle added:', 'toggleDistance' in hook)

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 62', gradle), encoding='utf-8')
print('versionCode 62')
