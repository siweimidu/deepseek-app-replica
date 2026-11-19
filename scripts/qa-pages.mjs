import { readFileSync, writeFileSync } from 'node:fs'

/**
 * 从当前 dist/index.html 生成各个 QA 变体页面。
 * 每次 pnpm build 之后跑一次即可（bundle 名字带 hash）。
 */

const html = readFileSync('dist/index.html', 'utf8')

const base = (extra = '', key = 'sk-qa-placeholder') => `<script>
try{localStorage.setItem('chat-demo:theme-preference','dark')}catch{}
window.__downloadCalls=[]
window.__installCalls=[]
const noop=()=>undefined
window.DeepSeekAndroid={
  statusInset:()=>24, systemFontScale:()=>1, openAppPermissions:noop, openSourcePage:noop,
  readApiKey:()=>${JSON.stringify(key)}, writeApiKey:()=>true, setDarkBars:noop,
  requestRecentPhotos:noop, prefetchRecentPhotos:noop, requestHistoryExport:noop,
  writeHistoryExport:()=>true, finishHistoryExport:()=>true,
  beginImageSave:()=>true, writeImageSave:()=>true, finishImageSave:()=>true,
  requestCamera:noop, requestGallery:noop, requestFiles:noop,
  requestRecording:noop, finishRecording:()=>true, recordingLevel:()=>0,
  versionLabel:()=>'com.deep.sleep - QA',
  startHistoryDownload:(url)=>{ window.__downloadCalls.push(url); var t='tok1';
    setTimeout(function(){ window.dispatchEvent(new CustomEvent('android-download',{detail:{token:t,state:'ready',loaded:14669,total:14669,url:'/sample-export.zip',message:''}})) },200);
    return t },
  historyDownloadSize:()=>14669, readHistoryDownload:()=>'', releaseHistoryDownload:noop,
  appVersionInfo:()=>'79|0.1.0',
  checkAppUpdate:()=>JSON.stringify({ok:true,tag:'v0.1.0',notes:'feat: 应用内更新\\nfeat: 图片裁剪',url:'https://github.com/siweimidu/deepseek-app-replica/releases/download/v0.1.0/DeepSleep-0.1.0-build80.apk',size:4440000,current:'0.1.0'}),
  installAppUpdate:(url)=>{ window.__installCalls.push(url);
    setTimeout(function(){ window.dispatchEvent(new CustomEvent('android-update',{detail:{state:'progress',percent:42,loaded:1800000,total:4440000,message:''}})) },150);
    setTimeout(function(){ window.dispatchEvent(new CustomEvent('android-update',{detail:{state:'ready',percent:100,loaded:4440000,total:4440000,message:''}})) },600) },
  openInstallPermission:()=>{ window.__installCalls.push('open-permission') }
  ${extra}
}
</script>`

const bigDownload = `,
  startHistoryDownload:(url)=>{ window.__downloadCalls.push(url); var t='tokbig';
    setTimeout(function(){ window.dispatchEvent(new CustomEvent('android-download',{detail:{token:t,state:'ready',loaded:46328333,total:46328333,url:'/big-export.zip',message:''}})) },250);
    return t },
  historyDownloadSize:()=>46328333`

const write = (name, stub) => {
  const page = html
    .replace('<html lang="zh-CN">', '<html lang="zh-CN" data-android data-ds-dark-theme>')
    .replace('</head>', stub + '</head>')
  writeFileSync(`dist/${name}`, page, 'utf8')
  console.log('written', name)
}

write('qa-dark.html', base())
write('qa-link.html', base())
write('qa-update.html', base())
write('qa-worker.html', base(bigDownload))
write('qa-nokey.html', base('', ''))
