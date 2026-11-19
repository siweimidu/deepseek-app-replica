import zipfile
import zlib
from pathlib import Path

dist = Path('dist')

# ---- docx：word/document.xml 里放可识别字符串 ----
doc_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:body>
  <w:p><w:r><w:t>DEEPSLEEP_DOCX_MARKER_第一段正文</w:t></w:r></w:p>
  <w:p><w:r><w:t>DEEPSLEEP_DOCX_SECOND_第二段正文</w:t></w:r></w:p>
</w:body></w:document>'''

with zipfile.ZipFile(dist / 'test-doc.docx', 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('[Content_Types].xml', '<?xml version="1.0"?><Types/>')
    z.writestr('word/document.xml', doc_xml)
print('docx:', (dist / 'test-doc.docx').stat().st_size, 'bytes')

# ---- pptx ----
slide = '''<?xml version="1.0" encoding="UTF-8"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
<a:p><a:r><a:t>DEEPSLEEP_PPTX_MARKER_第一页</a:t></a:r></a:p></a:sld>'''
with zipfile.ZipFile(dist / 'test-deck.pptx', 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('ppt/slides/slide1.xml', slide)
print('pptx:', (dist / 'test-deck.pptx').stat().st_size, 'bytes')

# ---- xlsx：sharedStrings ----
shared = '''<?xml version="1.0" encoding="UTF-8"?>
<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<si><t>DEEPSLEEP_XLSX_MARKER_单元格</t></si></sst>'''
with zipfile.ZipFile(dist / 'test-sheet.xlsx', 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('xl/sharedStrings.xml', shared)
print('xlsx:', (dist / 'test-sheet.xlsx').stat().st_size, 'bytes')

# ---- PDF：明文流 ----
stream = b'BT /F1 12 Tf 72 720 Td (DEEPSLEEP_PDF_MARKER_plain) Tj ET'
pdf = (b'%PDF-1.4\n1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n'
       b'2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n'
       b'3 0 obj << /Type /Page /Parent 2 0 R /Contents 4 0 R >> endobj\n'
       b'4 0 obj << /Length ' + str(len(stream)).encode() + b' >>\nstream\n'
       + stream + b'\nendstream endobj\ntrailer << /Root 1 0 R >>\n%%EOF\n')
(dist / 'test-plain.pdf').write_bytes(pdf)
print('pdf plain:', len(pdf), 'bytes')

# ---- PDF：FlateDecode 压缩流 ----
compressed = zlib.compress(stream)
pdf2 = (b'%PDF-1.4\n1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n'
        b'2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n'
        b'3 0 obj << /Type /Page /Parent 2 0 R /Contents 4 0 R >> endobj\n'
        b'4 0 obj << /Length ' + str(len(compressed)).encode() + b' /Filter /FlateDecode >>\nstream\n'
        + compressed + b'\nendstream endobj\ntrailer << /Root 1 0 R >>\n%%EOF\n')
(dist / 'test-flate.pdf').write_bytes(pdf2)
print('pdf flate:', len(pdf2), 'bytes')
