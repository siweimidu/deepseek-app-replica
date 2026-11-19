from pathlib import Path

p = Path('src/app/App.tsx')
t = p.read_text(encoding='utf-8')
t = t.replace(
    "import { openImageViewer as __openViewer } from '../components/files/imageViewerState.js'\n",
    '',
)
t = t.replace(
    '  ;(window as unknown as Record<string, unknown>).__dshImageViewer = __openViewer\n',
    '',
)
p.write_text(t, encoding='utf-8')
print('hook removed:', '__dshImageViewer' not in t, '| import removed:', '__openViewer' not in t)
