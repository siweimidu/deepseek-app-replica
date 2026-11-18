// 复刻 useDrawerSwipe 的判定，验证"任一方向横滑都能切换"
const W = 321.6
const SLOP = 8
const RATIO = 1.15
const TRIGGER_PX = 24
const OPEN_RATIO = 0.12
const CLOSE_PX = 22

const simulate = (openedAtStart, dx, dy = 2) => {
  let phase = 'pending'
  let follow = false
  let progress = openedAtStart ? 1 : 0

  // touchmove
  const horizontal = Math.abs(dx) > Math.abs(dy) * RATIO
  if (!horizontal || (Math.abs(dx) < SLOP && Math.abs(dy) < SLOP)) {
    return openedAtStart ? 'stay-open' : 'stay-closed'
  }
  phase = 'dragging'
  follow = !openedAtStart && dx > 0

  if (follow) {
    progress = dx / W
    // touchend
    return progress > OPEN_RATIO ? 'open' : 'stay-closed'
  }

  if (Math.abs(dx) > TRIGGER_PX) {
    return openedAtStart ? 'close' : 'open'
  }
  return openedAtStart ? 'stay-open' : 'stay-closed'
}

const cases = [
  ['对话页 左滑 60px → 打开', false, -60, 'open'],
  ['对话页 右滑 60px → 打开', false, 60, 'open'],
  ['对话页 右滑 20px → 不动', false, 20, 'stay-closed'],
  ['对话页 左滑 20px → 不动', false, -20, 'stay-closed'],
  ['抽屉 左滑 30px → 关闭', true, -30, 'close'],
  ['抽屉 右滑 30px → 关闭', true, 30, 'close'],
  ['抽屉 竖直滑动 → 不动', true, 3, 'stay-open'],
  ['对话页 竖直滑动 → 不动', false, 4, 'stay-closed'],
]

let failed = 0
for (const [name, opened, dx, expect] of cases) {
  const actual = simulate(opened, dx, name.includes('竖直') ? 30 : 2)
  const ok = actual === expect
  if (!ok) failed += 1
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${name.padEnd(26)} → ${actual}`)
}
console.log(failed === 0 ? 'ALL PASS' : `${failed} FAILED`)
