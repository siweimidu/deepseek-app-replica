from pathlib import Path

ZH_ADD = """  callInProgress: '通话中 {time}',
  callListening: '正在聆听',
  callThinking: '正在思考',
  callSpeaking: '正在回答',
  callMuted: '你已静音',
  callMute: '静音',
  callUnmute: '取消静音',
  callEnd: '挂断',
  callTextMode: '切换到文字',
  callVoiceTitle: '朗读音色',
  callVoiceClear: '清晰明亮',
  callVoiceDeep: '低沉浑厚',
  callAnswerSettings: '回答设置',
  searchModeLabel: '智能搜索',
"""

EN_ADD = """  callInProgress: 'In call {time}',
  callListening: 'Listening',
  callThinking: 'Thinking',
  callSpeaking: 'Answering',
  callMuted: 'You are muted',
  callMute: 'Mute',
  callUnmute: 'Unmute',
  callEnd: 'Hang up',
  callTextMode: 'Switch to text',
  callVoiceTitle: 'Voice',
  callVoiceClear: 'Clear and bright',
  callVoiceDeep: 'Low and warm',
  callAnswerSettings: 'Answer settings',
  searchModeLabel: 'Smart search',
"""

for path, add in ((Path('src/i18n/zh.ts'), ZH_ADD), (Path('src/i18n/en.ts'), EN_ADD)):
    text = path.read_text(encoding='utf-8')
    anchor = '  contentCaveat:'
    assert anchor in text, path
    if 'callInProgress' in text:
        print('skip', path)
        continue
    path.write_text(text.replace(anchor, add + anchor, 1), encoding='utf-8')
    print('patched', path)
