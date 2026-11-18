"""Scroll the mobile scroller by computed offset instead of scrollIntoView."""

from pathlib import Path

LIST = Path('src/components/messages/MessageList.tsx')
tsx = LIST.read_text(encoding='utf-8')

OLD = """      if (node) {
        clearScrollTarget()
        stickyRef.current = false
        node.scrollIntoView({ block: 'center', behavior: 'smooth' })
        node.classList.add(styles.flash)
        window.setTimeout(() => node.classList.remove(styles.flash), 1400)
        return
      }"""
NEW = """      if (node) {
        clearScrollTarget()
        stickyRef.current = false
        // scrollIntoView 在嵌套滚动容器里会去滚祖先，这里自己算偏移
        const box = scroll.getBoundingClientRect()
        const rect = node.getBoundingClientRect()
        const centered = scroll.scrollTop + (rect.top - box.top) - box.height / 2 + rect.height / 2
        const top = Math.max(0, Math.min(scroll.scrollHeight - scroll.clientHeight, centered))
        scroll.scrollTo({ top, behavior: 'smooth' })
        scrollTopRef.current = top
        node.classList.add(styles.flash)
        window.setTimeout(() => node.classList.remove(styles.flash), 1400)
        return
      }"""
assert OLD in tsx, 'scroll branch not found'
LIST.write_text(tsx.replace(OLD, NEW, 1), encoding='utf-8')
print('manual offset scroll applied')
