"""Make the whole search field row open the page on tap, not just on focus."""

from pathlib import Path

SIDER = Path('src/components/sider/Sider.tsx')
sider = SIDER.read_text(encoding='utf-8')
old = "        <label className={styles.search}>"
new = "        <label className={styles.search} onClick={() => openSessionSearch()}>"
if old in sider and 'styles.search} onClick' not in sider:
    sider = sider.replace(old, new, 1)
    SIDER.write_text(sider, encoding='utf-8')
    print('label click opens search')
else:
    print('label already patched')
