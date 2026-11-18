from pathlib import Path

ANCHOR = Path('src/services/chat/context/anchor.ts')
anchor = ANCHOR.read_text(encoding='utf-8')
anchor = anchor.replace(
    "      messages.push({ role: 'user', content: user.content } as MessageParam)",
    "      messages.push({ role: 'user', content: [{ type: 'text', text: user.content }] })",
    1,
)
anchor = anchor.replace(
    "        messages.push({ role: 'assistant', content: answer } as MessageParam)",
    "        messages.push({ role: 'assistant', content: [{ type: 'text', text: answer }] })",
    1,
)
ANCHOR.write_text(anchor, encoding='utf-8')
print('anchor message params fixed')

STORE = Path('src/services/chat/store.ts')
store = STORE.read_text(encoding='utf-8')
store = store.replace(
    "              const previous = usage",
    "              const previous: ContextUsage | null = usage",
    1,
)
STORE.write_text(store, encoding='utf-8')
print('usage narrowing fixed')
