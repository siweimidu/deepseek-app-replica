package com.deep.sleep;

import android.content.Context;
import android.os.Build;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;

/**
 * 应用内更新：查 GitHub Release、下载 APK。
 *
 * 只做「查」和「下」，安装由调用方用 FileProvider 起系统安装器。
 * 全部走原生 HTTP，避免 WebView 里 fetch 被 CORS 和 CSP 拦。
 */
final class AppUpdater {

    /** 仓库固定，发布流程不变的情况下不需要改这里 */
    private static final String OWNER_REPO = "siweimidu/deepseek-app-replica";
    private static final String API =
            "https://api.github.com/repos/" + OWNER_REPO + "/releases/latest";
    private static final int CONNECT_TIMEOUT = 15000;
    private static final int READ_TIMEOUT = 30000;

    interface Progress {
        /** percent < 0 表示只有进度不知总量 */
        void onProgress(int percent, long loaded, long total);
    }

    private AppUpdater() {}

    private static HttpURLConnection open(String address, String accept) throws IOException {
        HttpURLConnection connection = (HttpURLConnection) new URL(address).openConnection();
        connection.setConnectTimeout(CONNECT_TIMEOUT);
        connection.setReadTimeout(READ_TIMEOUT);
        connection.setInstanceFollowRedirects(true);
        connection.setRequestProperty("User-Agent", "DeepSleep");
        connection.setRequestProperty("Accept", accept);
        return connection;
    }

    /**
     * 查最新版本。返回 JSON 字符串，字段：
     * ok / tag / notes / url / size / error
     */
    static String check(Context context) {
        JSONObject result = new JSONObject();
        HttpURLConnection connection = null;
        try {
            connection = open(API, "application/vnd.github+json");
            int status = connection.getResponseCode();
            if (status < 200 || status >= 300) {
                result.put("ok", false);
                result.put("error", "HTTP " + status);
                return result.toString();
            }
            String body = readAll(connection.getInputStream());
            JSONObject json = new JSONObject(body);
            String tag = json.optString("tag_name", "");
            JSONArray assets = json.optJSONArray("assets");
            String url = "";
            long size = 0;
            if (assets != null) {
                for (int i = 0; i < assets.length(); i++) {
                    JSONObject asset = assets.getJSONObject(i);
                    String name = asset.optString("name", "");
                    if (name.endsWith(".apk")) {
                        url = asset.optString("browser_download_url", "");
                        size = asset.optLong("size", 0);
                        break;
                    }
                }
            }
            result.put("ok", !url.isEmpty());
            result.put("tag", tag);
            result.put("notes", json.optString("body", ""));
            result.put("url", url);
            result.put("size", size);
            result.put("current", currentVersionName(context));
            if (url.isEmpty()) {
                result.put("error", "该版本没有 APK 附件");
            }
            return result.toString();
        } catch (Exception error) {
            try {
                result.put("ok", false);
                result.put("error", String.valueOf(error.getMessage()));
            } catch (Exception ignored) {
                return "{\"ok\":false,\"error\":\"unknown\"}";
            }
            return result.toString();
        } finally {
            if (connection != null) {
                connection.disconnect();
            }
        }
    }

    static String currentVersionName(Context context) {
        try {
            return context.getPackageManager().getPackageInfo(context.getPackageName(), 0).versionName;
        } catch (Exception error) {
            return "";
        }
    }

    static long currentVersionCode(Context context) {
        try {
            android.content.pm.PackageInfo pack =
                    context.getPackageManager().getPackageInfo(context.getPackageName(), 0);
            return Build.VERSION.SDK_INT >= 28 ? pack.getLongVersionCode() : pack.versionCode;
        } catch (Exception error) {
            return 0;
        }
    }

    /** 下载 APK 到缓存目录，返回文件；失败抛异常由调用方转成事件 */
    static File download(Context context, String address, Progress progress) throws IOException {
        HttpURLConnection connection = null;
        try {
            connection = open(address, "application/octet-stream");
            int status = connection.getResponseCode();
            if (status < 200 || status >= 300) {
                throw new IOException("HTTP " + status);
            }
            long total = connection.getContentLengthLong();
            File dir = new File(context.getCacheDir(), "update");
            if (!dir.exists() && !dir.mkdirs()) {
                throw new IOException("无法创建缓存目录");
            }
            File target = new File(dir, "DeepSleep-update.apk");
            try (InputStream input = connection.getInputStream();
                 FileOutputStream output = new FileOutputStream(target)) {
                byte[] buffer = new byte[64 * 1024];
                long loaded = 0;
                int lastPercent = -1;
                int read;
                while ((read = input.read(buffer)) != -1) {
                    output.write(buffer, 0, read);
                    loaded += read;
                    int percent = total > 0 ? (int) (loaded * 100 / total) : -1;
                    if (percent != lastPercent) {
                        lastPercent = percent;
                        progress.onProgress(percent, loaded, total);
                    }
                }
                output.flush();
            }
            if (target.length() <= 0) {
                throw new IOException("下载内容为空");
            }
            return target;
        } finally {
            if (connection != null) {
                connection.disconnect();
            }
        }
    }

    private static String readAll(InputStream input) throws IOException {
        try (InputStream stream = input) {
            java.io.ByteArrayOutputStream buffer = new java.io.ByteArrayOutputStream();
            byte[] chunk = new byte[16 * 1024];
            int read;
            while ((read = stream.read(chunk)) != -1) {
                buffer.write(chunk, 0, read);
            }
            return buffer.toString("UTF-8");
        }
    }
}
