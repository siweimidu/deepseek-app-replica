/**
 * 会话菜单、详情弹层与多选页用的图标。
 * 统一采用官方那套线性几何（24 网格、1.7 描边、圆角端点），尺寸按 20/24 输出。
 */

const line = {
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.7,
  strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const,
}

/** 图钉：官方菜单里的「置顶」 */
export const IconPinOutline20 = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
    <path
      {...line}
      d="M12 17v5M9 10.76a2 2 0 0 1-1.11 1.79l-1.78.9A2 2 0 0 0 5 15.24V16a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-.76a2 2 0 0 0-1.11-1.79l-1.78-.9A2 2 0 0 1 15 10.76V7a1 1 0 0 1 1-1 2 2 0 0 0 0-4H8a2 2 0 0 0 0 4 1 1 0 0 1 1 1z"
    />
  </svg>
)

/** 取消置顶：同一图钉加一道斜杠 */
export const IconPinSlashOutline20 = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
    <path
      {...line}
      d="M12 17v5M15 9.34V7a1 1 0 0 1 1-1 2 2 0 0 0 0-4H8a2 2 0 0 0-2 2M9 10.76a2 2 0 0 1-1.11 1.79l-1.78.9A2 2 0 0 0 5 15.24V16a1 1 0 0 0 1 1h12"
    />
    <path {...line} d="m2 2 20 20" />
  </svg>
)

export const IconInfoOutline20 = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
    <circle {...line} cx="12" cy="12" r="9" />
    <path {...line} d="M12 11v5" />
    <circle cx="12" cy="7.8" r="1.05" fill="currentColor" />
  </svg>
)

/** 多选：官方是「点 + 横线」两行 */
export const IconListOutline20 = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
    <circle {...line} cx="4.6" cy="6.6" r="1.6" />
    <circle {...line} cx="4.6" cy="17.4" r="1.6" />
    <path {...line} d="M9.4 6.6h10M9.4 17.4h10" />
  </svg>
)

/** 重命名：官方是一支斜铅笔 */
export const IconPencilOutline20 = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
    <path
      {...line}
      d="M21.2 6.8a1 1 0 0 0-4-4L3.8 16.2a2 2 0 0 0-.5.8l-1.3 4.4a.5.5 0 0 0 .6.6l4.4-1.3a2 2 0 0 0 .8-.5z"
    />
    <path {...line} d="m15 5 4 4" />
  </svg>
)

export const IconTrashOutline20 = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
    <path {...line} d="M3 6h18" />
    <path {...line} d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6" />
    <path {...line} d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
    <path {...line} d="M10 11v6M14 11v6" />
  </svg>
)

export const IconChatOutline20 = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
    <path
      {...line}
      d="M12 3.6c4.8 0 8.4 3.1 8.4 7.1 0 4-3.6 7.1-8.4 7.1-.9 0-1.8-.1-2.6-.3l-4.1 1.4 1.1-3.2C4.9 14.5 3.6 12.9 3.6 10.7c0-4 3.6-7.1 8.4-7.1Z"
    />
  </svg>
)

export const IconClockOutline20 = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
    <circle {...line} cx="12" cy="12" r="9" />
    <path {...line} d="M12 7v5.2l3.4 2.4" />
  </svg>
)

export const IconCopyOutline20 = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
    <rect {...line} x="8.6" y="3.6" width="11.8" height="11.8" rx="2.6" />
    <path {...line} d="M15.4 20.4H6.6A3 3 0 0 1 3.6 17.4V8.6" />
  </svg>
)

export const IconIdOutline20 = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
    <rect {...line} x="3.4" y="5.4" width="17.2" height="13.2" rx="2.8" />
    <circle {...line} cx="9" cy="10.6" r="1.8" />
    <path {...line} d="M6.4 15.2c.4-1.1 1.4-1.7 2.6-1.7s2.2.6 2.6 1.7M14.6 10.2h3.4M14.6 13.6h3.4" />
  </svg>
)

/** 通话入口：听筒。尺寸/描边与顶部其它图标保持一致（22 / 1.9 / 圆角端点） */
export const IconPhoneOutline20 = () => (
  <svg
    width="22"
    height="22"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.9"
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden="true"
  >
    <g transform="translate(12 12) scale(1.16) translate(-12 -12)">
      <path d="M6.4 3.2h2.5l1.6 3.9-2 1.3a11.8 11.8 0 0 0 5.1 5.1l1.3-2 3.9 1.6v2.5a2.3 2.3 0 0 1-2.5 2.3A17.2 17.2 0 0 1 4.1 5.7 2.3 2.3 0 0 1 6.4 3.2Z" />
    </g>
  </svg>
)

/** 挂断：听筒朝下 */
export const IconPhoneOffOutline = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true">
    <path
      {...line}
      d="M3.2 10.4c4.9-3.5 12.7-3.5 17.6 0 .7.5.9 1.5.4 2.2l-1.4 1.9a1.6 1.6 0 0 1-2 .4l-2-1.1a1.6 1.6 0 0 1-.8-1.5l.1-1.1a12 12 0 0 0-4.2 0l.1 1.1a1.6 1.6 0 0 1-.8 1.5l-2 1.1a1.6 1.6 0 0 1-2-.4l-1.4-1.9a1.6 1.6 0 0 1 .4-2.2Z"
    />
  </svg>
)

/** 通话页右上角：切换/设置 */
export const IconSwitchOutline20 = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
    <path {...line} d="M4 8.6h15.2M20 8.6l-3.4-3.2M20 15.4H4.8M4.8 15.4l3.4 3.2" />
  </svg>
)

