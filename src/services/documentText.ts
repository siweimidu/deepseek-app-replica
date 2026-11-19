import { decompressSync, unzipSync } from 'fflate'

/**
 * 本地抽取文档正文（docx / xlsx / pptx / pdf）。
 *
 * 目的：让用户能把文档内容直接发成文本，即使服务端解析失败或文件太大也能读。
 * 只做「尽量拿到可读文本」，不追求版式还原；拿不到时返回空串，由界面提示。
 */

export const TEXT_EXTRACTABLE = ['docx', 'xlsx', 'pptx', 'pdf'] as const

export const extensionOf = (name: string) => (name.split('.').pop() ?? '').toLowerCase()

export const canExtractText = (name: string) =>
  (TEXT_EXTRACTABLE as readonly string[]).includes(extensionOf(name))

const decodeXml = (xml: string) =>
  xml
    .replace(/<w:p[ >]/g, '\n<w:p ')
    .replace(/<a:p[ >]/g, '\n<a:p ')
    .replace(/<w:tab\/>/g, '\t')
    .replace(/<w:br\/>/g, '\n')
    .replace(/<[^>]+>/g, '')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&amp;/g, '&')
    .replace(/&quot;/g, '"')
    .replace(/&apos;/g, "'")
    .replace(/[ \t]+\n/g, '\n')
    .replace(/\n{3,}/g, '\n\n')
    .trim()

const textOfFiles = (files: Record<string, Uint8Array>, matcher: RegExp) => {
  const parts: string[] = []
  for (const [path, data] of Object.entries(files)) {
    if (!matcher.test(path)) {
      continue
    }
    const xml = new TextDecoder('utf-8').decode(data)
    const text = decodeXml(xml)
    if (text) {
      parts.push(text)
    }
  }
  return parts.join('\n\n').trim()
}

const extractOffice = (bytes: Uint8Array, ext: string) => {
  const files = unzipSync(bytes)
  if (ext === 'docx') {
    return textOfFiles(files, /^word\/document\d*\.xml$/)
  }
  if (ext === 'pptx') {
    return textOfFiles(files, /^ppt\/slides\/slide\d+\.xml$/)
  }
  if (ext === 'xlsx') {
    // 共享字符串里是全部文本单元格；数字单元格在 sheet 里，按顺序补上
    const shared = files['xl/sharedStrings.xml']
      ? decodeXml(new TextDecoder('utf-8').decode(files['xl/sharedStrings.xml']))
      : ''
    const sheet = textOfFiles(files, /^xl\/worksheets\/sheet\d+\.xml$/)
    return [shared, sheet].filter(Boolean).join('\n\n').trim()
  }
  return ''
}

/** 从 PDF 内容流里抠文本：支持 FlateDecode，Tj / TJ 两种文本算子 */
const extractPdf = (bytes: Uint8Array) => {
  const latin = new TextDecoder('latin1').decode(bytes)
  const parts: string[] = []
  const streamPattern = /stream\r?\n/g
  let match: RegExpExecArray | null
  while ((match = streamPattern.exec(latin))) {
    const dataStart = match.index + match[0].length
    // 字典里声明的 /Length 最可靠；没有才回退到找 endstream
    const dictStart = Math.max(0, latin.lastIndexOf('<<', match.index))
    const dict = latin.slice(dictStart, match.index)
    const declared = /\/Length\s+(\d+)/.exec(dict)
    let dataEnd: number
    if (declared) {
      dataEnd = dataStart + Number(declared[1])
    } else {
      dataEnd = latin.indexOf('endstream', dataStart)
    }
    if (dataEnd <= dataStart || dataEnd > bytes.length) {
      continue
    }
    const compressed = /\/FlateDecode/.test(dict)
    const raw = bytes.subarray(dataStart, dataEnd)
    let text: string
    try {
      const data = compressed ? decompressSync(raw) : raw
      text = new TextDecoder('latin1').decode(data)
    } catch {
      continue
    }
    if (!/(Tj|TJ)/.test(text)) {
      continue
    }
    const literal = /\((?:\\.|[^\\()])*\)/g
    const tokens = text.match(literal)
    if (!tokens) {
      continue
    }
    for (const token of tokens) {
      const body = token.slice(1, -1)
      const decoded = body
        .replace(/\\([nrt])/g, (_all, ch: string) => (ch === 'n' ? '\n' : ch === 'r' ? '' : '\t'))
        .replace(/\\([0-7]{1,3})/g, (_all, oct: string) => String.fromCharCode(parseInt(oct, 8)))
        .replace(/\\(.)/g, '$1')
      parts.push(decoded)
    }
    parts.push('\n')
  }
  return parts
    .join('')
    .replace(/[ \t]{2,}/g, ' ')
    .replace(/\n{3,}/g, '\n\n')
    .trim()
}

export const extractDocumentText = async (file: File, limit = 12000): Promise<string> => {
  const ext = extensionOf(file.name)
  const buffer = new Uint8Array(await file.arrayBuffer())
  let text = ''
  if (ext === 'pdf') {
    text = extractPdf(buffer)
  } else if (ext === 'docx' || ext === 'xlsx' || ext === 'pptx') {
    text = extractOffice(buffer, ext)
  }
  return text.slice(0, limit)
}
