"""Invariant: open ⇒ progress 1, closed ⇒ no inline progress. Ordering bugs become impossible."""

from pathlib import Path

HOOK = Path('src/components/sider/useDrawerSwipe.ts')
hook = HOOK.read_text(encoding='utf-8')

OLD = """  // 状态自愈：任何一次开合结束后都不允许残留半途的进度
  useEffect(
    () =>
      useMobileSider.subscribe(() => {
        const frame = frameRef.current
        if (!frame) {
          return
        }
        if (!frame.hasAttribute('data-drawer-dragging')) {
          frame.style.removeProperty('--drawer-progress')
        }
      }),
    [frameRef],
  )"""
NEW = """  /**
   * 不变量：打开 ⇒ 进度恒为 1；关闭 ⇒ 不保留任何内联进度。
   * 拖拽中不动它。这样即便某次收尾的顺序出了岔子，抽屉也不可能停在半途或弹回去。
   */
  useEffect(
    () =>
      useMobileSider.subscribe((state) => {
        const frame = frameRef.current
        if (!frame || frame.hasAttribute('data-drawer-dragging')) {
          return
        }
        if (state.open) {
          frame.style.setProperty('--drawer-progress', '1')
        } else {
          frame.style.removeProperty('--drawer-progress')
        }
      }),
    [frameRef],
  )"""
assert OLD in hook, 'self-heal block not found'
hook = hook.replace(OLD, NEW, 1)
HOOK.write_text(hook, encoding='utf-8')
print('invariant applied')

import re

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 33', gradle), encoding='utf-8')
print('versionCode 33')
