from pathlib import Path

STORE = Path('src/services/chat/store.ts')
store = STORE.read_text(encoding='utf-8')

store = store.replace(
    """          } else if (event.type === 'message_delta') {
            const reported = event.usage
            if (reported) {
              const previous: ContextUsage | null = usage
              usage = {
                inputTokens: reported.input_tokens || previous?.inputTokens || 0,
                outputTokens: reported.output_tokens,
                cacheReadTokens: reported.cache_read_input_tokens || previous?.cacheReadTokens || 0,
                cacheWriteTokens:
                  reported.cache_creation_input_tokens || previous?.cacheWriteTokens || 0,
                updatedAt: Date.now(),
              }
            }
          }""",
    """          } else if (event.type === 'message_delta') {
            const reported = event.usage
            if (reported) {
              // 输入侧用量以 message_start 为准，这里补上累计输出与缓存情况
              usage = {
                inputTokens: reported.input_tokens || 0,
                outputTokens: reported.output_tokens,
                cacheReadTokens: reported.cache_read_input_tokens || 0,
                cacheWriteTokens: reported.cache_creation_input_tokens || 0,
                updatedAt: Date.now(),
              }
            }
          }""",
    1,
)
STORE.write_text(store, encoding='utf-8')
print('delta usage simplified')
