from pathlib import Path

p = Path('android/app/src/main/java/com/deep/sleep/MainActivity.java')
t = p.read_text(encoding='utf-8')

fixes = [
    ('emitUpdate("error", 0, 0, "下载地址为空");', 'emitUpdate("error", 0, 0, 0, "下载地址为空");'),
    ('emitUpdate("downloading", 0, 0, "");', 'emitUpdate("downloading", 0, 0, 0, "");'),
    ('emitUpdate("ready", 100, apk.length(), "");', 'emitUpdate("ready", 100, apk.length(), apk.length(), "");'),
    ('emitUpdate("error", 0, 0, String.valueOf(error.getMessage()));',
     'emitUpdate("error", 0, 0, 0, String.valueOf(error.getMessage()));'),
    ('emitUpdate("error", 0, 0, "无法启动安装器：" + error.getMessage());',
     'emitUpdate("error", 0, 0, 0, "无法启动安装器：" + error.getMessage());'),
]
for old, new in fixes:
    if old in t:
        t = t.replace(old, new)
        print('fixed:', old[:48])
    else:
        print('MISS:', old[:48])
p.write_text(t, encoding='utf-8')
