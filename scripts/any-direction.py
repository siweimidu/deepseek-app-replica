"""Any horizontal swipe toggles the drawer: left or right, both work."""

from pathlib import Path

HOOK = Path('src/components/sider/useDrawerSwipe.ts')
hook = HOOK.read_text(encoding='utf-8')

# 常量：任一方向的触发阈值
hook = hook.replace(
    "const OPEN_RATIO = 0.12",
    "const OPEN_RATIO = 0.12\nconst TRIGGER_PX = 24",
    1,
)

OLD_MOVE = """      if (state.phase === 'pending') {
        if (Math.abs(dx) < SLOP && Math.abs(dy) < SLOP) {
          return
        }
        const horizontal = Math.abs(dx) > Math.abs(dy) * DIRECTION_RATIO
        // 打开状态下两个方向都接受（往左=收起），关闭状态下只接受往右（往左=拉出）
        const valid = state.openedAtStart ? horizontal : horizontal && dx > 0
        if (!valid) {
          track.current = null
          return
        }
        state.phase = 'dragging'
        frameOf()?.setAttribute('data-drawer-dragging', '')
      }

      state.progress = state.openedAtStart ? 1 + dx / state.width : dx / state.width
      setProgress(state.progress)"""
NEW_MOVE = """      if (state.phase === 'pending') {
        if (Math.abs(dx) < SLOP && Math.abs(dy) < SLOP) {
          return
        }
        // 横向为准即可，不再区分左右：用户要的是"怎么滑都能切换"
        if (Math.abs(dx) <= Math.abs(dy) * DIRECTION_RATIO) {
          track.current = null
          return
        }
        state.phase = 'dragging'
        // 关闭时只有向右滑才跟手（左滑看着不合理），其余情况到阈值直接触发
        state.follow = !state.openedAtStart && dx > 0
        if (state.follow) {
          frameOf()?.setAttribute('data-drawer-dragging', '')
        }
      }

      if (state.follow) {
        state.progress = dx / state.width
        setProgress(state.progress)
        return
      }

      // 非跟手模式：越过阈值立刻切换，不等抬手
      if (Math.abs(dx) > TRIGGER_PX) {
        track.current = null
        flushSync(() => {
          if (state.openedAtStart) {
            closeMobileSider()
          } else {
            openMobileSider()
          }
        })
        frameOf()?.style.removeProperty('--drawer-progress')
      }"""
assert OLD_MOVE in hook, 'move block not found'
hook = hook.replace(OLD_MOVE, NEW_MOVE, 1)

# Track 增加 follow 字段
hook = hook.replace("  progress: number\n", "  progress: number\n  follow: boolean\n", 1)
hook = hook.replace(
    "        progress: useMobileSider.getState().open ? 1 : 0,\n",
    "        progress: useMobileSider.getState().open ? 1 : 0,\n        follow: false,\n",
    1,
)

# 松手：跟手模式才需要收尾判定
OLD_END = """    const onEnd = () => {
      const state = track.current
      if (!state || state.phase !== 'dragging') {
        track.current = null
        return
      }"""
NEW_END = """    const onEnd = () => {
      const state = track.current
      if (!state || state.phase !== 'dragging') {
        track.current = null
        return
      }
      if (!state.follow) {
        track.current = null
        return
      }"""
if OLD_END in hook:
    hook = hook.replace(OLD_END, NEW_END, 1)

HOOK.write_text(hook, encoding='utf-8')
print('any-direction toggle applied')

import re

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 34', gradle), encoding='utf-8')
print('versionCode 34')
