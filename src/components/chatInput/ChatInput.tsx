import clsx from 'clsx'
import { memo, useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react'
import { create } from 'zustand'
import { android } from '../../app/android.js'
import {
  IconGlobeLanguageOutline14,
  IconPaperclipOutline16,
  IconSendOutline16,
  IconStopFill16,
  IconThinkOutline14,
} from '../base/icons.js'
import { setSearch, setThinking, useSettings } from '../../services/settings.js'
import { useIsMobile } from '../../app/viewport.js'
import { sendMessage, stopReply, useChatStore } from '../../services/chat/store.js'
import {
  addDraftFiles,
  EMPTY_DRAFT,
  getDraft,
  prepareDraftMessage,
  removeDraftAttachment,
  retryDraftAttachment,
  setDraftText,
  useDrafts,
} from '../../services/chat/drafts.js'
import { stopReadAloud } from '../../services/speech/readAloud.js'
import { IconButton } from '../base/IconButton.js'
import { AndroidCircle } from '../base/AndroidIcons.js'
import { Tooltip } from '../base/Tooltip.js'
import { ensureApiKey } from '../settings/settingsDialogState.js'
import { DragMask, useFileDrop } from './DragMask.js'
import { showToast } from '../base/toastState.js'
import { ACCEPT, useUploads } from '../../services/attachments.js'
import { DraftAttachments } from './DraftAttachments.js'
import { useVoiceInput } from './useVoiceInput.js'
import { VoiceButton } from './VoiceButton.js'
import { Spectrum } from './Spectrum.js'
import { AndroidAttachments } from './AndroidAttachments.js'
import { AndroidDraftAttachments } from './AndroidDraftAttachments.js'
import { AndroidVoiceOverlay } from './AndroidVoiceOverlay.js'
import { useHoldToTalk } from './useHoldToTalk.js'
import { useTranslate } from '../../i18n/index.js'
import styles from './ChatInput.module.css'

const useVoiceMode = create<{ enabled: boolean }>(() => ({ enabled: false }))

/** 输入框：自适应高度的文本框 + 文件 + 深度思考与智能搜索开关 + 语音输入 + 发送 / 停止 */
export const ChatInput = memo(function ChatInput({ sessionId }: { sessionId: string | null }) {
  // 切换目标时释放录音、转写和 DOM 状态；文字与附件由草稿服务保留。
  return <Input key={sessionId === null ? 'new' : `session:${sessionId}`} sessionId={sessionId} />
})

const Input = ({ sessionId }: { sessionId: string | null }) => {
  const t = useTranslate()
  const draft = useDrafts((state) => state.drafts.get(sessionId) ?? EMPTY_DRAFT)
  const { text, attachments } = draft
  const setText = (value: string) => setDraftText(sessionId, value)
  const draftReady = useUploads((state) => prepareDraftMessage(draft, state.tasks) !== null)
  const imagesUploading = useUploads((state) =>
    attachments.some(
      (item) =>
        item.isImage && (!state.tasks[item.id] || state.tasks[item.id].status === 'uploading')
    )
  )
  const streaming = useChatStore(
    (state) => sessionId !== null && Object.hasOwn(state.streaming, sessionId)
  )
  const thinking = useSettings((state) => state.thinking)
  const importingHistory = useChatStore((state) => state.importingHistory)
  const isMobile = useIsMobile()
  const search = useSettings((state) => state.search)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const togglesRef = useRef<HTMLDivElement>(null)
  const voiceMode = useVoiceMode((state) => state.enabled)
  const [showAttachments, setShowAttachments] = useState(false)
  const [typing, setTyping] = useState(false)
  const sendSpoken = useRef(false)

  useLayoutEffect(() => {
    const toggles = togglesRef.current
    if (!toggles) {
      return
    }

    const updateLabels = () => {
      toggles.classList.remove(styles.collapsedToggles)
      toggles.classList.toggle(styles.collapsedToggles, toggles.scrollWidth > toggles.clientWidth)
    }

    updateLabels()
    const observer = new ResizeObserver(updateLabels)
    observer.observe(toggles)
    return () => observer.disconnect()
  }, [t])

  const acceptFiles = (files: File[], recentPhotoId?: string) => {
    if (files.length === 0 || useChatStore.getState().importingHistory || !ensureApiKey()) {
      return
    }
    const error = addDraftFiles(
      sessionId,
      files,
      useSettings.getState().apiKey ?? '',
      recentPhotoId
    )
    if (error) {
      showToast(error)
    }
  }
  const retryFile = useCallback(
    (id: string) => {
      if (!useChatStore.getState().importingHistory && ensureApiKey()) {
        retryDraftAttachment(sessionId, id, useSettings.getState().apiKey ?? '')
      }
    },
    [sessionId]
  )
  const removeFile = useCallback(
    (id: string) => {
      if (!useChatStore.getState().importingHistory) {
        removeDraftAttachment(sessionId, id)
      }
    },
    [sessionId]
  )
  const dragging = useFileDrop(acceptFiles)

  /** 转写结果插入到光标处，并把光标移到插入内容之后 */
  const voice = useVoiceInput((transcript) => {
    const textarea = textareaRef.current
    const current = getDraft(sessionId).text
    const start = textarea?.selectionStart ?? current.length
    const end = textarea?.selectionEnd ?? current.length
    setText(current.slice(0, start) + transcript + current.slice(end))
    if (sendSpoken.current) {
      sendSpoken.current = false
      if (!useChatStore.getState().importingHistory && ensureApiKey()) {
        stopReadAloud()
        sendMessage(sessionId)
      }
      return
    }
    requestAnimationFrame(() => {
      textarea?.focus({ preventScroll: true })
      textarea?.setSelectionRange(start + transcript.length, start + transcript.length)
    })
  })
  const hold = useHoldToTalk(voice, () => {
    if (importingHistory || streaming || !ensureApiKey()) {
      return false
    }
    setShowAttachments(false)
    sendSpoken.current = true
    return true
  })

  // 欢迎页导入后会话 ID 不变，不能依赖卸载取消语音；订阅开始事件也覆盖快速完成的导入。
  const cancelVoice = voice.cancel
  useEffect(
    () =>
      useChatStore.subscribe((state, previous) => {
        if (state.importingHistory && !previous.importingHistory) {
          cancelVoice()
        }
      }),
    [cancelVoice]
  )

  // 移动端录音时用频谱替代输入框内容
  const recording = voice.status === 'recording'
  const voiceOverlayActive = recording || voice.status === 'transcribing'

  // 排队、上传中或上传失败的附件都留在输入框，全部上传成功后才能发送
  const canSend = !importingHistory && !streaming && voice.status === 'idle' && draftReady
  const showSend = !android || streaming || draftReady

  useEffect(() => {
    if (!showAttachments) {
      return
    }
    const closeOnBack = (event: Event) => {
      if (event.defaultPrevented) {
        return
      }
      event.preventDefault()
      setShowAttachments(false)
    }
    window.addEventListener('android-back', closeOnBack)
    return () => window.removeEventListener('android-back', closeOnBack)
  }, [showAttachments])

  const send = () => {
    if (
      useChatStore.getState().importingHistory ||
      voice.status !== 'idle' ||
      !prepareDraftMessage(getDraft(sessionId), useUploads.getState().tasks)
    ) {
      return
    }
    // 文本与上传完成态由提交动作读取最新快照，不使用上一次渲染的草稿。
    if (!ensureApiKey() || !sendMessage(sessionId)) {
      return
    }
    setShowAttachments(false)
    stopReadAloud()
    if (isMobile) {
      textareaRef.current?.blur()
    } else {
      textareaRef.current?.focus()
    }
  }

  return (
    <div className={styles.composer}>
      <div
        data-drawer-gesture-ignore=""
        className={clsx(
          styles.wrapper,
          sessionId === null ? styles.home : styles.session,
          android && voiceOverlayActive && styles.recordingCard
        )}
        onClick={(event) => {
          if (event.target === event.currentTarget) {
            textareaRef.current?.focus({ preventScroll: true })
          }
        }}
      >
        {android ? (
          <AndroidDraftAttachments
            items={attachments}
            suggestions={!text.trim() && attachments.some((item) => item.isImage)}
            loading={imagesUploading}
            canSend={canSend}
            onRetry={retryFile}
            onRemove={removeFile}
            onSuggestion={(message) => {
              if (!canSend || getDraft(sessionId).text.trim()) {
                return
              }
              setText(message)
              send()
            }}
          />
        ) : (
          <DraftAttachments items={attachments} onRetry={retryFile} onRemove={removeFile} />
        )}
        <div className={styles.textareaWrapper}>
          {android && voiceMode ? (
            <button
              type="button"
              className={styles.holdButton}
              disabled={importingHistory || streaming}
              {...hold.direct}
              onPointerDown={(event) => {
                if (voice.status === 'transcribing') {
                  voice.cancel()
                } else {
                  hold.direct.onPointerDown(event)
                }
              }}
            >
              {t(voice.status === 'transcribing' ? 'voiceInputCancel' : 'androidHoldToTalk')}
            </button>
          ) : (
            <textarea
              ref={textareaRef}
              className={clsx(styles.textarea, recording && isMobile && styles.textareaHidden)}
              placeholder={t(
                android
                  ? typing
                    ? 'androidMessageHint'
                    : 'androidHoldHint'
                  : 'chatInputPlaceholderChat'
              )}
              rows={2}
              // 移动端不自动聚焦，避免一打开就弹出键盘
              autoFocus={!isMobile}
              disabled={importingHistory}
              value={text}
              onChange={(event) => setText(event.target.value)}
              onFocus={() => {
                setTyping(true)
                setShowAttachments(false)
              }}
              onBlur={() => setTyping(false)}
              {...(android ? hold.delayed : {})}
              onPointerDown={(event) => {
                if (android && !text && !typing) {
                  hold.delayed.onPointerDown(event)
                }
              }}
              onContextMenu={(event) => {
                if (recording && android) {
                  event.preventDefault()
                }
              }}
              onMouseDown={(event) => {
                // 首次点击时手动聚焦，避免 Safari 把整个页面滚到输入框位置。
                if (
                  isMobile &&
                  event.button === 0 &&
                  document.activeElement !== event.currentTarget
                ) {
                  event.preventDefault()
                  event.currentTarget.focus({ preventScroll: true })
                }
              }}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
                  event.preventDefault()
                  send()
                }
              }}
              onPaste={(event) => {
                const files = Array.from(event.clipboardData.files)
                if (files.length > 0) {
                  event.preventDefault()
                  acceptFiles(files)
                }
              }}
            />
          )}
          {recording && isMobile && !android ? <Spectrum getAnalyser={voice.getAnalyser} /> : null}
          {voiceMode ? null : (
            <div className={styles.mirror} aria-hidden>
              {`${text}\n`}
            </div>
          )}
        </div>
        <div className={styles.functionRow}>
          {/* 深度思考 / 智能搜索开关，tooltip 在按钮上方 */}
          <div ref={togglesRef} className={styles.toggles}>
            <Tooltip content={t('deactivatedThinkTooltip')}>
              <button
                type="button"
                className={clsx(styles.toggle, thinking && styles.selected)}
                aria-label={t('thinkingSwitch')}
                aria-pressed={thinking}
                onClick={() => setThinking(!thinking)}
              >
                <IconThinkOutline14 />
                <span className={styles.toggleLabel}>{t('thinkingSwitch')}</span>
              </button>
            </Tooltip>
            <Tooltip content={t('deactivatedSearchTooltip')}>
              <button
                type="button"
                className={clsx(styles.toggle, search && styles.selected)}
                aria-label={t('search')}
                aria-pressed={search}
                onClick={() => setSearch(!search)}
              >
                <IconGlobeLanguageOutline14 />
                <span className={styles.toggleLabel}>{t('search')}</span>
              </button>
            </Tooltip>
          </div>
          <div className={styles.right}>
            {android ? (
              <>
                <IconButton
                  size="xl"
                  tone="primary"
                  icon={<AndroidCircle icon="add" />}
                  aria-label={t(showAttachments ? 'close' : 'uploadFile')}
                  aria-expanded={showAttachments}
                  disabled={importingHistory}
                  onClick={() => {
                    textareaRef.current?.blur()
                    setShowAttachments(!showAttachments)
                  }}
                />
                {draftReady && (attachments.length === 0 || text.trim()) ? null : (
                  <IconButton
                    size="xl"
                    tone="primary"
                    icon={<AndroidCircle icon={voiceMode ? 'keys' : 'voice'} />}
                    aria-label={t(voiceMode ? 'androidTextMode' : 'voiceInput')}
                    aria-pressed={voiceMode}
                    onClick={() => {
                      voice.cancel()
                      useVoiceMode.setState({ enabled: !voiceMode })
                    }}
                  />
                )}
              </>
            ) : (
              <>
                <VoiceButton
                  status={voice.status}
                  disabled={!voice.available}
                  seconds={voice.seconds}
                  onClick={() => {
                    if (
                      voice.status !== 'idle' ||
                      (!useChatStore.getState().importingHistory && ensureApiKey())
                    ) {
                      void voice.toggle()
                    }
                  }}
                />
                <IconButton
                  size="m"
                  tone="primary"
                  icon={<IconPaperclipOutline16 />}
                  tooltip={t('uploadFile')}
                  disabled={importingHistory}
                  onClick={() => ensureApiKey() && fileInputRef.current?.click()}
                />
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  hidden
                  accept={ACCEPT}
                  onChange={(event) => {
                    acceptFiles(Array.from(event.target.files ?? []))
                    event.target.value = ''
                  }}
                />
              </>
            )}
            {streaming && sessionId ? (
              <button
                type="button"
                className={styles.sendButton}
                aria-label={t('chatInputStopButtonTooltip')}
                onClick={() => {
                  stopReadAloud()
                  stopReply(sessionId)
                }}
              >
                <IconStopFill16 />
              </button>
            ) : showSend ? (
              <button
                type="button"
                className={clsx(styles.sendButton, !canSend && styles.disabled)}
                aria-label={t('send')}
                aria-disabled={!canSend}
                onClick={send}
              >
                <IconSendOutline16 />
              </button>
            ) : null}
          </div>
        </div>
        {dragging ? <DragMask /> : null}
      </div>
      {android ? (
        <>
          <AndroidAttachments
            open={showAttachments}
            selectedPhotos={
              new Map(
                attachments.flatMap((item) =>
                  item.recentPhotoId ? [[item.recentPhotoId, item.id] as const] : []
                )
              )
            }
            onRecentFile={(file, photoId) => acceptFiles([file], photoId)}
            onRemove={removeFile}
            onFiles={(files) => {
              setShowAttachments(false)
              acceptFiles(files)
            }}
          />
          <AndroidVoiceOverlay
            active={voiceOverlayActive}
            canceling={hold.canceling}
            level={voice.getLevel}
          />
        </>
      ) : null}
    </div>
  )
}
