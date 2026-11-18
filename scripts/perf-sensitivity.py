"""Raise interaction sensitivity: faster feedback, earlier gesture capture, quicker voice turn-taking."""

import re
from pathlib import Path

# ---------- 1) 动效时长整体收紧 ----------
MOTION = Path('src/app/motion.css')
motion = MOTION.read_text(encoding='utf-8')
if '--motion-press-fast' not in motion:
    motion += """
/* 交互灵敏度：按压反馈要立刻给，导航要快 */
:root {
  --motion-press: 180ms linear(0, 0.42 10%, 0.86 26%, 1.02 44%, 1.005 66%, 1);
  --motion-press-fast: 140ms linear(0, 0.5 12%, 0.92 30%, 1.01 48%, 1);
  --motion-drawer:
    220ms linear(0, 0.34 8%, 0.78 20%, 0.95 32%, 1.01 46%, 1.004 64%, 1);
  --motion-sheet: 300ms linear(0, 0.26 8%, 0.66 20%, 0.9 34%, 1.015 50%, 1.006 68%, 1);
}
"""
    MOTION.write_text(motion, encoding='utf-8')
    print('motion tokens tightened')

# ---------- 2) 去掉点击高亮与双击缩放延迟 ----------
GLOBAL = Path('src/app/global.css')
glob = GLOBAL.read_text(encoding='utf-8')
if 'tap-highlight-color' not in glob:
    glob += """
/* 交互灵敏度：去掉点击高亮与双击缩放等待，点击即刻响应 */
* {
  -webkit-tap-highlight-color: transparent;
}

button,
a,
[role='button'],
[role='menuitem'] {
  touch-action: manipulation;
}

html {
  overscroll-behavior-y: none;
}
"""
    GLOBAL.write_text(glob, encoding='utf-8')
    print('tap latency removed')

# ---------- 3) 左滑关闭：更早接管 ----------
SIDER = Path('src/components/sider/Sider.tsx')
sider = SIDER.read_text(encoding='utf-8')
sider = sider.replace('if (Math.abs(dx) < 10 && Math.abs(dy) < 10)', 'if (Math.abs(dx) < 6 && Math.abs(dy) < 6)')
sider = sider.replace('Math.abs(dx) <= Math.abs(dy) * 1.2', 'Math.abs(dx) <= Math.abs(dy) * 1.1')
sider = sider.replace('offset < -state.width * 0.3', 'offset < -state.width * 0.24')
SIDER.write_text(sider, encoding='utf-8')
print('swipe thresholds tightened')

# ---------- 4) 通话：更早判停、更灵敏的收音 ----------
CALL = Path('src/components/call/useCallSession.ts')
call = CALL.read_text(encoding='utf-8')
call = call.replace('const SILENCE_MS = 1300', 'const SILENCE_MS = 900')
call = call.replace('const MIN_SPEECH_MS = 320', 'const MIN_SPEECH_MS = 260')
call = call.replace('const SPEECH_LEVEL = 0.06', 'const SPEECH_LEVEL = 0.045')
CALL.write_text(call, encoding='utf-8')
print('voice turn-taking tightened')

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 16', gradle), encoding='utf-8')
print('versionCode 16')
