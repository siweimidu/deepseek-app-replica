"""Insert the dispatchTouchEvent override before onCreate (signature: onCreate(Bundle state))."""

from pathlib import Path

JAVA = Path('android/app/src/main/java/com/deep/sleep/MainActivity.java')
java = JAVA.read_text(encoding='utf-8')

if 'dispatchSwipeIfHorizontal' in java:
    print('already present')
else:
    anchor = '    public void onCreate(Bundle state) {'
    assert anchor in java, 'onCreate anchor not found'
    # 找到 @Override 行（onCreate 前一行）
    index = java.index(anchor)
    line_start = java.rfind('\n', 0, index)
    override_start = java.rfind('\n', 0, line_start)
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

'''
    java = java[:override_start] + '\n' + addition + java[override_start + 1 :]
    JAVA.write_text(java, encoding='utf-8')
    print('dispatchTouchEvent inserted:', 'dispatchSwipeIfHorizontal' in java)
