"""禁用资源缓存：避免升级后 WebView 用旧 index.html 引用已不存在的 JS/CSS 导致黑屏。"""

import re
from pathlib import Path

JAVA = Path('android/app/src/main/java/com/deep/sleep/MainActivity.java')
java = JAVA.read_text(encoding='utf-8')

# 1) index.html 与 /static/* 的响应加 no-store
OLD = """                Map<String, String> headers = Map.of("Content-Security-Policy","""
NEW = """                Map<String, String> headers = new HashMap<>();
                // 关键：升级后必须拿到新的 index.html，否则旧 html 会引用已删除的
                // hash 文件名，页面直接空白/黑屏
                headers.put("Cache-Control", "no-store, no-cache, must-revalidate");
                headers.put("Pragma", "no-cache");
                headers.put("Expires", "0");
                headers.put("Content-Security-Policy","""
assert OLD in java, 'header block not found'
java = java.replace(OLD, NEW, 1)

# 上面把 Map.of(...) 改成了 put，需要补上结尾的括号形态
OLD_TAIL = """                    + "frame-src 'none'; base-uri 'none'; form-action 'none';");"""
NEW_TAIL = """                    + "frame-src 'none'; base-uri 'none'; form-action 'none';");"""
java = java.replace(OLD_TAIL, NEW_TAIL.replace('");', '");'))

# 修正：Map.of( 的第一个 key 已经被替换成 put，这里补齐 value 的括号
java = java.replace(
    """                headers.put("Content-Security-Policy",
                    "default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; """,
    """                headers.put("Content-Security-Policy",
                    "default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; """,
)

# 2) 启动时清一次缓存
if 'clearCache(true)' not in java:
    anchor = '        webView.loadUrl(HOME);'
    if anchor not in java:
        anchor = '        webView.loadUrl('
        index = java.index(anchor)
        anchor = java[index : java.index('\n', index)]
    java = java.replace(
        anchor,
        '        // 升级后清掉旧缓存，保证加载的是本次安装的资源\n'
        '        webView.clearCache(true);\n'
        '        webView.clearHistory();\n' + anchor,
        1,
    )

JAVA.write_text(java, encoding='utf-8')
print('no-store headers:', 'Cache-Control' in java)
print('clearCache on start:', 'clearCache(true)' in java)
