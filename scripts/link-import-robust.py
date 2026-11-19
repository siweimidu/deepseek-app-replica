"""从链接导入的健壮性：
1) 原生下载用原始 URL 字符串（避免 Uri.toString() 重编码破坏签名）
2) JS 侧加超时看门狗，永不静默卡住
"""

import re
from pathlib import Path

JAVA = Path('android/app/src/main/java/com/deep/sleep/MainActivity.java')
java = JAVA.read_text(encoding='utf-8')

OLD = """            String token = Long.toHexString(System.nanoTime());
            File target = downloadFile(token);
            downloads.put(token, target);
            startDownload(token, uri.toString());
            return token;"""
NEW = """            String token = Long.toHexString(System.nanoTime());
            File target = downloadFile(token);
            downloads.put(token, target);
            // 用原始字符串下载：签名链接的 query 一旦被重新编码就会 403
            startDownload(token, address == null ? "" : address.trim());
            return token;"""
assert OLD in java, 'startHistoryDownload body not found'
java = java.replace(OLD, NEW, 1)

# emitDownload 增加异常兜底日志
java = java.replace(
    "        runOnUiThread(() -> webView.evaluateJavascript(script, null));",
    """        android.util.Log.d("DeepSleep", "download " + token + " " + state + " " + message);
        runOnUiThread(() -> webView.evaluateJavascript(script, null));""",
    1,
)
JAVA.write_text(java, encoding='utf-8')
print('java: raw url + log')

# JS 侧：超时看门狗
ANDROID = Path('src/app/android.ts')
src = ANDROID.read_text(encoding='utf-8')
if 'DOWNLOAD_TIMEOUT_MS' not in src:
    src = src.replace(
        "export const downloadAndroidHistory = (",
        "/** 原生下载最长等待，超时就报错，避免界面一直没反应 */\nconst DOWNLOAD_TIMEOUT_MS = 60_000\n\nexport const downloadAndroidHistory = (",
        1,
    )
    src = src.replace(
        "    window.addEventListener('android-download', listen)",
        """    const watchdog = window.setTimeout(() => {
      window.removeEventListener('android-download', listen)
      reject(new Error('下载超时，请检查链接是否过期'))
    }, DOWNLOAD_TIMEOUT_MS)
    window.addEventListener('android-download', listen)""",
        1,
    )
    ANDROID.write_text(src, encoding='utf-8')
print('js watchdog added:', 'DOWNLOAD_TIMEOUT_MS' in src)

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 71', gradle), encoding='utf-8')
print('versionCode 71')
