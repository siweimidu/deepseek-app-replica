"""Search page must answer the system back gesture; drop the dead gesture hook."""

import re
from pathlib import Path

PAGE = Path('src/components/search/SessionSearchPage.tsx')
page = PAGE.read_text(encoding='utf-8')

if 'usePredictiveBack' not in page:
    page = page.replace(
        "import { useTranslate } from '../../i18n/index.js'",
        "import { usePredictiveBack } from '../../app/backGesture.js'\nimport { useTranslate } from '../../i18n/index.js'",
        1,
    )
    page = page.replace(
        "  const inputRef = useRef<HTMLInputElement>(null)",
        "  const pageRef = useRef<HTMLDivElement>(null)\n  const inputRef = useRef<HTMLInputElement>(null)",
        1,
    )
    page = page.replace(
        "  const term = query.trim().toLocaleLowerCase()",
        "  usePredictiveBack(pageRef, closeSessionSearch, open)\n\n  const term = query.trim().toLocaleLowerCase()",
        1,
    )
    page = page.replace(
        """    <div className={styles.page} role="dialog" aria-modal="true">""",
        """    <div className={styles.page} role="dialog" aria-modal="true" ref={pageRef}>""",
        1,
    )
    PAGE.write_text(page, encoding='utf-8')
    print('search page handles back')

DEAD = Path('src/components/sider/useAndroidDrawerGesture.ts')
if DEAD.exists():
    referenced = any(
        'useAndroidDrawerGesture' in f.read_text(encoding='utf-8')
        for f in Path('src').rglob('*.ts*')
        if f != DEAD
    )
    if not referenced:
        DEAD.unlink()
        print('dead gesture hook removed')

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 32', gradle), encoding='utf-8')
print('versionCode 32')
