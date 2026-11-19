"""接入全屏看图：App 挂载组件 + 消息图片可点开。"""

from pathlib import Path

# 1) App 挂载
APP = Path('src/app/App.tsx')
app = APP.read_text(encoding='utf-8')
if 'ImageViewer' not in app:
    app = app.replace(
        "import { ImportStatusBar } from '../components/base/ImportStatusBar.js'",
        "import { ImportStatusBar } from '../components/base/ImportStatusBar.js'\nimport { ImageViewer } from '../components/files/ImageViewer.js'",
        1,
    )
    # 挂到 frame 结束之前
    marker = "      </div>\n    </div>\n  )"
    if marker in app:
        app = app.replace(marker, "        <ImageViewer />\n" + marker, 1)
    else:
        # 兜底：放在最后一个 </div> 之前
        idx = app.rindex('</div>')
        app = app[:idx] + '  <ImageViewer />\n' + app[idx:]
    APP.write_text(app, encoding='utf-8')
print('ImageViewer mounted:', 'ImageViewer' in app)

# 2) 消息图片可点开
FILE = Path('src/components/messages/MessageFile.tsx')
src = FILE.read_text(encoding='utf-8')
if 'openImageViewer' not in src:
    src = src.replace(
        "import styles from './MessageFile.module.css'",
        "import { openImageViewer } from '../files/imageViewerState.js'\nimport styles from './MessageFile.module.css'",
        1,
    )
    src = src.replace(
        "        <img src={url} alt={file.name} onError={() => setFailedUrl(url)} />",
        """        <img
          src={url}
          alt={file.name}
          onError={() => setFailedUrl(url)}
          onClick={() => openImageViewer(url, file.name)}
        />""",
        1,
    )
    FILE.write_text(src, encoding='utf-8')
print('message image opens viewer:', 'openImageViewer' in src)
