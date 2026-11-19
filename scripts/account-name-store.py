"""账户名称可修改：设置存储 + 侧边栏显示 + 账号页改名弹窗。"""

import re
from pathlib import Path

# ---------- 1) 设置存储 ----------
SETTINGS = Path('src/services/settings.ts')
s = SETTINGS.read_text(encoding='utf-8')

if 'accountName' not in s:
    s = s.replace(
        "  avatar: string | null",
        "  avatar: string | null\n  /** 自定义账户名称；null 表示用默认的 API Key */\n  accountName: string | null",
        1,
    )
    s = s.replace(
        "  avatar: 'deepsleep:avatar',",
        "  avatar: 'deepsleep:avatar',\n  accountName: 'deepsleep:account-name',",
        1,
    )
    s = s.replace(
        "  avatar: read(KEYS.avatar),",
        "  avatar: read(KEYS.avatar),\n  accountName: read(KEYS.accountName),",
        1,
    )
    anchor = "export const setAvatar = (avatar: string | null) => {"
    s = s.replace(
        anchor,
        """export const setAccountName = (accountName: string | null) => {
  const value = accountName?.trim() ? accountName.trim().slice(0, 20) : null
  if (value) {
    write(KEYS.accountName, value)
  } else {
    remove(KEYS.accountName)
  }
  useSettings.setState({ accountName: value })
}

""" + anchor,
        1,
    )
    SETTINGS.write_text(s, encoding='utf-8')
print('settings store updated:', 'accountName' in s)

# ---------- 2) 侧边栏底部显示 ----------
SIDER = Path('src/components/sider/Sider.tsx')
sider = SIDER.read_text(encoding='utf-8')
if 'accountName' not in sider:
    sider = sider.replace(
        "  const avatar = useSettings((state) => state.avatar)",
        "  const avatar = useSettings((state) => state.avatar)\n  const accountName = useSettings((state) => state.accountName)",
        1,
    )
    sider = sider.replace(
        "              {androidDrawer ? 'API Key' : t('settings')}",
        "              {androidDrawer ? accountName || 'API Key' : t('settings')}",
        1,
    )
    SIDER.write_text(sider, encoding='utf-8')
print('sider shows account name:', 'accountName ||' in sider)

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 69', gradle), encoding='utf-8')
print('versionCode 69')
