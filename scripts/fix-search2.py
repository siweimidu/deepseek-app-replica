"""Point the drawer field at the search page; add a safe text accessor for messages."""

from pathlib import Path

SIDER = Path('src/components/sider/Sider.tsx')
sider = SIDER.read_text(encoding='utf-8')
OLD_INPUT = """          <input
            type="search"
            placeholder={t('androidSearchChats')}
            aria-label={t('androidSearchChats')}
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />"""
NEW_INPUT = """          <input
            type="search"
            placeholder={t('androidSearchChats')}
            aria-label={t('androidSearchChats')}
            value=""
            readOnly
            onFocus={() => openSessionSearch()}
          />"""
if OLD_INPUT in sider:
    sider = sider.replace(OLD_INPUT, NEW_INPUT, 1)
    SIDER.write_text(sider, encoding='utf-8')
    print('drawer field opens the search page')
else:
    print('input already patched')

PAGE = Path('src/components/search/SessionSearchPage.tsx')
page = PAGE.read_text(encoding='utf-8')
if 'userText' not in page:
    page = page.replace(
        """        const messageHit = session?.messages.find(
          (message) => message.role === 'user' && message.content.toLocaleLowerCase().includes(term)
        )""",
        """        const messageHit = session?.messages.find((message) =>
          userText(message).toLocaleLowerCase().includes(term)
        )""",
        1,
    )
    page = page.replace(
        "        const text = messageHit?.content ?? ''",
        "        const text = messageHit ? userText(messageHit) : ''",
        1,
    )
    page = page.replace(
        "const clock = (value: number) => {",
        """type MessageLike = { role: string } & Record<string, unknown>

/** 只有用户消息带纯文本 content；助手消息是分段结构 */
const userText = (message: MessageLike) =>
  message.role === 'user' && typeof message.content === 'string' ? (message.content as string) : ''

const clock = (value: number) => {""",
        1,
    )
    PAGE.write_text(page, encoding='utf-8')
    print('userText helper added')
