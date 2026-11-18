"""Detect horizontal swipes in the Activity so the WebView event quirks can't swallow them."""

from pathlib import Path

JAVA = Path('android/app/src/main/java/com/deep/sleep/MainActivity.java')
java = JAVA.read_text(encoding='utf-8')

# 1) 需要的 import
if 'import android.view.MotionEvent;' not in java:
    java = java.replace(
        'import android.os.Bundle;',
        'import android.os.Bundle;\nimport android.os.SystemClock;\nimport android.view.MotionEvent;',
        1,
    )

# 2) 字段
if 'swipeDownX' not in java:
    java = java.replace(
        '    private WebView webView;',
        """    private WebView webView;
    // 横滑判定（原生层，绕开 WebView 的事件仲裁）
    private float swipeDownX;
    private float swipeDownY;
    private boolean swipeTracking;
    private static final float SWIPE_DP = 24f;
    private static final float SWIPE_RATIO = 1.2f;""",
        1,
    )

# 3) dispatchTouchEvent + 派发方法
if 'dispatchTouchEvent' not in java:
    anchor = '    @Override\n    protected void onCreate(Bundle savedInstanceState) {'
    addition = '''    @Override
    public boolean dispatchTouchEvent(MotionEvent event) {
        switch (event.getActionMasked()) {
            case MotionEvent.ACTION_DOWN:
                swipeDownX = event.getX();
                swipeDownY = event.getY();
                swipeTracking = true;
                break;
            case MotionEvent.ACTION_UP:
                if (swipeTracking) {
                    swipeTracking = false;
                    dispatchSwipeIfHorizontal(event.getX(), event.getY());
                }
                break;
            case MotionEvent.ACTION_CANCEL:
                swipeTracking = false;
                break;
            default:
                break;
        }
        return super.dispatchTouchEvent(event);
    }

    /** 横滑超过 24dp 且明显偏横向时通知网页：left = 打开侧边栏，right = 回到对话 */
    private void dispatchSwipeIfHorizontal(float upX, float upY) {
        final float dx = upX - swipeDownX;
        final float dy = upY - swipeDownY;
        final float minPx = SWIPE_DP * getResources().getDisplayMetrics().density;
        if (Math.abs(dx) < minPx || Math.abs(dx) <= Math.abs(dy) * SWIPE_RATIO) {
            return;
        }
        final String direction = dx < 0 ? "left" : "right";
        runOnUiThread(() -> {
            if (webView != null) {
                webView.evaluateJavascript(
                    "window.__dshSwipe&&window.__dshSwipe('" + direction + "')", null);
            }
        });
    }

''' + anchor
    java = java.replace(anchor, addition, 1)

JAVA.write_text(java, encoding='utf-8')
print('native swipe detector added:', 'dispatchSwipeIfHorizontal' in java)
