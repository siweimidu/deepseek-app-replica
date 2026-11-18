"""Phone chip without shadow, grey ellipsis like the official, right-swipe close, default avatar art."""

import re
import shutil
from pathlib import Path

REPO = Path('.')

# ---------- 1) 电话圆钮：纯色底、无阴影 ----------
HEADER = Path('src/components/session/MobileHeader.module.css')
header = HEADER.read_text(encoding='utf-8')
header = header.replace(
    """[data-android] .call {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: color-mix(in srgb, var(--dsw-alias-label-primary) 10%, transparent);
  margin: 0 6px;""",
    """[data-android] .call {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  /* 官方是干净的浅灰实底，不带任何投影 */
  background: var(--dsw-alias-bg-skeleton);
  box-shadow: none;
  margin: 0 6px;""",
)
HEADER.write_text(header, encoding='utf-8')
print('phone chip: flat fill, no shadow')

# ---------- 2) 「⋯」：灰色、贴右侧，与官方一致 ----------
ITEM = Path('src/components/sider/SessionItem.module.css')
item = ITEM.read_text(encoding='utf-8')
item = item.replace(
    """  .action {
    position: absolute;
    right: 4px;
    display: flex;
    opacity: 0;
    pointer-events: none;
  }""",
    """  .action {
    position: absolute;
    right: 6px;
    display: flex;
    /* 官方那个「⋯」是灰色，不跟着选中行的蓝字走 */
    color: color-mix(in srgb, var(--dsw-alias-label-primary) 46%, transparent);
    opacity: 0;
    pointer-events: none;
  }""",
)
ITEM.write_text(item, encoding='utf-8')
print('ellipsis grey like official')

# ---------- 3) 抽屉打开时右滑也能关闭 ----------
SIDER = Path('src/components/sider/Sider.tsx')
sider = SIDER.read_text(encoding='utf-8')

OLD = """          const progress =
            Number.parseFloat(
              element?.parentElement?.style.getPropertyValue('--drawer-progress') ?? '1'
            ) || 1
          settle(progress < 0.76)"""
NEW = """          const progress =
            Number.parseFloat(
              element?.parentElement?.style.getPropertyValue('--drawer-progress') ?? '1'
            ) || 1
          const travelled = event.clientX - state.x
          // 往左拖按进度判断；往右轻轻一滑也直接收起（官方手感）
          const flickRight = travelled > state.width * 0.12
          settle(flickRight || progress < 0.76)"""
assert OLD in sider, 'settle call not found'
SIDER.write_text(sider.replace(OLD, NEW, 1), encoding='utf-8')
print('right swipe closes the drawer')

# ---------- 4) 默认头像换成 DeepSleep 的角色图 ----------
src = Path(r'C:\Users\35238\.dsh\attachments\v1\objects\bd\bdb4b936099d8fa6c8d0de917644af9a237420db64c3ca035573403a1a63a3d2')
target = REPO / 'src/assets/deepsleep-avatar.png'
if src.exists():
    shutil.copyfile(src, target)
    print('default avatar copied', target.stat().st_size, 'bytes')

SIDER_TSX = SIDER
src_tsx = SIDER_TSX.read_text(encoding='utf-8')
if 'deepsleep-avatar' not in src_tsx:
    src_tsx = src_tsx.replace(
        "import { android } from '../../app/android.js'",
        "import { android } from '../../app/android.js'\nimport defaultAvatar from '../../assets/deepsleep-avatar.png'",
        1,
    )
    src_tsx = src_tsx.replace(
        """                avatar ? (
                  <img className={styles.avatarImage} src={avatar} alt="" />
                ) : (
                  <PersonIcon />
                )""",
        """                <img className={styles.avatarImage} src={avatar ?? defaultAvatar} alt="" />""",
        1,
    )
    SIDER_TSX.write_text(src_tsx, encoding='utf-8')
    print('drawer uses default avatar art')

SETTINGS = Path('src/components/settings/AndroidSettings.tsx')
settings = SETTINGS.read_text(encoding='utf-8')
if 'deepsleep-avatar' not in settings:
    settings = settings.replace(
        "import { AvatarEditor } from './AvatarEditor.js'",
        "import defaultAvatar from '../../assets/deepsleep-avatar.png'\nimport { AvatarEditor } from './AvatarEditor.js'",
        1,
    )
    settings = settings.replace(
        """                  {avatar ? <img src={avatar} alt="" /> : <Profile />}""",
        """                  <img src={avatar ?? defaultAvatar} alt="" />""",
        1,
    )
    SETTINGS.write_text(settings, encoding='utf-8')
    print('account page uses default avatar art')

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 26', gradle), encoding='utf-8')
print('versionCode 26')
