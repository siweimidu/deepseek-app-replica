"""删除导入完成后的「已导入 N 个对话」提示（顶部条 + toast），以后不再弹出。"""

import re
from pathlib import Path

# 1) 顶部状态条：done 阶段直接不显示，并立即收起任务
BAR = Path('src/components/base/ImportStatusBar.tsx')
bar = BAR.read_text(encoding='utf-8')

bar = bar.replace(
    """  // 完成后再停留一会儿展示结果，然后自动收起。
  useEffect(() => {
    if (phase !== 'done') {
      return
    }
    setShown(true)
    const timer = setTimeout(() => {
      setShown(false)
      dismissImportJob()
    }, 2400)
    return () => clearTimeout(timer)
  }, [phase])

  if (phase === 'idle' || phase === 'error') {
    return null
  }""",
    """  // 导入完成不展示任何结果条：直接把任务收掉，只保留进行中的进度
  useEffect(() => {
    if (phase === 'done') {
      dismissImportJob()
    }
  }, [phase])

  if (phase === 'idle' || phase === 'error' || phase === 'done') {
    return null
  }""",
)
# 去掉不再需要的 translate 导入与 done 文案
bar = bar.replace(
    """  const total = (finished?.added ?? 0) + (finished?.updated ?? 0)
  const label =
    phase === 'done'
      ? translate(total === 1 ? 'historyImportedOne' : 'historyImported', { count: total })
      : phase === 'downloading'
        ? translate('historyImportDownloading', { percent: value })
        : translate('historyImportProgress', { percent: value })""",
    """  const label =
    phase === 'downloading'
      ? translate('historyImportDownloading', { percent: value })
      : translate('historyImportProgress', { percent: value })""",
)
bar = bar.replace("  const { phase, percent, sessions, finished } = useImportJob()", "  const { phase, percent, sessions } = useImportJob()")
BAR.write_text(bar, encoding='utf-8')
print('status bar no longer shows the imported summary')

# 2) 导入完成不再弹 toast
JOB = Path('src/services/chat/importJob.ts')
job = JOB.read_text(encoding='utf-8')
start = job.find('    showToast(')
if start > 0:
    # 找到这个 showToast 调用的结尾
    end = job.find('    )', start) + len('    )\n')
    block = job[start:end]
    if 'historyImported' in block:
        job = job[:start] + job[end:]
        JOB.write_text(job, encoding='utf-8')
        print('completion toast removed')
    else:
        print('unexpected toast block:', block[:80])
else:
    print('toast call not found')
