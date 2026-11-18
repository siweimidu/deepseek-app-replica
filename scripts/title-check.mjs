// 复刻 store.ts 里的 buildTitle 规则，验证 13 字截断与省略号
const TITLE_LIMIT = 13

const cleanForTitle = (text) =>
  text
    .replace(/```[\s\S]*?```/g, ' ')
    .replace(/`[^`]*`/g, ' ')
    .replace(/!?\[[^\]]*\]\([^)]*\)/g, ' ')
    .replace(/^[#>*\-\s]+/gm, '')
    .replace(/\s+/g, ' ')
    .trim()

const buildTitle = (firstUserText) => {
  const text = cleanForTitle(firstUserText)
  if (!text) return ''
  const head = text.split(/[。！？!?；;]/)[0] ?? text
  const source = head.length >= 4 ? head : text
  const chars = Array.from(source)
  if (chars.length <= TITLE_LIMIT) {
    return source.replace(/[，,、：:\s]+$/, '')
  }
  return `${chars.slice(0, TITLE_LIMIT).join('').replace(/[，,、：:\s]+$/, '')}…`
}

const cases = [
  ['帮我写一个 Python 脚本，把目录下所有图片按拍摄时间重命名', 14],
  ['你好', 2],
  ['```js\nconsole.log(1)\n```\n这段代码为什么报错？', 13],
  ['为什么我的 Blender 渲染出来全是噪点呢', 13],
  ['', 0],
  ['# 标题\n\n正文内容在这里，还有更多文字需要被截断处理', 13],
]

let failed = 0
for (const [input, max] of cases) {
  const out = buildTitle(input)
  const len = Array.from(out).length
  const ok = len <= max + 1 // 允许末尾省略号多一个字符
  if (!ok) failed += 1
  console.log(`${ok ? 'PASS' : 'FAIL'}  「${String(input).slice(0, 22).replace(/\n/g, '⏎')}…」 → 「${out}」 (${len} 字)`)
}
console.log(failed === 0 ? 'ALL PASS' : `${failed} FAILED`)
