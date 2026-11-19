import appIcon from '../../assets/deepsleep-avatar.jpg'
import { useTranslate } from '../../i18n/index.js'
import { useApiKeyForm } from './useApiKeyForm.js'
import styles from './ApiKeyScreen.module.css'

export const ApiKeyScreen = () => {
  const t = useTranslate()
  const form = useApiKeyForm()

  return (
    <main className={styles.page}>
      <form
        className={styles.form}
        onSubmit={(event) => {
          event.preventDefault()
          void form.submit()
        }}
      >
        <img className={styles.appIcon} src={appIcon} alt="" />
        <h1>{t('apiKeyStart')}</h1>
        <input
          aria-label="DeepSeek API Key"
          aria-invalid={Boolean(form.error)}
          type="password"
          autoComplete="off"
          autoCapitalize="off"
          spellCheck={false}
          enterKeyHint="go"
          placeholder={t('apiKeyPlaceholder')}
          value={form.value}
          onChange={(event) => form.setValue(event.target.value)}
        />
        {form.error ? <div role="alert" className={styles.error}>{form.error}</div> : null}
        <button type="submit" disabled={form.verifying || !form.value.trim()}>
          {t(form.verifying ? 'apiKeyVerifying' : 'confirm')}
        </button>
        <a href="https://platform.deepseek.com/api_keys">{t('apiKeyGet')}</a>
      </form>
    </main>
  )
}
