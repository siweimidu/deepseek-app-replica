// 验证重写后的手势规则：对话页只能左滑打开，侧边栏只能右滑关闭
const W = 321.6
const SLOP = 8
const RATIO = 1.2
const OPEN_PX = 28
const CLOSE_PX = 28
const OPEN_RATIO = 0.18
const CLOSE_RATIO = 0.82

const run = (opened, dx, dy = 2) => {
  // pending 判定
  if (Math.abs(dx) < SLOP && Math.abs(dy) < SLOP) return opened ? 'stay-open' : 'stay-closed'
  if (Math.abs(dx) <= Math.abs(dy) * RATIO) return opened ? 'stay-open' : 'stay-closed'

  let phase = 'none'
  if (!opened && dx < 0) phase = 'opening'
  else if (opened && dx > 0) phase = 'closing'
  if (phase === 'none') return opened ? 'stay-open' : 'stay-closed'

  const progress = phase === 'opening' ? -dx / W : 1 - dx / W
  if (phase === 'opening') {
    const travelled = progress * W
    return travelled >= OPEN_PX || progress > OPEN_RATIO ? 'open' : 'stay-closed'
  }
  const travelled = (1 - progress) * W
  return travelled >= CLOSE_PX || progress < CLOSE_RATIO ? 'close' : 'stay-open'
}

const cases = [
  ['对话页 左滑 60px → 打开', false, -60, 'open'],
  ['对话页 左滑 30px → 打开', false, -30, 'open'],
  ['对话页 右滑 60px → 不开', false, 60, 'stay-closed'],
  ['对话页 左滑 20px → 不动', false, -20, 'stay-closed'],
  ['侧边栏 右滑 60px → 关闭', true, 60, 'close'],
  ['侧边栏 右滑 30px → 关闭', true, 30, 'close'],
  ['侧边栏 左滑 60px → 不关', true, -60, 'stay-open'],
  ['侧边栏 右滑 20px → 不动', true, 20, 'stay-open'],
  ['对话页 竖直滑动 → 不动', false, 4, 'stay-closed'],
  ['侧边栏 竖直滑动 → 不动', true, 4, 'stay-open'],
]

let failed = 0
for (const [name, opened, dx, expect] of cases) {
  const actual = run(opened, dx, name.includes('竖直') ? 30 : 2)
  const ok = actual === expect
  if (!ok) failed += 1
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${name.padEnd(24)} → ${actual}`)
}
console.log(failed === 0 ? 'ALL PASS' : `${failed} FAILED`)
