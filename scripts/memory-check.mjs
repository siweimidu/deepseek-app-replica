// 校验账本拼接格式（与 memory.ts 的 withMemory 规则一致）
const withMemory = (system, blocks) => {
  if (!blocks?.length) return system
  const body = blocks
    .map((b) => `#${b.index}（第 ${b.fromRound}-${b.toRound} 轮）\n${b.text}`)
    .join('\n\n')
  return `${system}\n\n<memory_log>\n${body}\n</memory_log>`
}

const system = '该助手为DeepSeek。\n\n<session_anchor>\n开头：用户在做 DeepSleep\n</session_anchor>'
const blocks = [
  { index: 1, fromRound: 0, toRound: 20, text: '事实：做 Android 复刻\n决定：包名 com.deep.sleep\n偏好：要 1:1\n待办：动画' },
  { index: 2, fromRound: 20, toRound: 40, text: '事实：修横滑\n决定：用 build47 实现\n偏好：要快\n待办：无' },
]

const out = withMemory(system, blocks)
console.log('--- 拼接结果 ---')
console.log(out)
console.log('--- 校验 ---')
const checks = [
  ['锚点卡在最前', out.indexOf('<session_anchor>') < out.indexOf('<memory_log>')],
  ['块按编号顺序', out.indexOf('#1（') < out.indexOf('#2（')],
  ['块含轮次区间', out.includes('第 0-20 轮') && out.includes('第 20-40 轮')],
  ['无块时原样返回系统提示', withMemory(system, undefined) === system],
  ['旧块内容不被改写', out.includes('包名 com.deep.sleep')],
]
let failed = 0
for (const [name, ok] of checks) {
  if (!ok) failed += 1
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}`)
}
console.log(failed === 0 ? 'ALL PASS' : `${failed} FAILED`)
