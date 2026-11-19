"""1) 彻底去掉「已导入 N 个对话」提示（顶部条/toast/设置页状态行）
2) 大文件下载不再被固定 60 秒掐断，改成"无进展 90 秒"才算超时
"""

from pathlib import Path

# ---- 1) 任务完成不再进入 done 状态 ----
JOB = Path('src/services/chat/importJob.ts')
job = JOB.read_text(encoding='utf-8')
job = job.replace(
    "      await task(report)\n      useImportJob.setState({ phase: 'done', percent: 1 })",
    "      await task(report)\n      // 完成后直接回到 idle：不显示任何「已导入 N 个对话」提示\n      useImportJob.setState({ ...IDLE })",
    1,
)
JOB.write_text(job, encoding='utf-8')
print('job: done state removed')

# ---- 2) 设置页（桌面版）不再显示导入结果行 ----
DIALOG = Path('src/components/settings/SettingsDialog.tsx')
src = DIALOG.read_text(encoding='utf-8')
src = src.replace(
    """      const outcome = await importHistory(file)
      const count = outcome.added + outcome.updated
      setStatus({ key: count === 1 ? 'historyImportedOne' : 'historyImported', params: { count } })""",
    """      await importHistory(file)""",
    1,
)
DIALOG.write_text(src, encoding='utf-8')
print('settings dialog: import status line removed')

# ---- 3) 大文件：看门狗改为“无进展才超时” ----
ANDROID = Path('src/app/android.ts')
src = ANDROID.read_text(encoding='utf-8')
src = src.replace(
    "/** 原生下载最长等待，超时就报错，避免界面一直没反应 */\nconst DOWNLOAD_TIMEOUT_MS = 60_000",
    "/** 多久没有新进展就算超时（大包可能几十 MB，不能按总时长掐） */\nconst DOWNLOAD_IDLE_TIMEOUT_MS = 90_000",
    1,
)
src = src.replace(
    """    const watchdog = window.setTimeout(() => {
      window.removeEventListener('android-download', listen)
      reject(new Error('下载超时，请检查链接是否过期'))
    }, DOWNLOAD_TIMEOUT_MS)""",
    """    let watchdog = 0
    const armWatchdog = () => {
      window.clearTimeout(watchdog)
      watchdog = window.setTimeout(() => {
        window.removeEventListener('android-download', listen)
        reject(new Error('下载超时，请检查链接是否过期'))
      }, DOWNLOAD_IDLE_TIMEOUT_MS)
    }
    armWatchdog()""",
    1,
)
src = src.replace(
    """      if (detail.state === 'progress') {
        onProgress(detail.loaded, detail.total)
        return
      }""",
    """      if (detail.state === 'progress') {
        // 每来一块进度就重新计时，46MB 这种大包也不会被误判超时
        armWatchdog()
        onProgress(detail.loaded, detail.total)
        return
      }""",
    1,
)
ANDROID.write_text(src, encoding='utf-8')
print('js: idle-based watchdog')

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
import re

GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 73', gradle), encoding='utf-8')
print('versionCode 73')
