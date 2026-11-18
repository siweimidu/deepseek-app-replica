"""Header phone identical to siblings, drawer left-flick closes, call reads the whole reply once."""

import re
from pathlib import Path

# ---------- 1) 电话按钮：与音量、加号完全一样（无底色、无阴影） ----------
HEADER = Path('src/components/session/MobileHeader.module.css')
header = HEADER.read_text(encoding='utf-8')
header = re.sub(
    r"/\* 官方：电话是带圆形底色的按钮.*?\n\}\n",
    "",
    header,
    flags=re.S,
)
header += """
/* 电话与音量、加号保持完全一致：透明底、同尺寸、无任何投影 */
[data-android] .call,
[data-android] .sound,
[data-android] .newChat {
  background: transparent;
  box-shadow: none;
  border: 0;
}

[data-android] .call svg {
  width: 22px;
  height: 22px;
}
"""
HEADER.write_text(header, encoding='utf-8')
print('phone matches siblings')

# ---------- 2) 抽屉里往左轻划就能回到对话 ----------
SIDER = Path('src/components/sider/Sider.tsx')
sider = SIDER.read_text(encoding='utf-8')
OLD = """          const travelled = event.clientX - state.x
          // 往左拖按进度判断；往右轻轻一滑也直接收起（官方手感）
          const flickRight = travelled > state.width * 0.12
          settle(flickRight || progress < 0.76)"""
NEW = """          const travelled = event.clientX - state.x
          // 轻划也算数：往左 18px、往右 12% 都直接收起，不必拖到进度阈值
          const flickLeft = travelled < -18
          const flickRight = travelled > state.width * 0.12
          settle(flickLeft || flickRight || progress < 0.76)"""
assert OLD in sider, 'settle block not found'
SIDER.write_text(sider.replace(OLD, NEW, 1), encoding='utf-8')
print('left flick closes drawer')

# ---------- 3) 通话朗读：整段一次性读出，避免听到的内容和文本不一致 ----------
CALL = Path('src/components/call/useCallSession.ts')
call = CALL.read_text(encoding='utf-8')
START = call.index('        // 1) 等到第一句')
END = call.index('        setPhase(\'listening\')', START)
REPLACEMENT = """        // 等这一轮回复生成完，整段一次性朗读：分句朗读会出现听到的和看到的对不上
        let spokenText = ''
        let replyId: string | null = null
        for (let step = 0; step < 1800; step++) {
          const snapshot = replyText()
          replyId = snapshot.id ?? replyId
          if (!snapshot.streaming && step > 4) {
            spokenText = snapshot.text
            break
          }
          await wait(120)
          if (ticket !== loop.current) {
            return
          }
        }
        if (ticket !== loop.current) {
          return
        }
        if (spokenText.trim()) {
          await speakText(spokenText, replyId)
        }
        if (ticket !== loop.current) {
          return
        }
"""
call = call[:START] + REPLACEMENT + call[END:]
CALL.write_text(call, encoding='utf-8')
print('single-shot speech restored')

# takeSentence 不再需要
call = CALL.read_text(encoding='utf-8')
call = re.sub(
    r"/\*\* 取回第一个完整句子[\s\S]*?\n\}\n",
    "",
    call,
    count=1,
)
CALL.write_text(call, encoding='utf-8')
print('takeSentence removed:', 'takeSentence' not in call)

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 27', gradle), encoding='utf-8')
print('versionCode 27')
