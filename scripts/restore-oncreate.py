"""恢复 MainActivity 的 onCreate，只精确删除两个原生横滑方法。"""

import re
from pathlib import Path

JAVA = Path('android/app/src/main/java/com/deep/sleep/MainActivity.java')

# 1) 先恢复成已知可用版本（含 onCreate）
import subprocess

subprocess.run(
    ['git', 'checkout', 'b07c0f8', '--', 'android/app/src/main/java/com/deep/sleep/MainActivity.java'],
    check=True,
)
java = JAVA.read_text(encoding='utf-8')
print('restored; onCreate present:', 'protected void onCreate' in java)

# 2) 精确删除：从 dispatchTouchEvent 的 @Override 到 onCreate 的 @Override 之前
start = java.index('    @Override\n    public boolean dispatchTouchEvent')
end = java.index('    @Override\n    protected void onCreate')
removed = java[start:end]
assert 'dispatchSwipeIfHorizontal' in removed, 'sanity: wrong slice'
java = java[:start] + java[end:]

# 3) 字段与 import
java = re.sub(r"    // 横滑判定[^\n]*\n", '', java)
for line in [
    '    private float swipeDownX;\n',
    '    private float swipeDownY;\n',
    '    private boolean swipeTracking;\n',
    '    private static final float SWIPE_DP = 24f;\n',
    '    private static final float SWIPE_RATIO = 1.2f;\n',
    'import android.view.MotionEvent;\n',
]:
    java = java.replace(line, '')

JAVA.write_text(java, encoding='utf-8')
print('swipe removed:', 'dispatchTouchEvent' not in java and 'swipeDownX' not in java)
print('onCreate kept:', 'protected void onCreate' in java)
print('setContentView kept:', 'setContentView' in java)
print('loadUrl kept:', 'loadUrl' in java)
