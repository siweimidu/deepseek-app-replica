"""把 androidx FileProvider 换成自写的 UpdateProvider，并把安装 URI 改成直接用 content scheme。"""

from pathlib import Path

# ---------- Manifest ----------
MANIFEST = Path('android/app/src/main/AndroidManifest.xml')
xml = MANIFEST.read_text(encoding='utf-8')
xml = xml.replace(
    '''        <provider
            android:name="androidx.core.content.FileProvider"
            android:authorities="${applicationId}.update"
            android:exported="false"
            android:grantUriPermissions="true">
            <meta-data
                android:name="android.support.FILE_PROVIDER_PATHS"
                android:resource="@xml/update_paths" />
        </provider>
''',
    '''        <provider
            android:name=".UpdateProvider"
            android:authorities="${applicationId}.update"
            android:exported="false"
            android:grantUriPermissions="true" />
''',
)
MANIFEST.write_text(xml, encoding='utf-8')
print('manifest UpdateProvider:', '.UpdateProvider' in xml, '| androidx removed:', 'androidx.core' not in xml)

# ---------- MainActivity ----------
JAVA = Path('android/app/src/main/java/com/deep/sleep/MainActivity.java')
java = JAVA.read_text(encoding='utf-8')
old = '''                Uri uri = androidx.core.content.FileProvider.getUriForFile(
                    MainActivity.this, getPackageName() + ".update", apk);'''
new = '''                Uri uri = new Uri.Builder()
                    .scheme("content")
                    .authority(getPackageName() + ".update")
                    .appendPath(apk.getName())
                    .build();
                grantUriPermission("com.android.packageinstaller", uri,
                    Intent.FLAG_GRANT_READ_URI_PERMISSION);
                grantUriPermission("com.google.android.packageinstaller", uri,
                    Intent.FLAG_GRANT_READ_URI_PERMISSION);'''
assert old in java, 'installer uri block not found'
java = java.replace(old, new, 1)
JAVA.write_text(java, encoding='utf-8')
print('androidx usage removed:', 'androidx.' not in java)

# ---------- 清掉不再使用的 xml ----------
paths = Path('android/app/src/main/res/xml/update_paths.xml')
if paths.exists():
    paths.unlink()
    print('removed update_paths.xml')
