"""Expose a native build label so the settings page can prove which APK is installed."""

from pathlib import Path

JAVA = Path('android/app/src/main/java/com/deep/sleep/MainActivity.java')
java = JAVA.read_text(encoding='utf-8')
anchor = """        @JavascriptInterface
        public void releaseHistoryDownload(String token) {"""
addition = """        /** 给「版本信息」用：一眼能看出装的是哪个包、哪个构建。 */
        @JavascriptInterface
        public String versionLabel() {
            try {
                android.content.pm.PackageInfo pack =
                    getPackageManager().getPackageInfo(getPackageName(), 0);
                long code = android.os.Build.VERSION.SDK_INT >= 28
                    ? pack.getLongVersionCode() : pack.versionCode;
                return getPackageName() + " · " + pack.versionName + " · " + code;
            } catch (Exception error) {
                return getPackageName();
            }
        }

        @JavascriptInterface
        public void releaseHistoryDownload(String token) {"""
assert anchor in java, 'java anchor missing'
if 'versionLabel' not in java:
    JAVA.write_text(java.replace(anchor, addition, 1), encoding='utf-8')
    print('java versionLabel added')

ANDROID = Path('src/app/android.ts')
bridge = ANDROID.read_text(encoding='utf-8')
if 'versionLabel' not in bridge:
    bridge = bridge.replace(
        '  startHistoryDownload: (url: string) => string',
        '  versionLabel: () => string\n  startHistoryDownload: (url: string) => string',
        1,
    )
    ANDROID.write_text(bridge, encoding='utf-8')
    print('bridge type added')

SETTINGS = Path('src/components/settings/AndroidSettings.tsx')
page = SETTINGS.read_text(encoding='utf-8')
if 'nativeVersion' not in page:
    page = page.replace(
        'const appVersion = document.querySelector<HTMLMetaElement>(',
        'const nativeVersion = android?.versionLabel?.()\nconst appVersion = nativeVersion ?? document.querySelector<HTMLMetaElement>(',
        1,
    )
    SETTINGS.write_text(page, encoding='utf-8')
    print('settings label wired')

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
import re

GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 13', gradle), encoding='utf-8')
print('versionCode 13')
