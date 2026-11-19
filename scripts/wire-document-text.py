"""草稿附件区加「读取文档内容」按钮：抽出 docx/xlsx/pptx/pdf 正文塞进输入框。"""

from pathlib import Path

FILE = Path('src/components/chatInput/DraftAttachments.tsx')
src = FILE.read_text(encoding='utf-8')

if 'extractDocumentText' not in src:
    src = src.replace(
        "import { useUploads, type UploadTask } from '../../services/attachments.js'",
        "import { useUploads, type UploadTask } from '../../services/attachments.js'\n"
        "import { canExtractText, extractDocumentText } from '../../services/documentText.js'\n"
        "import { getDraft, setDraftText } from '../../services/chat/drafts.js'\n"
        "import { useChatStore } from '../../services/chat/store.js'\n"
        "import { showToast } from '../base/toastState.js'",
        1,
    )

    # 在列表渲染里加按钮
    OLD = """  return (
    <div className={styles.attachments}>
      {items.map((item) => (
        <AttachmentItem
          key={item.id}
          item={item}
          exiting={exiting}
          onRetry={() => onRetry(item.id)}
          onRemove={() => onRemove(item.id)}
        />
      ))}
    </div>
  )"""
    NEW = """  const sessionId = useChatStore((state) => state.activeId)
  const document = items.find((item) => !item.isImage && canExtractText(item.file.name))
  return (
    <div className={styles.attachments}>
      {items.map((item) => (
        <AttachmentItem
          key={item.id}
          item={item}
          exiting={exiting}
          onRetry={() => onRetry(item.id)}
          onRemove={() => onRemove(item.id)}
        />
      ))}
      {document ? (
        <button
          type="button"
          className={styles.readDocument}
          onClick={async () => {
            try {
              const text = await extractDocumentText(document.file)
              if (!text) {
                showToast('没能从这份文档里读到文字')
                return
              }
              const draft = getDraft(sessionId)
              setDraftText(sessionId, `${draft.text}${draft.text ? '\\n\\n' : ''}${text}`)
              showToast(`已读取 ${document.file.name} 的正文`)
            } catch {
              showToast('读取失败，可能是不支持的文档格式')
            }
          }}
        >
          读取文档内容
        </button>
      ) : null}
    </div>
  )"""
    assert OLD in src, 'attachments render block not found'
    src = src.replace(OLD, NEW, 1)
    FILE.write_text(src, encoding='utf-8')
print('read document button:', 'readDocument' in src)

CSS = Path('src/components/chatInput/ChatInput.module.css')
css = CSS.read_text(encoding='utf-8')
if '.readDocument' not in css:
    css += """
/* 附件区里的「读取文档内容」 */
.readDocument {
  align-self: center;
  height: 30px;
  padding: 0 12px;
  border: 0;
  border-radius: 15px;
  background: color-mix(in srgb, currentColor 10%, transparent);
  color: inherit;
  font: inherit;
  font-size: 12.5px;
  white-space: nowrap;

  &:active {
    background: color-mix(in srgb, currentColor 18%, transparent);
  }
}
"""
    CSS.write_text(css, encoding='utf-8')
print('readDocument style:', '.readDocument' in css)
