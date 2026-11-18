"""Use the app icon instead of the whale on the empty chat screen."""

import re
from pathlib import Path

WELCOME = Path('src/components/session/Welcome.tsx')
tsx = WELCOME.read_text(encoding='utf-8')
tsx = tsx.replace(
    "import whale from '../../assets/deepseek-whale.svg'",
    "import appIcon from '../../assets/deepsleep-avatar.jpg'",
    1,
)
tsx = tsx.replace(
    '          {android ? <img src={whale} alt="" /> : null}',
    '          {android ? <img className={styles.appIcon} src={appIcon} alt="" /> : null}',
    1,
)
WELCOME.write_text(tsx, encoding='utf-8')
print('welcome uses the app icon')

CSS = Path('src/components/session/Welcome.module.css')
css = CSS.read_text(encoding='utf-8')
if '.appIcon' not in css:
    css = css.replace(
        """  img {
    display: block;
    width: 42px;
    height: auto;
  }""",
        """  .appIcon {
    display: block;
    width: 56px;
    height: 56px;
    border-radius: 16px;
    object-fit: cover;
  }""",
        1,
    )
    CSS.write_text(css, encoding='utf-8')
    print('app icon sized 56px rounded')

GRADLE = Path('android/app/build.gradle')
gradle = GRADLE.read_text(encoding='utf-8')
GRADLE.write_text(re.sub(r'versionCode = \d+', 'versionCode = 36', gradle), encoding='utf-8')
print('versionCode 36')
