import zipfile

z = zipfile.ZipFile(r'C:\Users\35238\AppData\Local\Temp\verify-release-45.apk')
dex = z.read('classes.dex')
print('发布的包含原生滑动代码:', b'dispatchSwipeIfHorizontal' in dex)
print('发布的包含JS桥:', b'__dshSwipe' in dex)
