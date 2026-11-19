"""账号管理页加「账户名称」行 + 改名弹窗。"""

import re
from pathlib import Path

FILE = Path('src/components/settings/AndroidSettings.tsx')
src = FILE.read_text(encoding='utf-8')

# 1) Popup 类型
src = src.replace(
    "type Popup = 'locale' | 'theme' | 'voice' | 'logout' | 'delete' | 'link' | 'avatar'",
    "type Popup = 'locale' | 'theme' | 'voice' | 'logout' | 'delete' | 'link' | 'avatar' | 'name'",
    1,
)

# 2) 导入 setAccountName
src = src.replace("  setAvatar,\n", "  setAvatar,\n  setAccountName,\n", 1)

# 3) 状态
src = src.replace(
    "  const [avatarFile, setAvatarFile] = useState<File | null>(null)",
    "  const [avatarFile, setAvatarFile] = useState<File | null>(null)\n"
    "  const [nameDraft, setNameDraft] = useState('')",
    1,
)

# 4) 账户页加一行「账户名称」，放在头像下面
anchor = """              <input
                ref={avatarInput}
                hidden
                type="file"
                accept="image/*"
                onChange={(event) => {
                  const picked = event.target.files?.[0]
                  event.target.value = ''
                  if (picked) {
                    setAvatarFile(picked)
                  }
                }}
              />"""
addition = anchor + """
              <Row
                label={tr('账户名称', 'Account name')}
                value={accountName || 'API Key'}
                onClick={() => {
                  setNameDraft(accountName ?? '')
                  setPopup('name')
                }}
              />"""
assert anchor in src, 'avatar input anchor not found'
if "tr('账户名称'" not in src:
    src = src.replace(anchor, addition, 1)

# 5) 改名弹窗（放在 link 弹窗之前）
popup_anchor = "      {popup === 'link' ? ("
modal = """      {popup === 'name' ? (
        <div className={styles.overlay}>
          <section className={styles.choice} role="dialog" aria-modal="true">
            <header>{tr('账户名称', 'Account name')}</header>
            <p className={styles.message}>
              {tr(
                '这个名字只显示在侧边栏底部，不影响你的账号。留空则显示 API Key。',
                'Shown at the bottom of the sidebar only. Leave empty to show API Key.'
              )}
            </p>
            <label className={styles.linkField}>
              <span>{tr('名称', 'Name')}</span>
              <input
                value={nameDraft}
                maxLength={20}
                spellCheck={false}
                placeholder="API Key"
                onChange={(event) => setNameDraft(event.target.value)}
              />
            </label>
            <div className={styles.confirmActions}>
              <button className={styles.confirm} onClick={back}>
                {t('cancel')}
              </button>
              <button
                className={styles.confirm}
                onClick={() => {
                  setAccountName(nameDraft)
                  setPopup(null)
                }}
              >
                {tr('保存', 'Save')}
              </button>
            </div>
          </section>
        </div>
      ) : null}
"""
if "popup === 'name'" not in src:
    src = src.replace(popup_anchor, modal + popup_anchor, 1)

FILE.write_text(src, encoding='utf-8')
print('account name row + modal added')
