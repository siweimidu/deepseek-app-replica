"""重写账户名称编辑弹窗：DeepSeek 官方卡面语言（圆角卡片、填充式输入、主次按钮）。"""

from pathlib import Path

# ---------- CSS ----------
CSS = Path('src/components/settings/AndroidSettings.module.css')
css = CSS.read_text(encoding='utf-8')

if '.nameCard' not in css:
    css += """
/* 账户名称编辑：居中卡片，填充式输入，无边框无分隔线 */
.nameOverlay {
  position: fixed;
  inset: 0;
  z-index: 40;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgb(0 0 0 / 45%);
  backdrop-filter: blur(10px);
  animation: name-fade 160ms ease-out;
}

.nameCard {
  width: min(330px, 100%);
  padding: 24px 20px 18px;
  border-radius: 24px;
  background: var(--settings-card);
  box-shadow: 0 20px 50px rgb(0 0 0 / 40%);
  animation: name-pop 260ms cubic-bezier(0.22, 1, 0.36, 1);
}

.nameTitle {
  margin: 0;
  font-size: 17px;
  font-weight: 600;
  text-align: center;
}

.nameHint {
  margin: 8px 0 0;
  color: var(--settings-muted);
  font-size: 13px;
  line-height: 1.5;
  text-align: center;
}

.nameField {
  display: flex;
  align-items: center;
  height: 50px;
  margin-top: 20px;
  padding: 0 16px;
  border-radius: 16px;
  background: var(--settings-bg);
  transition: box-shadow 160ms ease;

  &:focus-within {
    box-shadow: 0 0 0 2px var(--dsw-alias-brand-text, #4d6bfe);
  }

  input {
    flex: 1;
    min-width: 0;
    padding: 0;
    border: 0;
    outline: 0;
    appearance: none;
    background: transparent;
    color: inherit;
    caret-color: var(--dsw-alias-brand-text, #4d6bfe);
    font: inherit;
    font-size: 16px;

    &::placeholder {
      color: var(--settings-muted);
    }
  }
}

.nameReset {
  display: block;
  width: 100%;
  margin-top: 8px;
  padding: 8px;
  border: 0;
  border-radius: 12px;
  background: transparent;
  color: var(--settings-muted);
  font: inherit;
  font-size: 13px;

  &:active {
    background: var(--settings-bg);
  }
}

.nameActions {
  display: flex;
  gap: 10px;
  margin-top: 18px;

  button {
    height: 46px;
    border: 0;
    border-radius: 14px;
    font: inherit;
    font-size: 15px;
    transition:
      transform 120ms ease,
      opacity 160ms ease;

    &:active {
      transform: scale(0.97);
    }
  }
}

.nameCancel {
  flex: 1;
  background: var(--settings-button);
  color: inherit;
}

.nameSave {
  flex: 1.35;
  background: var(--dsw-alias-brand-text, #4d6bfe);
  color: #fff;
  font-weight: 600;
}

@keyframes name-fade {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes name-pop {
  from {
    opacity: 0;
    transform: scale(0.94) translateY(8px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}
"""
    CSS.write_text(css, encoding='utf-8')
print('name dialog css written')

# ---------- JSX ----------
FILE = Path('src/components/settings/AndroidSettings.tsx')
src = FILE.read_text(encoding='utf-8')

start = src.index("      {popup === 'name' ? (")
end = src.index("      {popup === 'link' ? (", start)
NEW = """      {popup === 'name' ? (
        <div
          className={styles.nameOverlay}
          role="presentation"
          onClick={() => setPopup(null)}
        >
          <section
            className={styles.nameCard}
            role="dialog"
            aria-modal="true"
            aria-label={tr('账户名称', 'Account name')}
            onClick={(event) => event.stopPropagation()}
          >
            <h2 className={styles.nameTitle}>{tr('账户名称', 'Account name')}</h2>
            <p className={styles.nameHint}>
              {tr(
                '只显示在侧边栏底部，不影响账号本身',
                'Shown at the bottom of the sidebar only'
              )}
            </p>
            <label className={styles.nameField}>
              <input
                autoFocus
                value={nameDraft}
                maxLength={20}
                spellCheck={false}
                autoCapitalize="off"
                autoComplete="off"
                enterKeyHint="done"
                placeholder="API Key"
                onChange={(event) => setNameDraft(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter') {
                    setAccountName(nameDraft)
                    setPopup(null)
                  }
                }}
              />
            </label>
            {accountName ? (
              <button
                type="button"
                className={styles.nameReset}
                onClick={() => {
                  setAccountName(null)
                  setPopup(null)
                }}
              >
                {tr('恢复默认（API Key）', 'Reset to API Key')}
              </button>
            ) : null}
            <div className={styles.nameActions}>
              <button type="button" className={styles.nameCancel} onClick={() => setPopup(null)}>
                {t('cancel')}
              </button>
              <button
                type="button"
                className={styles.nameSave}
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
src = src[:start] + NEW + src[end:]
FILE.write_text(src, encoding='utf-8')
print('name dialog markup replaced')
