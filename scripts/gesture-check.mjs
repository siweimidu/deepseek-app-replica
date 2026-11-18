// 用同样的判定公式跑几组手势，确认逻辑正确（不是靠感觉）
const W = 321.6
const CLOSE_PX = 22
const OPEN_RATIO = 0.12

const decide = (openedAtStart, dx) => {
  const progress = openedAtStart ? 1 + dx / W : dx / W
  const clamped = Math.max(0, Math.min(1, progress))
  if (openedAtStart) {
    const travelled = (progress - 1) * W
    return { progress: clamped, action: travelled < -CLOSE_PX || progress < 0.8 ? 'close' : 'stay-open' }
  }
  return { progress: clamped, action: progress > OPEN_RATIO ? 'open' : 'stay-closed' }
}

const cases = [
  ['打开 + 左滑 30px', true, -30],
  ['打开 + 左滑 120px', true, -120],
  ['打开 + 左滑 21px（小于阈值）', true, -21],
  ['打开 + 右滑 40px', true, 40],
  ['关闭 + 右滑 80px', false, 80],
  ['关闭 + 右滑 20px（不够）', false, 20],
  ['关闭 + 左滑 60px（不应打开）', false, -60],
]

let failed = 0
for (const [name, openedAtStart, dx] of cases) {
  const result = decide(openedAtStart, dx)
  const expectClose = name.includes('30px') || name.includes('120px')
  const expectOpen = name.includes('右滑 80px')
  const ok =
    (expectClose && result.action === 'close') ||
    (expectOpen && result.action === 'open') ||
    (!expectClose && !expectOpen && result.action.startsWith('stay'))
  if (!ok) failed += 1
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${name.padEnd(28)} progress=${result.progress.toFixed(2)} → ${result.action}`)
}
console.log(failed === 0 ? 'ALL PASS' : `${failed} FAILED`)
