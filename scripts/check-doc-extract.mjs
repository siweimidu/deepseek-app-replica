import { unzipSync, decompressSync } from 'fflate'
import { readFileSync } from 'node:fs'

/** 与 src/services/documentText.ts 同逻辑的离线校验（用于确认算法，不替代浏览器验证） */

const dir = '../out/fixtures/'

const decodeXml = (xml) =>
  xml
    .replace(/<w:p[ >]/g, '\n<w:p ')
    .replace(/<a:p[ >]/g, '\n<a:p ')
    .replace(/<w:tab\/>/g, '\t')
    .replace(/<w:br\/>/g, '\n')
    .replace(/<[^>]+>/g, '')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&amp;/g, '&')
    .replace(/[ \t]+\n/g, '\n')
    .replace(/\n{3,}/g, '\n\n')
    .trim()

const office = (path, matcher) => {
  const files = unzipSync(new Uint8Array(readFileSync(dir + path)))
  return Object.entries(files)
    .filter(([name]) => matcher.test(name))
    .map(([, data]) => decodeXml(new TextDecoder('utf-8').decode(data)))
    .filter(Boolean)
    .join('\n\n')
}

const pdf = (path) => {
  const bytes = new Uint8Array(readFileSync(dir + path))
  const latin = new TextDecoder('latin1').decode(bytes)
  const out = []
  const rx = /stream\r?\n/g
  let m
  while ((m = rx.exec(latin))) {
    const dataStart = m.index + m[0].length
    const dictStart = Math.max(0, latin.lastIndexOf('<<', m.index))
    const dict = latin.slice(dictStart, m.index)
    const declared = /\/Length\s+(\d+)/.exec(dict)
    const dataEnd = declared ? dataStart + Number(declared[1]) : latin.indexOf('endstream', dataStart)
    if (dataEnd <= dataStart) continue
    const compressed = /\/FlateDecode/.test(dict)
    if (path.includes('flate')) {
      console.log('  [debug] declared=', declared && declared[1], 'slice=', dataEnd - dataStart, 'compressed=', compressed)
    }
    let text
    try {
      text = new TextDecoder('latin1').decode(
        compressed ? decompressSync(bytes.subarray(dataStart, dataEnd)) : bytes.subarray(dataStart, dataEnd)
      )
    } catch (error) {
      if (path.includes('flate')) console.log('  [debug] inflate error:', String(error && error.message))
      continue
    }
    if (!/(Tj|TJ)/.test(text)) continue
    const tokens = text.match(/\((?:\\.|[^\\()])*\)/g) ?? []
    for (const t of tokens) out.push(t.slice(1, -1))
    out.push('\n')
  }
  return out.join('').trim()
}

console.log('docx  →', JSON.stringify(office('test-doc.docx', /^word\/document\d*\.xml$/).slice(0, 60)))
console.log('pptx  →', JSON.stringify(office('test-deck.pptx', /^ppt\/slides\/slide\d+\.xml$/).slice(0, 60)))
console.log('xlsx  →', JSON.stringify(office('test-sheet.xlsx', /^xl\/sharedStrings\.xml$|^xl\/worksheets\/sheet\d+\.xml$/).slice(0, 60)))
console.log('pdf明文 →', JSON.stringify(pdf('test-plain.pdf').slice(0, 60)))
console.log('pdf压缩 →', JSON.stringify(pdf('test-flate.pdf').slice(0, 60)))
