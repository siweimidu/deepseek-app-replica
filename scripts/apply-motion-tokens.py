"""One-off: point every hand-written easing at the generated spring tokens."""

import re
from pathlib import Path

EDITS: list[tuple[str, str, str]] = [
    (
        'src/app/App.module.css',
        """  --drawer-transition: 430ms linear(
    0,
    0.12 6%,
    0.36 14%,
    0.64 24%,
    0.86 34%,
    0.98 45%,
    1.018 56%,
    1.012 68%,
    0.998 82%,
    1
  );""",
        """  --drawer-transition: var(--motion-reveal);""",
    ),
    (
        'src/components/base/Menu.module.css',
        """  transition:
    background-color 120ms ease-out,
    transform 220ms linear(0, 0.4 12%, 1.04 38%, 1);""",
        """  transition:
    background-color 120ms ease-out,
    transform var(--motion-press);""",
    ),
    (
        'src/components/base/Menu.module.css',
        """  animation: menu-pop 260ms linear(0, 0.32 10%, 0.86 32%, 1.06 52%, 0.99 74%, 1);""",
        """  animation: menu-pop var(--motion-reveal);""",
    ),
    (
        'src/components/sider/SessionDetailSheet.module.css',
        """  transform: translateY(calc(var(--sheet-in) + var(--back-progress, 0) * 55%));
  transition: transform 420ms linear(0, 0.18 10%, 0.52 24%, 0.82 38%, 1.02 56%, 1.01 70%, 1);""",
        """  transform: translateY(calc(var(--sheet-in) + var(--back-progress, 0) * 100%));
  transition: transform var(--motion-sheet);""",
    ),
    (
        'src/components/sider/SessionDetailSheet.module.css',
        """  transition: transform 260ms linear(0, 0.45 14%, 1.05 42%, 1);""",
        """  transition: transform var(--motion-press);""",
    ),
    (
        'src/components/settings/AvatarEditor.module.css',
        """  transform: translateX(calc(var(--back-progress, 0) * 100%));
  transition: transform 240ms cubic-bezier(0.2, 0.72, 0.25, 1);""",
        """  transform: translateX(calc(var(--back-progress, 0) * 100%));
  transition: transform var(--motion-gesture);""",
    ),
    (
        'src/components/settings/AvatarEditor.module.css',
        """  transition: transform 240ms linear(0, 0.42 14%, 1.06 42%, 1);""",
        """  transition: transform var(--motion-press);""",
    ),
    (
        'src/components/settings/AndroidSettings.module.css',
        """  transform: translateX(calc(var(--back-progress, 0) * 26%))
    scale(calc(1 - var(--back-progress, 0) * 0.06));
  transition: transform 260ms cubic-bezier(0.2, 0.72, 0.25, 1);""",
        """  transform: translateX(calc(var(--back-progress, 0) * 34%))
    scale(calc(1 - var(--back-progress, 0) * 0.1));
  transition: transform var(--motion-gesture);""",
    ),
    (
        'src/components/settings/AndroidSettings.module.css',
        """    transform-origin: left center;
    transition: transform 320ms linear(0, 0.32 8%, 0.79 20%, 1.03 30%, 1.01 46%, 1);""",
        """    transform-origin: left center;
    transition: transform var(--motion-metric);""",
    ),
    (
        'src/components/base/ImportStatusBar.module.css',
        """  transform: translateY(-100%);
  transition: transform 340ms linear(0, 0.28 6%, 0.72 16%, 1.06 26%, 1.02 40%, 0.99 58%, 1);""",
        """  transform: translateY(-100%);
  transition: transform var(--motion-reveal);""",
    ),
    (
        'src/components/base/ImportStatusBar.module.css',
        """    transition: transform 320ms linear(0, 0.32 8%, 0.79 20%, 1.03 30%, 1.01 46%, 1);""",
        """    transition: transform var(--motion-metric);""",
    ),
    (
        'src/components/chatInput/AndroidAttachments.module.css',
        """  transition:
    grid-template-rows 260ms cubic-bezier(0.2, 0.8, 0.2, 1),
    opacity 160ms ease-out;""",
        """  transition:
    grid-template-rows var(--motion-sheet),
    opacity 200ms ease-out;""",
    ),
    (
        'src/components/sider/Sider.module.css',
        """  transition: transform 260ms linear(0, 0.42 14%, 1.06 42%, 1);""",
        """  transition: transform var(--motion-press);""",
    ),
    (
        'src/components/sider/Sider.module.css',
        """  transition: transform 280ms linear(0, 0.46 14%, 1.07 44%, 1);""",
        """  transition: transform var(--motion-press);""",
    ),
    (
        'src/components/sider/Sider.module.css',
        """  transition: transform 300ms linear(0, 0.44 12%, 1.05 42%, 1);""",
        """  transition: transform var(--motion-press);""",
    ),
    (
        'src/components/sider/Sider.module.css',
        """    transition:
      background-color 150ms ease-out,
      transform 300ms linear(0, 0.44 12%, 1.05 42%, 1);""",
        """    transition:
      background-color 150ms ease-out,
      transform var(--motion-press);""",
    ),
    (
        'src/components/sider/SessionItem.module.css',
        """    transform 320ms linear(0, 0.5 12%, 1.12 42%, 0.98 64%, 1);""",
        """    transform var(--motion-press);""",
    ),
]

changed = 0
for path, old, new in EDITS:
    file = Path(path)
    text = file.read_text(encoding='utf-8')
    if old in text:
        file.write_text(text.replace(old, new, 1), encoding='utf-8')
        changed += 1
        print(f'ok   {path}')
    else:
        print(f'MISS {path} :: {old.splitlines()[0][:60]}')

# 兜底：把残留的手写 linear(...) 曲线统计出来，便于人工确认
for path in [
    'src/app/App.module.css',
    'src/components/sider/Sider.module.css',
    'src/components/base/Menu.module.css',
    'src/components/settings/AndroidSettings.module.css',
]:
    leftovers = re.findall(r'linear\([^)]{20,}\)', Path(path).read_text(encoding='utf-8'))
    if leftovers:
        print(f'leftover in {path}: {len(leftovers)}')

print(f'changed {changed}/{len(EDITS)}')
