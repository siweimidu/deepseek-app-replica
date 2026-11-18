// 验证 planContext 的窗口行为（与 budget.ts 中的常量/算法一致）
const WINDOW = 128_000
const RESERVE = 8_000
const TRIGGER = Math.floor((WINDOW - RESERVE) * 0.75)
const TARGET = Math.floor((WINDOW - RESERVE) * 0.36)

const plan = (rounds, measured = 0) => {
  const total = rounds.reduce((sum, cost) => sum + cost, 0)
  const estimate = measured > 0 ? measured + rounds[rounds.length - 1] : total
  if (estimate <= TRIGGER || rounds.length <= 2) {
    return { kept: rounds.length, estimate, compacted: false }
  }
  let kept = 1
  let sum = rounds[0]
  for (let index = rounds.length - 1; index >= 1; index -= 1) {
    if (sum + rounds[index] > TARGET) break
    sum += rounds[index]
    kept += 1
  }
  return { kept, estimate: sum, compacted: true }
}

const make = (count, cost) => Array.from({ length: count }, () => cost)
const cases = []

// 1) 常规 20 轮不压缩
cases.push(['20 轮 × 1K → 原样发送', plan(make(20, 1000)), (r) => !r.compacted && r.kept === 20])
// 2) 120 轮触发压缩
cases.push(['120 轮 × 1K → 压缩', plan(make(120, 1000)), (r) => r.compacted && r.estimate <= TARGET])
// 3) 压缩后剩余空间够几十轮
cases.push(
  ['压缩后 ≤ 目标线', plan(make(120, 1000)), (r) => r.estimate <= TARGET && r.kept > 1]
)
// 4) 真实用量作为基线
cases.push([
  '上轮实测 100K → 压缩',
  plan(make(100, 1000), 100_000),
  (r) => r.compacted && r.estimate <= TARGET,
])
// 5) 首轮永远保留
cases.push(['首轮（大）保留', plan([30_000, ...make(100, 1000)]), (r) => r.kept >= 2])

let failed = 0
for (const [name, result, check] of cases) {
  const ok = check(result)
  if (!ok) failed += 1
  console.log(
    `${ok ? 'PASS' : 'FAIL'}  ${name.padEnd(24)} kept=${result.kept} est=${Math.round(
      result.estimate / 1000
    )}K compacted=${result.compacted}`
  )
}
console.log(`trigger=${TRIGGER / 1000}K target=${TARGET / 1000}K`)
console.log(failed === 0 ? 'ALL PASS' : `${failed} FAILED`)
