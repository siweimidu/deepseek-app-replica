"""PDF 提取改用字典里的 /Length 切流，避免文本下标错位。"""

from pathlib import Path

p = Path('src/services/documentText.ts')
src = p.read_text(encoding='utf-8')

OLD_START = src.index('/** 从 PDF 内容流里抠文本')
OLD_END = src.index('export const extractDocumentText')
NEW = '''/** 从 PDF 内容流里抠文本：支持 FlateDecode，Tj / TJ 两种文本算子 */
const extractPdf = (bytes: Uint8Array) => {
  const latin = new TextDecoder('latin1').decode(bytes)
  const parts: string[] = []
  const streamPattern = /stream\\r?\\n/g
  let match: RegExpExecArray | null
  while ((match = streamPattern.exec(latin))) {
    const dataStart = match.index + match[0].length
    // 字典里声明的 /Length 最可靠；没有才回退到找 endstream
    const dictStart = Math.max(0, latin.lastIndexOf('<<', match.index))
    const dict = latin.slice(dictStart, match.index)
    const declared = /\\/Length\\s+(\\d+)/.exec(dict)
    let dataEnd: number
    if (declared) {
      dataEnd = dataStart + Number(declared[1])
    } else {
      dataEnd = latin.indexOf('endstream', dataStart)
    }
    if (dataEnd <= dataStart || dataEnd > bytes.length) {
      continue
    }
    const compressed = /\\/FlateDecode/.test(dict)
    const raw = bytes.subarray(dataStart, dataEnd)
    let text: string
    try {
      const data = compressed ? inflateSync(raw) : raw
      text = new TextDecoder('latin1').decode(data)
    } catch {
      continue
    }
    if (!/(Tj|TJ)/.test(text)) {
      continue
    }
    const literal = /\\((?:\\\\.|[^\\\\()])*\\)/g
    const tokens = text.match(literal)
    if (!tokens) {
      continue
    }
    for (const token of tokens) {
      const body = token.slice(1, -1)
      const decoded = body
        .replace(/\\\\([nrt])/g, (_all, ch: string) => (ch === 'n' ? '\\n' : ch === 'r' ? '' : '\\t'))
        .replace(/\\\\([0-7]{1,3})/g, (_all, oct: string) => String.fromCharCode(parseInt(oct, 8)))
        .replace(/\\\\(.)/g, '$1')
      parts.push(decoded)
    }
    parts.push('\\n')
  }
  return parts
    .join('')
    .replace(/[ \\t]{2,}/g, ' ')
    .replace(/\\n{3,}/g, '\\n\\n')
    .trim()
}

'''
src = src[:OLD_START] + NEW + src[OLD_END:]
p.write_text(src, encoding='utf-8')
print('pdf extractor uses /Length:', 'declared' in src)
