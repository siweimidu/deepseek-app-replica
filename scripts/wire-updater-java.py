"""应用内更新：清单权限 + FileProvider + MainActivity 桥方法。"""

from pathlib import Path

# ---------- 1) AndroidManifest ----------
MANIFEST = Path('android/app/src/main/AndroidManifest.xml')
xml = MANIFEST.read_text(encoding='utf-8')
if 'REQUEST_INSTALL_PACKAGES' not in xml:
    xml = xml.replace(
        '    <uses-permission android:name="android.permission.INTERNET" />',
        '    <uses-permission android:name="android.permission.INTERNET" />\n'
        '    <uses-permission android:name="android.permission.REQUEST_INSTALL_PACKAGES" />',
        1,
    )
if 'UpdateProvider' not in xml:
    xml = xml.replace(
        '        <provider\n            android:name=".CaptureProvider"',
        '        <provider\n'
        '            android:name="androidx.core.content.FileProvider"\n'
        '            android:authorities="${applicationId}.update"\n'
        '            android:exported="false"\n'
        '            android:grantUriPermissions="true">\n'
        '            <meta-data\n'
        '                android:name="android.support.FILE_PROVIDER_PATHS"\n'
        '                android:resource="@xml/update_paths" />\n'
        '        </provider>\n'
        '        <provider\n            android:name=".CaptureProvider"',
        1,
    )
MANIFEST.write_text(xml, encoding='utf-8')
print('manifest:', 'REQUEST_INSTALL_PACKAGES' in xml, '| FileProvider:', '${applicationId}.update' in xml)

# ---------- 2) MainActivity 桥方法 ----------
JAVA = Path('android/app/src/main/java/com/deep/sleep/MainActivity.java')
java = JAVA.read_text(encoding='utf-8')

if 'checkAppUpdate' not in java:
    bridge = '''
        /** 查询 GitHub 最新版本，返回 JSON（ok/tag/notes/url/size/current/error） */
        @JavascriptInterface
        public String checkAppUpdate() {
            return AppUpdater.check(MainActivity.this);
        }

        /** 下载并调用系统安装器；进度通过 android-update 事件回传 */
        @JavascriptInterface
        public void installAppUpdate(String address) {
            if (address == null || address.trim().isEmpty()) {
                emitUpdate("error", 0, 0, "下载地址为空");
                return;
            }
            emitUpdate("downloading", 0, 0, "");
            downloadExecutor.execute(() -> {
                try {
                    File apk = AppUpdater.download(MainActivity.this, address.trim(),
                        (percent, loaded, total) -> emitUpdate("progress", percent, loaded, total, ""));
                    emitUpdate("ready", 100, apk.length(), "");
                    runOnUiThread(() -> launchInstaller(apk));
                } catch (Exception error) {
                    emitUpdate("error", 0, 0, String.valueOf(error.getMessage()));
                }
            });
        }

        /** 当前安装包的 versionCode / versionName，设置页展示用 */
        @JavascriptInterface
        public String appVersionInfo() {
            return AppUpdater.currentVersionCode(MainActivity.this) + "|"
                + AppUpdater.currentVersionName(MainActivity.this);
        }

        /** 系统「安装未知应用」开关页；部分机型直接落到应用详情 */
        @JavascriptInterface
        public void openInstallPermission() {
            runOnUiThread(() -> {
                try {
                    Intent intent = new Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES,
                        Uri.parse("package:" + getPackageName()));
                    intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                    startActivity(intent);
                } catch (Exception error) {
                    try {
                        Intent fallback = new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS,
                            Uri.parse("package:" + getPackageName()));
                        fallback.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                        startActivity(fallback);
                    } catch (Exception ignored) {
                        // 无能为力时保持静默，前端会提示手动安装
                    }
                }
            });
        }

        /** 用系统安装器安装已下载的 APK */
        private void launchInstaller(File apk) {
            try {
                Uri uri = androidx.core.content.FileProvider.getUriForFile(
                    MainActivity.this, getPackageName() + ".update", apk);
                Intent intent = new Intent(Intent.ACTION_VIEW);
                intent.setDataAndType(uri, "application/vnd.android.package-archive");
                intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
                startActivity(intent);
            } catch (Exception error) {
                emitUpdate("error", 0, 0, "无法启动安装器：" + error.getMessage());
            }
        }

        private void emitUpdate(String state, int percent, long loaded, long total, String message) {
            String script = "window.dispatchEvent(new CustomEvent('android-update',{detail:{"
                + "state:'" + escapeJs(state) + "',percent:" + percent
                + ",loaded:" + loaded + ",total:" + total
                + ",message:'" + escapeJs(message) + "'}}))";
            runOnUiThread(() -> webView.evaluateJavascript(script, null));
        }
'''
    marker = '        @JavascriptInterface\n        public void releaseHistoryDownload(String token) {'
    assert marker in java, 'bridge anchor not found'
    java = java.replace(marker, bridge.strip('\n') + '\n\n' + marker, 1)
    JAVA.write_text(java, encoding='utf-8')
print('bridge added:', 'checkAppUpdate' in java)

# ---------- 3) 依赖 androidx.core（FileProvider） ----------
GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
if 'androidx.core:core' not in gradle:
    gradle = gradle.replace(
        'dependencies {',
        'dependencies {\n    implementation "androidx.core:core:1.13.1"',
        1,
    )
    GRADLE.write_text(gradle, encoding='utf-8')
print('androidx.core dep:', 'androidx.core:core' in gradle)
