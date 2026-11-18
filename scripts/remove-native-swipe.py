"""精确删除原生横滑（dispatchTouchEvent + dispatchSwipeIfHorizontal + 字段 + import），保留其余方法。"""

import re
from pathlib import Path

JAVA = Path('android/app/src/main/java/com/deep/sleep/MainActivity.java')
java = JAVA.read_text(encoding='utf-8')

# 1) 删两个方法：从 @Override dispatchTouchEvent 到 handleBack 之前
start = java.find('    @Override\n    public boolean dispatchTouchEvent')
end = java.find('    private void handleBack()')
assert start > 0 and end > start, 'method block not found'
java = java[:start] + java[end:]

# 2) 删字段块
java = re.sub(
    r"    // 横滑判定（原生层[^\n]*\n(?:    private (?:float|boolean) swipe[^\n]*\n|    private static final float SWIPE[^\n]*\n)+\n?",
    '',
    java,
)

# 3) 删 import
java = java.replace('import android.view.MotionEvent;\n', '')
java = java.replace('import android.os.SystemClock;\n', '')

JAVA.write_text(java, encoding='utf-8')
print('dispatchTouchEvent removed:', 'dispatchTouchEvent' not in java)
print('swipe fields removed:', 'swipeDownX' not in java)
print('handleBack kept:', 'private void handleBack()' in java)
print('setBars kept:', 'private void setBars(' in java)
