"""设置页加「检查更新」入口与更新弹窗。"""

from pathlib import Path

FILE = Path('src/components/settings/AndroidSettings.tsx')
src = FILE.read_text(encoding='utf-8')

# 1) Popup 类型
src = src.replace(
    "type Popup = 'locale' | 'theme' | 'voice' | 'logout' | 'delete' | 'link' | 'avatar' | 'name'",
    "type Popup = 'locale' | 'theme' | 'voice' | 'logout' | 'delete' | 'link' | 'avatar' | 'name' | 'update'",
    1,
)

# 2) import
if 'checkAppUpdate' not in src:
    src = src.replace(
        "import { useChatStore } from '../../services/chat/store.js'",
        "import { checkAppUpdate, installAppUpdate, installedVersionCode, openInstallPermission, type UpdateInfo, type UpdateProgress } from '../../services/appUpdate.js'\n"
        "import { useChatStore } from '../../services/chat/store.js'",
        1,
    )

# 3) 状态
if 'updateInfo' not in src:
    src = src.replace(
        "  const [nameDraft, setNameDraft] = useState('')",
        "  const [nameDraft, setNameDraft] = useState('')\n"
        "  const [updateInfo, setUpdateInfo] = useState<UpdateInfo | null>(null)\n"
        "  const [updateProgress, setUpdateProgress] = useState<UpdateProgress | null>(null)\n"
        "  const [updateBusy, setUpdateBusy] = useState(false)",
        1,
    )

# 4) 设置根页加一行「检查更新」，放在服务协议那一组之前
anchor = """            <Group spaced>
              <Row label={labels.help} icon={<Info glyph="?" />} onClick={() => setPage('help')} />"""
addition = """            <Group spaced>
              <Row
                label={tr('检查更新', 'Check for updates')}
                value={`build${installedVersionCode()}`}
                icon={<IconSettingsOutline16 />}
                onClick={async () => {
                  try {
                    const info = await checkAppUpdate()
                    if (!info.available) {
                      showToast(tr('已是最新版本', 'You are up to date'))
                      return
                    }
                    setUpdateInfo(info)
                    setUpdateProgress(null)
                    setPopup('update')
                  } catch (error) {
                    showToast({
                      key: 'historyImportFailedDetail',
                      params: { message: error instanceof Error ? error.message : String(error) },
                      type: 'error',
                    })
                  }
                }}
              />
            </Group>
""" + anchor
if "tr('检查更新'" not in src:
    src = src.replace(anchor, addition, 1)

# 5) 更新弹窗（沿用账户名称那套卡面样式）
popup_anchor = "      {popup === 'name' ? ("
modal = """      {popup === 'update' && updateInfo ? (
        <div className={styles.nameOverlay} role="presentation" onClick={() => setPopup(null)}>
          <section
            className={styles.nameCard}
            role="dialog"
            aria-modal="true"
            aria-label={tr('发现新版本', 'Update available')}
            onClick={(event) => event.stopPropagation()}
          >
            <h2 className={styles.nameTitle}>
              {tr('发现新版本', 'Update available')} {updateInfo.tag}
            </h2>
            <p className={styles.nameHint}>
              {tr('当前 build', 'Current build')}
              {updateInfo.current}
              {' → build'}
              {updateInfo.latest}
              {updateInfo.size > 0 ? ` · ${(updateInfo.size / 1024 / 1024).toFixed(1)} MB` : ''}
            </p>
            {updateInfo.notes ? (
              <p className={styles.updateNotes}>{updateInfo.notes.slice(0, 400)}</p>
            ) : null}
            {updateProgress && updateProgress.state !== 'ready' ? (
              <p className={styles.updateProgress}>
                {updateProgress.state === 'error'
                  ? updateProgress.message
                  : `${tr('正在下载', 'Downloading')} ${Math.max(0, updateProgress.percent)}%`}
              </p>
            ) : null}
            <div className={styles.nameActions}>
              <button type="button" className={styles.nameCancel} onClick={() => setPopup(null)}>
                {t('cancel')}
              </button>
              <button
                type="button"
                className={styles.nameSave}
                disabled={updateBusy}
                onClick={async () => {
                  setUpdateBusy(true)
                  setUpdateProgress({ state: 'downloading', percent: 0, loaded: 0, total: updateInfo.size, message: '' })
                  try {
                    await installAppUpdate(updateInfo.url, setUpdateProgress)
                    showToast(tr('已开始安装，按提示完成即可', 'Installer opened'))
                    setPopup(null)
                  } catch (error) {
                    const message = error instanceof Error ? error.message : String(error)
                    setUpdateProgress({ state: 'error', percent: 0, loaded: 0, total: 0, message })
                    if (/install|安装|permission|Permission/.test(message)) {
                      openInstallPermission()
                    }
                  } finally {
                    setUpdateBusy(false)
                  }
                }}
              >
                {updateBusy ? tr('处理中…', 'Working…') : tr('下载并安装', 'Download and install')}
              </button>
            </div>
          </section>
        </div>
      ) : null}
"""
if "popup === 'update'" not in src:
    src = src.replace(popup_anchor, modal + popup_anchor, 1)

FILE.write_text(src, encoding='utf-8')
print('update row:', "tr('检查更新'" in src, '| update modal:', "popup === 'update'" in src)

# 6) 样式
CSS = Path('src/components/settings/AndroidSettings.module.css')
css = CSS.read_text(encoding='utf-8')
if '.updateNotes' not in css:
    css += """
.updateNotes {
  max-height: 140px;
  margin: 14px 0 0;
  overflow-y: auto;
  padding: 10px 12px;
  border-radius: 12px;
  background: var(--settings-bg);
  color: var(--settings-muted);
  font-size: 12.5px;
  line-height: 1.6;
  white-space: pre-wrap;
}

.updateProgress {
  margin: 12px 0 0;
  color: var(--settings-muted);
  font-size: 13px;
  text-align: center;
}
"""
    CSS.write_text(css, encoding='utf-8')
print('update styles added')
