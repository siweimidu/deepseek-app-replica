import clsx from 'clsx'
import { useState, type ReactNode } from 'react'
import { createPortal } from 'react-dom'
import { useAnchoredPosition, useDismiss, type Align, type Side } from './anchored.js'
import styles from './Menu.module.css'

export type MenuOption = {
  key: string
  label: string
  icon: ReactNode
  danger?: boolean
  /** 在这一项之前画一条分隔线，与官方会话菜单一致 */
  divider?: boolean
  onSelect: () => void
}

/** 点击触发，默认向下展开；点外部或 Esc 关闭 */
export const Menu = ({
  options,
  children,
  align = 'start',
  side = 'bottom',
  alignOffset = -5,
  variant,
}: {
  options: MenuOption[]
  children: (props: { open: boolean; toggle: () => void }) => ReactNode
  align?: Align
  side?: Side
  alignOffset?: number
  /** roomy：会话长按菜单，行高与字号更大并带分隔线 */
  variant?: 'roomy'
}) => {
  const [open, setOpen] = useState(false)
  const close = () => setOpen(false)
  // 默认左侧对齐并再左移 5px，让菜单文字与触发元素图标对齐
  const { anchorRef, floatingRef, position } = useAnchoredPosition<HTMLSpanElement, HTMLDivElement>(
    open,
    { align, alignOffset, offset: 4, side }
  )
  useDismiss(open, [anchorRef, floatingRef], close)
  const roomy = variant === 'roomy'

  return (
    <>
      <span ref={anchorRef} className={styles.anchor}>
        {children({ open, toggle: () => setOpen((value) => !value) })}
      </span>
      {open
        ? createPortal(
            <div
              ref={floatingRef}
              className={clsx(styles.menu, roomy && styles.roomy)}
              style={position ?? undefined}
              role="menu"
            >
              {options.map((option) => (
                <div
                  key={option.key}
                  role="menuitem"
                  className={clsx(
                    styles.option,
                    option.danger && styles.danger,
                    option.divider && styles.divided
                  )}
                  onClick={() => {
                    setOpen(false)
                    option.onSelect()
                  }}
                >
                  <span className={styles.icon}>{option.icon}</span>
                  {option.label}
                </div>
              ))}
            </div>,
            document.body
          )
        : null}
    </>
  )
}
