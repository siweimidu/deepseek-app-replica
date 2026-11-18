/** 会话菜单与详情弹窗用到的图标，风格与官方客户端一致（1.6 描边、圆角端点）。 */

const stroke = {
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.6,
  strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const,
}

export const IconPinOutline20 = () => (
  <svg width="20" height="20" viewBox="0 0 20 20" aria-hidden="true">
    <path
      {...stroke}
      d="M12.6 2.9 17 7.3l-1.9.6a2 2 0 0 0-1 3.2l1.4 1.7-4.7 4.7-1.8-1.6a2 2 0 0 0-3.1 1l-.6 1.9-4.4-4.4 2-.6a2 2 0 0 0 1-3.1L2.5 9l4.7-4.7 1.7 1.4a2 2 0 0 0 3.1-1z"
    />
  </svg>
)

export const IconPinSlashOutline20 = () => (
  <svg width="20" height="20" viewBox="0 0 20 20" aria-hidden="true">
    <path {...stroke} d="M3 3l14 14" />
    <path
      {...stroke}
      d="M12.6 2.9 17 7.3l-1.9.6a2 2 0 0 0-1 3.2l1.4 1.7-4.7 4.7-1.8-1.6a2 2 0 0 0-3.1 1l-.6 1.9"
    />
  </svg>
)

export const IconInfoOutline20 = () => (
  <svg width="20" height="20" viewBox="0 0 20 20" aria-hidden="true">
    <circle {...stroke} cx="10" cy="10" r="7.2" />
    <path {...stroke} d="M10 9.2v4.1" />
    <circle cx="10" cy="6.6" r="0.95" fill="currentColor" />
  </svg>
)

export const IconListOutline20 = () => (
  <svg width="20" height="20" viewBox="0 0 20 20" aria-hidden="true">
    <circle {...stroke} cx="4.6" cy="5.7" r="1.5" />
    <circle {...stroke} cx="4.6" cy="14.3" r="1.5" />
    <path {...stroke} d="M8.6 5.7h8M8.6 14.3h8" />
  </svg>
)

export const IconPencilOutline20 = () => (
  <svg width="20" height="20" viewBox="0 0 20 20" aria-hidden="true">
    <path {...stroke} d="M13.4 3.5 16.5 6.6 7.4 15.7l-4 1 1-4z" />
    <path {...stroke} d="m12 4.9 3.1 3.1" />
  </svg>
)

export const IconTrashOutline20 = () => (
  <svg width="20" height="20" viewBox="0 0 20 20" aria-hidden="true">
    <path {...stroke} d="M3.6 5.4h12.8" />
    <path {...stroke} d="M7.6 5.4V3.9c0-.5.4-.9.9-.9h3c.5 0 .9.4.9.9v1.5" />
    <path {...stroke} d="M5.4 5.4l.8 10c0 .6.5 1 1.1 1h5.4c.6 0 1.1-.4 1.1-1l.8-10" />
  </svg>
)

/** 顶部「图层」按钮：官方是三层堆叠的圆角矩形。 */
export const IconChatOutline20 = () => (
  <svg width="20" height="20" viewBox="0 0 20 20" aria-hidden="true">
    <path {...stroke} d="M10 3.2c4 0 7 2.6 7 5.9 0 3.3-3 5.9-7 5.9-.8 0-1.6-.1-2.3-.3l-3.4 1.2.9-2.7C4.1 12.2 3 10.7 3 9.1c0-3.3 3-5.9 7-5.9Z" />
  </svg>
)

export const IconClockOutline20 = () => (
  <svg width="20" height="20" viewBox="0 0 20 20" aria-hidden="true">
    <circle {...stroke} cx="10" cy="10" r="7.2" />
    <path {...stroke} d="M10 5.9V10l2.9 2" />
  </svg>
)

export const IconCopyOutline20 = () => (
  <svg width="20" height="20" viewBox="0 0 20 20" aria-hidden="true">
    <rect {...stroke} x="7.1" y="3.2" width="9.7" height="9.7" rx="2.2" />
    <path {...stroke} d="M12.9 16.8H5.4c-1.2 0-2.2-1-2.2-2.2V7.1" />
  </svg>
)

export const IconIdOutline20 = () => (
  <svg width="20" height="20" viewBox="0 0 20 20" aria-hidden="true">
    <rect {...stroke} x="3.1" y="4.6" width="13.8" height="10.8" rx="2.4" />
    <circle {...stroke} cx="7.7" cy="8.9" r="1.5" />
    <path {...stroke} d="M5.6 12.6c.3-.9 1.1-1.4 2.1-1.4s1.8.5 2.1 1.4M12.2 8.6h2.7M12.2 11.4h2.7" />
  </svg>
)
