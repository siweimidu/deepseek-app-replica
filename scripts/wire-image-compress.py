"""把压缩管线接进草稿附件：图片先压缩再上传，预览仍用原图。"""

from pathlib import Path

DRAFTS = Path('src/services/chat/drafts.ts')
src = DRAFTS.read_text(encoding='utf-8')

if 'compressImage' not in src:
    # 1) 引入
    anchor = "import { validateFiles, resolveMimeType, isImage } from '../attachments.js'"
    if anchor not in src:
        # 兜底：找一条来自 attachments 的 import
        import re

        m = re.search(r"import \{[^}]*\} from '[^']*attachments\.js'\n", src)
        assert m, 'attachments import not found'
        anchor = m.group(0).rstrip('\n')
    src = src.replace(anchor, anchor + "\nimport { compressImage } from '../imageUpload.js'", 1)

    # 2) 上传前压缩
    src = src.replace(
        """  updateDraft(sessionId, (draft) => ({ ...draft, attachments: [...draft.attachments, ...added] }))
  added.forEach((attachment) => upload(attachment, apiKey))
  return null""",
        """  updateDraft(sessionId, (draft) => ({ ...draft, attachments: [...draft.attachments, ...added] }))
  added.forEach((attachment) => {
    // 图片可能很大：先本地压一次再上传，预览 URL 仍是原图
    void (async () => {
      if (attachment.isImage) {
        const next = await compressImage(attachment.file)
        if (next !== attachment.file) {
          updateDraft(sessionId, (draft) => ({
            ...draft,
            attachments: draft.attachments.map((item) =>
              item.id === attachment.id ? { ...item, file: next } : item
            ),
          }))
          upload({ ...attachment, file: next }, apiKey)
          return
        }
      }
      upload(attachment, apiKey)
    })()
  })
  return null""",
        1,
    )
    DRAFTS.write_text(src, encoding='utf-8')
    print('compression wired into draft attachments')
print('has compressImage:', 'compressImage' in DRAFTS.read_text(encoding='utf-8'))
