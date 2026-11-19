package com.deep.sleep;

import android.Manifest;
import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.ClipData;
import android.content.Intent;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageManager;
import android.content.res.Configuration;
import android.graphics.Color;
import android.graphics.Insets;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.MediaStore;
import android.provider.Settings;
import android.view.MotionEvent;
import android.view.WindowInsets;
import android.view.WindowInsetsController;
import android.webkit.JavascriptInterface;
import android.webkit.MimeTypeMap;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.FrameLayout;
import android.window.BackEvent;
import android.window.OnBackAnimationCallback;
import android.window.OnBackInvokedDispatcher;
import java.io.ByteArrayInputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.RandomAccessFile;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public final class MainActivity extends Activity {
    private static final String ASSET_HOST = "appassets.androidplatform.net";
    private static final String HOME = "https://" + ASSET_HOST + "/index.html";
    // 横滑判定（原生层，绕开 WebView 的事件仲裁）
    private float swipeDownX;
    private float swipeDownY;
    private boolean swipeTracking;
    private static final float SWIPE_DP = 24f;
    private static final float SWIPE_RATIO = 1.2f;

    private static final int MICROPHONE = 1;
    private static final int FILE_CHOOSER = 2;
    private static final int PHOTOS = 3;
    private static final int CAMERA = 4;
    private static final int EXPORT_HISTORY = 5;
    private WebView webView;
    private FrameLayout frame;
    private ApiKeyStore keys;
    private ValueCallback<Uri[]> fileCallback;
    private boolean keyboardVisible;
    private volatile float statusInset;
    private boolean askedForPhotos;
    private Uri capture;
    private RecentPhotos recentPhotos;
    private FileExport historyExport;
    private ImageSave imageSave;
    private NativeRecorder recorder;
    private final ExecutorService photoExecutor = Executors.newSingleThreadExecutor();
    /** 导出包下载缓存：令牌 -> 文件，导入结束后由前端调用释放。 */
    private final Map<String, File> downloads = new ConcurrentHashMap<>();
    private final ExecutorService downloadExecutor = Executors.newSingleThreadExecutor();

    @Override
    public boolean dispatchTouchEvent(MotionEvent event) {
        switch (event.getActionMasked()) {
            case MotionEvent.ACTION_DOWN:
                swipeDownX = event.getX();
                swipeDownY = event.getY();
                swipeTracking = true;
                break;
            case MotionEvent.ACTION_UP:
                if (swipeTracking) {
                    swipeTracking = false;
                    dispatchSwipeIfHorizontal(event.getX(), event.getY());
                }
                break;
            case MotionEvent.ACTION_CANCEL:
                swipeTracking = false;
                break;
            default:
                break;
        }
        return super.dispatchTouchEvent(event);
    }

    /** 横滑超过 24dp 且明显偏横向时通知网页：left = 打开侧边栏，right = 回到对话 */
    private void dispatchSwipeIfHorizontal(float upX, float upY) {
        final float dx = upX - swipeDownX;
        final float dy = upY - swipeDownY;
        final float minPx = SWIPE_DP * getResources().getDisplayMetrics().density;
        if (Math.abs(dx) < minPx || Math.abs(dx) <= Math.abs(dy) * SWIPE_RATIO) {
            return;
        }
        final String direction = dx < 0 ? "left" : "right";
        runOnUiThread(() -> {
            if (webView != null) {
                webView.evaluateJavascript(
                    "window.__dshSwipe&&window.__dshSwipe('" + direction + "')", null);
            }
        });
    }

    @Override
    public void onCreate(Bundle state) {
        super.onCreate(state);
        keys = new ApiKeyStore(this);
        recentPhotos = new RecentPhotos(getContentResolver());
        historyExport = new FileExport(getContentResolver());
        imageSave = new ImageSave(getContentResolver());
        recorder = new NativeRecorder();
        frame = new FrameLayout(this);
        webView = new WebView(this);
        frame.addView(webView, new FrameLayout.LayoutParams(-1, -1));
        frame.setOnApplyWindowInsetsListener((view, insets) -> {
            Insets safe = insets.getInsets(WindowInsets.Type.systemBars()
                | WindowInsets.Type.displayCutout() | WindowInsets.Type.ime());
            view.setPadding(safe.left, 0, safe.right, safe.bottom);
            float top = safe.top / getResources().getDisplayMetrics().density;
            if (top != statusInset) {
                statusInset = top;
                webView.evaluateJavascript("document.documentElement?.style.setProperty("
                    + "'--android-status-inset', '" + top + "px')", null);
            }
            boolean ime = insets.isVisible(WindowInsets.Type.ime());
            if (ime != keyboardVisible) {
                keyboardVisible = ime;
                webView.evaluateJavascript("document.documentElement?.toggleAttribute("
                    + "'data-keyboard', " + ime + ")", null);
            }
            return WindowInsets.CONSUMED;
        });
        setContentView(frame);
        // 真正铺满屏幕：内容画到系统状态栏/导航栏下面，留白由页面按 --android-status-inset 处理
        getWindow().setDecorFitsSystemWindows(false);
        getWindow().setStatusBarColor(Color.TRANSPARENT);
        getWindow().setNavigationBarColor(Color.TRANSPARENT);
        setBars((getResources().getConfiguration().uiMode & Configuration.UI_MODE_NIGHT_MASK)
            == Configuration.UI_MODE_NIGHT_YES);
        WebView.setWebContentsDebuggingEnabled(
            (getApplicationInfo().flags & ApplicationInfo.FLAG_DEBUGGABLE) != 0);
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(true);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        settings.setTextZoom(100);
        settings.setMediaPlaybackRequiresUserGesture(false);
        webView.setWebViewClient(new AppPage());
        webView.setWebChromeClient(new DeviceFeatures());
        webView.addJavascriptInterface(new DeviceBridge(), "DeepSeekAndroid");
        registerBackCallback();
        webView.loadUrl(HOME);
    }

    @Override
    @SuppressWarnings("deprecation")
    @SuppressLint("GestureBackNavigation") // API 33+ back gestures use the registered callback.
    public void onBackPressed() {
        handleBack();
    }

    private void handleBack() {
        webView.evaluateJavascript("window.dispatchEvent(new Event('android-back', {cancelable: true}))",
            result -> { if ("true".equals(result)) finish(); });
    }

    /** 把预测性返回手势的进度实时交给页面，让当前界面跟着手指位移。 */
    private void emitBackGesture(String state, float progress) {
        webView.evaluateJavascript(
            "window.dispatchEvent(new CustomEvent('android-back-gesture',{detail:{state:'" + state
                + "',progress:" + progress + "}}))", null);
    }

    /**
     * Android 14 起用 OnBackAnimationCallback 接收手势进度（started / progressed /
     * cancelled / invoked），13 及以下退回普通回调，回到同一套 JS 处理。
     */
    private void registerBackCallback() {
        if (Build.VERSION.SDK_INT >= 34) {
            getOnBackInvokedDispatcher().registerOnBackInvokedCallback(
                OnBackInvokedDispatcher.PRIORITY_DEFAULT, new OnBackAnimationCallback() {
                    @Override
                    public void onBackStarted(BackEvent event) {
                        emitBackGesture("start", 0f);
                    }

                    @Override
                    public void onBackProgressed(BackEvent event) {
                        emitBackGesture("progress", event.getProgress());
                    }

                    @Override
                    public void onBackCancelled() {
                        emitBackGesture("cancel", 0f);
                    }

                    @Override
                    public void onBackInvoked() {
                        // 页面里的预测性返回层若已接管，就不再重复派发返回事件
                        emitBackGesture("invoked", 1f);
                        webView.evaluateJavascript("window.__dshConsumedBack === true",
                            consumed -> {
                                if ("true".equals(consumed)) {
                                    return;
                                }
                                handleBack();
                            });
                    }
                });
            return;
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            getOnBackInvokedDispatcher().registerOnBackInvokedCallback(
                OnBackInvokedDispatcher.PRIORITY_DEFAULT, this::handleBack);
        }
    }

    private void setBars(boolean dark) {
        int flags = WindowInsetsController.APPEARANCE_LIGHT_STATUS_BARS
            | WindowInsetsController.APPEARANCE_LIGHT_NAVIGATION_BARS;
        getWindow().getInsetsController().setSystemBarsAppearance(dark ? 0 : flags, flags);
        getWindow().setNavigationBarContrastEnforced(false);
        // 状态栏/导航栏保持透明，颜色始终由页面本身决定，深浅色切换时不会留下灰边
        getWindow().setStatusBarColor(Color.TRANSPARENT);
        getWindow().setNavigationBarColor(Color.TRANSPARENT);
        int color = Color.parseColor(dark ? "#151517" : "#FFFFFF");
        frame.setBackgroundColor(color);
        webView.setBackgroundColor(color);
    }

    private static boolean isBundled(Uri url) {
        return "https".equals(url.getScheme()) && ASSET_HOST.equals(url.getHost())
            && url.getPort() == -1;
    }

    private File downloadFile(String token) {
        return new File(getCacheDir(), "history-" + token + ".zip");
    }

    private static String escapeJs(String value) {
        return value == null ? "" : value.replace("\\", "\\\\").replace("'", "\\'")
            .replace("\n", " ").replace("\r", " ");
    }

    /** 下载进度与结果都以自定义事件回传，前端据此显示进度条。 */
    private void emitDownload(String token, String state, long loaded, long total,
                              String url, String message) {
        String script = "window.dispatchEvent(new CustomEvent('android-download',{detail:{"
            + "token:'" + escapeJs(token) + "',state:'" + state + "',loaded:" + loaded
            + ",total:" + total + ",url:'" + escapeJs(url) + "',message:'" + escapeJs(message)
            + "'}}))";
        android.util.Log.d("DeepSleep", "download " + token + " " + state + " " + message);
        runOnUiThread(() -> webView.evaluateJavascript(script, null));
    }

    /** 只把缓存里的导出包暴露给页面；支持 Range，前端因此可以按需流式读取。 */
    private WebResourceResponse serveDownload(Uri url, String range) {
        File file = downloads.get(url.getLastPathSegment());
        if (file == null || !file.isFile()) {
            return new WebResourceResponse("text/plain", "UTF-8", 404, "Not Found",
                Map.of(), new ByteArrayInputStream(new byte[0]));
        }
        long size = file.length();
        long start = 0;
        long end = size - 1;
        boolean partial = false;
        if (range != null && range.startsWith("bytes=")) {
            String[] bounds = range.substring(6).split("-", -1);
            try {
                if (!bounds[0].isEmpty()) start = Long.parseLong(bounds[0]);
                if (bounds.length > 1 && !bounds[1].isEmpty()) end = Long.parseLong(bounds[1]);
            } catch (NumberFormatException ignored) {
                return new WebResourceResponse("text/plain", "UTF-8", 416,
                    "Range Not Satisfiable", Map.of(), new ByteArrayInputStream(new byte[0]));
            }
            end = Math.min(end, size - 1);
            partial = true;
        }
        if (start < 0 || end < start || start >= size) {
            return new WebResourceResponse("text/plain", "UTF-8", 416, "Range Not Satisfiable",
                Map.of(), new ByteArrayInputStream(new byte[0]));
        }
        int length = (int) (end - start + 1);
        byte[] body = new byte[length];
        try (RandomAccessFile raf = new RandomAccessFile(file, "r")) {
            raf.seek(start);
            raf.readFully(body);
        } catch (IOException error) {
            return new WebResourceResponse("text/plain", "UTF-8", 500, "Internal Error",
                Map.of(), new ByteArrayInputStream(new byte[0]));
        }
        Map<String, String> headers = new HashMap<>();
        headers.put("Accept-Ranges", "bytes");
        headers.put("Cache-Control", "no-store");
        // 不手写 Content-Length：由 WebView 按流长度计算，手写容易让读流提前结束
        if (partial) {
            headers.put("Content-Range", "bytes " + start + "-" + end + "/" + size);
            return new WebResourceResponse("application/zip", null, 206, "Partial Content",
                headers, new ByteArrayInputStream(body));
        }
        return new WebResourceResponse("application/zip", null, 200, "OK", headers,
            new ByteArrayInputStream(body));
    }

    /** 后台线程下载：绕开 WebView 的跨域限制，并把已下载字节数实时回报页面。 */
    private void startDownload(String token, String address) {
        File target = downloadFile(token);
        downloadExecutor.execute(() -> {
            HttpURLConnection connection = null;
            try {
                connection = (HttpURLConnection) new URL(address).openConnection();
                connection.setConnectTimeout(20000);
                connection.setReadTimeout(30000);
                connection.setInstanceFollowRedirects(true);
                connection.setRequestProperty("User-Agent", "DeepSleep");
                int status = connection.getResponseCode();
                if (status < 200 || status >= 300) {
                    emitDownload(token, "error", 0, 0, "", "HTTP " + status);
                    return;
                }
                long total = connection.getContentLengthLong();
                long loaded = 0;
                long reported = 0;
                try (InputStream input = connection.getInputStream();
                     FileOutputStream output = new FileOutputStream(target)) {
                    byte[] buffer = new byte[64 * 1024];
                    for (int read; (read = input.read(buffer)) > 0; ) {
                        output.write(buffer, 0, read);
                        loaded += read;
                        if (loaded - reported >= 128 * 1024) {
                            reported = loaded;
                            emitDownload(token, "progress", loaded, total, "", "");
                        }
                    }
                }
                emitDownload(token, "progress", loaded, total, "", "");
                emitDownload(token, "ready", loaded, loaded,
                    "https://" + ASSET_HOST + "/__download/" + token, "");
            } catch (IOException error) {
                //noinspection ResultOfMethodCallIgnored
                target.delete();
                downloads.remove(token);
                emitDownload(token, "error", 0, 0, "", String.valueOf(error.getMessage()));
            } finally {
                if (connection != null) connection.disconnect();
            }
        });
    }

    private final class AppPage extends WebViewClient {
        @Override
        public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
            if (isBundled(request.getUrl())) {
                return !request.isForMainFrame() || !"/index.html".equals(request.getUrl().getPath());
            }
            String scheme = request.getUrl().getScheme();
            if (request.isForMainFrame() && ("https".equals(scheme) || "http".equals(scheme))) {
                try {
                    startActivity(new Intent(Intent.ACTION_VIEW, request.getUrl()));
                } catch (ActivityNotFoundException ignored) {
                    // The device has no browser for external links.
                }
            }
            return true;
        }

        @Override
        public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
            Uri url = request.getUrl();
            if (!isBundled(url)) return null;
            String path = url.getPath();
            if (path != null && path.startsWith("/__download/")) {
                return serveDownload(url, request.getRequestHeaders().get("Range"));
            }
            if ("/recording.wav".equals(path)) {
                WebResourceResponse audio = recorder.takeWav();
                if (audio != null) return audio;
            }
            if (path != null && path.matches("/(recent|thumbnail)/[0-9]+")) {
                WebResourceResponse photo = recentPhotos.open(url.getLastPathSegment(),
                    path.startsWith("/thumbnail/"));
                if (photo != null) return photo;
            }
            if ("/index.html".equals(path) || (path != null && path.startsWith("/static/")
                    && !path.contains("/../"))) {
                String name = path.substring(1);
                String extension = name.substring(name.lastIndexOf('.') + 1);
                String type = "js".equals(extension) ? "text/javascript"
                    : MimeTypeMap.getSingleton().getMimeTypeFromExtension(extension);
                Map<String, String> headers = Map.of("Content-Security-Policy",
                    "default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
                    + "img-src 'self' https: data: blob:; font-src 'self' data:; "
                    + "media-src 'self' blob:; connect-src 'self' https://api.deepseek.com "
                    + "https://*.myhuaweicloud.com; worker-src 'self' blob:; "
                    + "frame-src 'none'; base-uri 'none'; form-action 'none';");
                try {
                    return new WebResourceResponse(type == null ? "application/octet-stream" : type,
                        "UTF-8", 200, "OK", headers, getAssets().open(name));
                } catch (IOException ignored) {
                    // Unknown paths must stay inside the bundled origin.
                }
            }
            return new WebResourceResponse("text/plain", "UTF-8", 404, "Not Found",
                Map.of(), new ByteArrayInputStream(new byte[0]));
        }
    }

    private final class DeviceFeatures extends WebChromeClient {
        @Override
        public boolean onShowFileChooser(WebView view, ValueCallback<Uri[]> callback,
                                         FileChooserParams params) {
            if (fileCallback != null) fileCallback.onReceiveValue(null);
            fileCallback = callback;
            if (params.isCaptureEnabled()) {
                if (granted(Manifest.permission.CAMERA)) {
                    launchCamera();
                } else {
                    requestPermissions(new String[]{Manifest.permission.CAMERA}, CAMERA);
                }
                return true;
            }
            boolean multiple = params.getMode() == FileChooserParams.MODE_OPEN_MULTIPLE;
            Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT).addCategory(Intent.CATEGORY_OPENABLE);
            if (multiple) intent.putExtra(Intent.EXTRA_ALLOW_MULTIPLE, true);
            String[] mimeTypes = Arrays.stream(params.getAcceptTypes())
                .map(type -> type.startsWith(".")
                    ? MimeTypeMap.getSingleton().getMimeTypeFromExtension(type.substring(1)) : type)
                .filter(type -> type != null && type.contains("/"))
                .distinct().toArray(String[]::new);
            intent.setType(mimeTypes.length == 1 ? mimeTypes[0] : "*/*");
            if (mimeTypes.length > 1) intent.putExtra(Intent.EXTRA_MIME_TYPES, mimeTypes);
            if (Build.VERSION.SDK_INT >= 33 && Arrays.equals(mimeTypes, new String[]{"image/*"})) {
                Intent picker = new Intent(MediaStore.ACTION_PICK_IMAGES).setType("image/*");
                if (multiple) {
                    picker.putExtra(MediaStore.EXTRA_PICK_IMAGES_MAX, 10);
                }
                try {
                    startActivityForResult(picker, FILE_CHOOSER);
                    return true;
                } catch (ActivityNotFoundException ignored) {
                    // Use the document picker on devices without the system photo picker.
                }
            }
            try {
                startActivityForResult(intent, FILE_CHOOSER);
            } catch (ActivityNotFoundException ignored) {
                fileCallback = null;
                callback.onReceiveValue(null);
            }
            return true;
        }
    }

    private boolean granted(String permission) {
        return checkSelfPermission(permission) == PackageManager.PERMISSION_GRANTED;
    }

    private boolean hasRecentPhotosPermission() {
        String imagesPermission = Build.VERSION.SDK_INT >= 33 ? Manifest.permission.READ_MEDIA_IMAGES
            : Manifest.permission.READ_EXTERNAL_STORAGE;
        return granted(imagesPermission) || (Build.VERSION.SDK_INT >= 34
            && granted(Manifest.permission.READ_MEDIA_VISUAL_USER_SELECTED));
    }

    private void showRecentPhotos() {
        String imagesPermission = Build.VERSION.SDK_INT >= 33 ? Manifest.permission.READ_MEDIA_IMAGES
            : Manifest.permission.READ_EXTERNAL_STORAGE;
        if (!hasRecentPhotosPermission() && !askedForPhotos) {
            askedForPhotos = true;
            String[] permissions = Build.VERSION.SDK_INT >= 34
                ? new String[]{imagesPermission, Manifest.permission.READ_MEDIA_VISUAL_USER_SELECTED}
                : new String[]{imagesPermission};
            requestPermissions(permissions, PHOTOS);
        } else {
            notifyRecentPhotos();
        }
    }

    private void notifyRecentPhotos() {
        photoExecutor.execute(() -> {
            String photos = recentPhotos.list();
            runOnUiThread(() -> {
                if (!isFinishing() && !isDestroyed()) {
                    webView.evaluateJavascript("window.dispatchEvent(new CustomEvent('android-photos', "
                        + "{detail: " + photos + "}))", null);
                }
            });
        });
    }

    private void launchCamera() {
        try {
            capture = CaptureProvider.create(this);
            Intent camera = new Intent(MediaStore.ACTION_IMAGE_CAPTURE)
                .putExtra(MediaStore.EXTRA_OUTPUT, capture)
                .addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
            camera.setClipData(ClipData.newRawUri("photo", capture));
            startActivityForResult(camera, FILE_CHOOSER);
        } catch (IOException | ActivityNotFoundException ignored) {
            capture = null;
            completeFileChooser(null);
        }
    }

    private void completeFileChooser(Uri[] files) {
        if (fileCallback == null) return;
        ValueCallback<Uri[]> callback = fileCallback;
        fileCallback = null;
        callback.onReceiveValue(files);
    }

    @Override
    public void onRequestPermissionsResult(int code, String[] permissions, int[] results) {
        super.onRequestPermissionsResult(code, permissions, results);
        if (code == MICROPHONE) {
            startRecording();
        } else if (code == PHOTOS) {
            notifyRecentPhotos();
        } else if (code == CAMERA && fileCallback != null) {
            if (granted(Manifest.permission.CAMERA)) {
                launchCamera();
            } else {
                completeFileChooser(null);
            }
        }
    }

    @Override
    protected void onActivityResult(int code, int result, Intent data) {
        super.onActivityResult(code, result, data);
        if (code == EXPORT_HISTORY) {
            Uri uri = result == RESULT_OK && data != null ? data.getData() : null;
            reportExport(uri == null ? "cancelled" : historyExport.open(uri) ? "ready" : "error");
        } else if (code == FILE_CHOOSER && fileCallback != null) {
            Uri[] files = null;
            if (result == RESULT_OK) {
                if (capture != null) {
                    files = new Uri[]{capture};
                } else if (data != null && data.getClipData() != null) {
                    ClipData clip = data.getClipData();
                    files = new Uri[clip.getItemCount()];
                    for (int index = 0; index < files.length; index++) {
                        files[index] = clip.getItemAt(index).getUri();
                    }
                } else if (data != null && data.getData() != null) {
                    files = new Uri[]{data.getData()};
                }
            }
            capture = null;
            completeFileChooser(files);
        }
    }

    @Override
    protected void onStop() {
        recorder.finish(false);
        webView.evaluateJavascript("window.dispatchEvent(new Event('android-recording-interrupted'))", null);
        super.onStop();
    }

    @Override
    protected void onDestroy() {
        photoExecutor.shutdownNow();
        if (fileCallback != null) fileCallback.onReceiveValue(null);
        recorder.finish(false);
        historyExport.close();
        imageSave.finish(false);
        frame.removeView(webView);
        webView.destroy();
        super.onDestroy();
    }

    private void reportExport(String state) {
        webView.evaluateJavascript("window.dispatchEvent(new CustomEvent('android-export', "
            + "{detail: '" + state + "'}))", null);
    }

    private void startRecording() {
        String state = !granted(Manifest.permission.RECORD_AUDIO) ? "denied"
            : recorder.start() ? "ready" : "error";
        webView.evaluateJavascript("window.dispatchEvent(new CustomEvent('android-recording', "
            + "{detail: '" + state + "'}))", null);
    }

    private final class DeviceBridge {
        @JavascriptInterface
        public float statusInset() { return statusInset; }

        @JavascriptInterface
        public float systemFontScale() { return getResources().getConfiguration().fontScale; }

        @JavascriptInterface
        public void openAppPermissions() {
            runOnUiThread(() -> startActivity(new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS,
                Uri.fromParts("package", getPackageName(), null))));
        }

        @JavascriptInterface
        public void openSourcePage(String url, boolean dark, String closeLabel, String browserLabel) {
            Uri uri = SourceBrowserActivity.webUri(url);
            if (uri == null) return;
            runOnUiThread(() -> startActivity(new Intent(MainActivity.this, SourceBrowserActivity.class)
                .setData(uri).putExtra("dark", dark)
                .putExtra("closeLabel", closeLabel).putExtra("browserLabel", browserLabel)));
        }

        @JavascriptInterface
        public String readApiKey() { return keys.read(); }

        @JavascriptInterface
        public boolean writeApiKey(String value) { return keys.write(value); }

        @JavascriptInterface
        public void setDarkBars(boolean dark) { runOnUiThread(() -> setBars(dark)); }

        @JavascriptInterface
        public void requestRecentPhotos() { runOnUiThread(() -> showRecentPhotos()); }

        @JavascriptInterface
        public void prefetchRecentPhotos() {
            runOnUiThread(() -> { if (hasRecentPhotosPermission()) notifyRecentPhotos(); });
        }

        @JavascriptInterface
        public void requestHistoryExport(String fileName) {
            runOnUiThread(() -> {
                Intent intent = new Intent(Intent.ACTION_CREATE_DOCUMENT)
                    .addCategory(Intent.CATEGORY_OPENABLE)
                    .setType("application/zip")
                    .putExtra(Intent.EXTRA_TITLE, fileName);
                try {
                    startActivityForResult(intent, EXPORT_HISTORY);
                } catch (ActivityNotFoundException ignored) {
                    reportExport("error");
                }
            });
        }

        @JavascriptInterface
        public boolean writeHistoryExport(String bytes) { return historyExport.append(bytes); }

        @JavascriptInterface
        public boolean finishHistoryExport() { return historyExport.close(); }

        @JavascriptInterface
        public boolean beginImageSave(String name, String mime) { return imageSave.begin(name, mime); }

        @JavascriptInterface
        public boolean writeImageSave(String bytes) { return imageSave.append(bytes); }

        @JavascriptInterface
        public boolean finishImageSave(boolean keep) { return imageSave.finish(keep); }

        @JavascriptInterface
        public void requestRecording() {
            runOnUiThread(() -> {
                if (granted(Manifest.permission.RECORD_AUDIO)) {
                    startRecording();
                } else {
                    requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO}, MICROPHONE);
                }
            });
        }

        @JavascriptInterface
        public boolean finishRecording(boolean keep) { return recorder.finish(keep); }

        @JavascriptInterface
        public double recordingLevel() { return recorder.level(); }

        @JavascriptInterface
        public String startHistoryDownload(String address) {
            Uri uri = Uri.parse(address == null ? "" : address.trim());
            String scheme = uri.getScheme();
            if (uri.getHost() == null || (!"https".equals(scheme) && !"http".equals(scheme))) {
                return "";
            }
            String token = Long.toHexString(System.nanoTime());
            File target = downloadFile(token);
            downloads.put(token, target);
            // 用原始字符串下载：签名链接的 query 一旦被重新编码就会 403
            startDownload(token, address == null ? "" : address.trim());
            return token;
        }

        /** 兜底通道：直接把缓存里的包分块吐给页面，不经过 HTTP 拦截。 */
        @JavascriptInterface
        public long historyDownloadSize(String token) {
            File file = downloads.get(token);
            return file != null && file.isFile() ? file.length() : -1L;
        }

        @JavascriptInterface
        public String readHistoryDownload(String token, long offset, int length) {
            File file = downloads.get(token);
            if (file == null || !file.isFile()) {
                return "";
            }
            long remaining = file.length() - offset;
            if (remaining <= 0) {
                return "";
            }
            int size = (int) Math.min(length, remaining);
            byte[] data = new byte[size];
            try (RandomAccessFile raf = new RandomAccessFile(file, "r")) {
                raf.seek(offset);
                raf.readFully(data);
            } catch (IOException error) {
                return "";
            }
            return android.util.Base64.encodeToString(data, android.util.Base64.NO_WRAP);
        }

        /** 给「版本信息」用：一眼能看出装的是哪个包、哪个构建。 */
        @JavascriptInterface
        public String versionLabel() {
            try {
                android.content.pm.PackageInfo pack =
                    getPackageManager().getPackageInfo(getPackageName(), 0);
                long code = android.os.Build.VERSION.SDK_INT >= 28
                    ? pack.getLongVersionCode() : pack.versionCode;
                return getPackageName() + " · " + pack.versionName + " · " + code;
            } catch (Exception error) {
                return getPackageName();
            }
        }

        /** 查询 GitHub 最新版本，返回 JSON（ok/tag/notes/url/size/current/error） */
        @JavascriptInterface
        public String checkAppUpdate() {
            return AppUpdater.check(MainActivity.this);
        }

        /** 下载并调用系统安装器；进度通过 android-update 事件回传 */
        @JavascriptInterface
        public void installAppUpdate(String address) {
            if (address == null || address.trim().isEmpty()) {
                emitUpdate("error", 0, 0, 0, "下载地址为空");
                return;
            }
            emitUpdate("downloading", 0, 0, 0, "");
            downloadExecutor.execute(() -> {
                try {
                    File apk = AppUpdater.download(MainActivity.this, address.trim(),
                        (percent, loaded, total) -> emitUpdate("progress", percent, loaded, total, ""));
                    emitUpdate("ready", 100, apk.length(), apk.length(), "");
                    runOnUiThread(() -> launchInstaller(apk));
                } catch (Exception error) {
                    emitUpdate("error", 0, 0, 0, String.valueOf(error.getMessage()));
                }
            });
        }

        /** 当前安装包的 versionCode / versionName，设置页展示用 */
        @JavascriptInterface
        public String appVersionInfo() {
            return AppUpdater.currentVersionCode(MainActivity.this) + "|"
                + AppUpdater.currentVersionName(MainActivity.this);
        }

        /** 系统「安装未知应用」开关页；部分机型直接落到应用详情 */
        @JavascriptInterface
        public void openInstallPermission() {
            runOnUiThread(() -> {
                try {
                    Intent intent = new Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES,
                        Uri.parse("package:" + getPackageName()));
                    intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                    startActivity(intent);
                } catch (Exception error) {
                    try {
                        Intent fallback = new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS,
                            Uri.parse("package:" + getPackageName()));
                        fallback.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                        startActivity(fallback);
                    } catch (Exception ignored) {
                        // 无能为力时保持静默，前端会提示手动安装
                    }
                }
            });
        }

        /** 用系统安装器安装已下载的 APK */
        private void launchInstaller(File apk) {
            try {
                Uri uri = new Uri.Builder()
                    .scheme("content")
                    .authority(getPackageName() + ".update")
                    .appendPath(apk.getName())
                    .build();
                grantUriPermission("com.android.packageinstaller", uri,
                    Intent.FLAG_GRANT_READ_URI_PERMISSION);
                grantUriPermission("com.google.android.packageinstaller", uri,
                    Intent.FLAG_GRANT_READ_URI_PERMISSION);
                Intent intent = new Intent(Intent.ACTION_VIEW);
                intent.setDataAndType(uri, "application/vnd.android.package-archive");
                intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
                startActivity(intent);
            } catch (Exception error) {
                emitUpdate("error", 0, 0, 0, "无法启动安装器：" + error.getMessage());
            }
        }

        private void emitUpdate(String state, int percent, long loaded, long total, String message) {
            String script = "window.dispatchEvent(new CustomEvent('android-update',{detail:{"
                + "state:'" + escapeJs(state) + "',percent:" + percent
                + ",loaded:" + loaded + ",total:" + total
                + ",message:'" + escapeJs(message) + "'}}))";
            runOnUiThread(() -> webView.evaluateJavascript(script, null));
        }

        @JavascriptInterface
        public void releaseHistoryDownload(String token) {
            File file = downloads.remove(token);
            if (file != null) {
                //noinspection ResultOfMethodCallIgnored
                file.delete();
            }
        }
    }
}
