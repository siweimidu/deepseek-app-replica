package com.deep.sleep;

import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Context;
import android.content.Intent;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Insets;
import android.graphics.Paint;
import android.graphics.Path;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.WindowInsets;
import android.view.WindowInsetsController;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.window.OnBackInvokedDispatcher;

/** A separate WebView keeps external pages away from the application's JavaScript bridge. */
public final class SourceBrowserActivity extends Activity {
    private WebView page;
    private LinearLayout root;

    static Uri webUri(String value) {
        if (value == null) return null;
        Uri uri = Uri.parse(value);
        String scheme = uri.getScheme();
        String host = uri.getHost();
        if (host == null || host.isEmpty() || scheme == null
                || !("https".equalsIgnoreCase(scheme) || "http".equalsIgnoreCase(scheme))) {
            return null;
        }
        return uri;
    }

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        Uri initial = webUri(getIntent().getDataString());
        if (initial == null) {
            finish();
            return;
        }
        boolean dark = getIntent().getBooleanExtra("dark", false);
        int background = Color.parseColor(dark ? "#0F0F0F" : "#FFFFFF");
        int foreground = Color.parseColor(dark ? "#F8F8F8" : "#111111");

        root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(background);
        root.setOnApplyWindowInsetsListener((view, insets) -> {
            Insets safe = insets.getInsets(WindowInsets.Type.systemBars()
                | WindowInsets.Type.displayCutout() | WindowInsets.Type.ime());
            view.setPadding(safe.left, safe.top, safe.right, safe.bottom);
            return WindowInsets.CONSUMED;
        });
        FrameLayout toolbar = new FrameLayout(this);
        toolbar.setBackgroundColor(background);
        root.addView(toolbar, new LinearLayout.LayoutParams(-1, dp(52)));

        ToolbarIcon close = new ToolbarIcon(this, false, foreground);
        close.setContentDescription(getIntent().getStringExtra("closeLabel"));
        close.setOnClickListener(view -> finish());
        toolbar.addView(close, new FrameLayout.LayoutParams(dp(48), -1, Gravity.START));

        ToolbarIcon external = new ToolbarIcon(this, true, foreground);
        external.setContentDescription(getIntent().getStringExtra("browserLabel"));
        external.setOnClickListener(view -> {
            Uri current = webUri(page.getUrl());
            if (current == null) return;
            try {
                startActivity(new Intent(Intent.ACTION_VIEW, current));
            } catch (ActivityNotFoundException ignored) {
                // No browser is available on this device.
            }
        });
        toolbar.addView(external, new FrameLayout.LayoutParams(dp(48), -1, Gravity.END));
        View divider = new View(this);
        divider.setBackgroundColor(Color.parseColor(dark ? "#373737" : "#E5E5E5"));
        root.addView(divider, new LinearLayout.LayoutParams(-1, dp(1)));

        page = new WebView(this);
        page.setBackgroundColor(Color.WHITE);
        WebSettings settings = page.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(false);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        settings.setTextZoom(100);
        page.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                return webUri(request.getUrl().toString()) == null;
            }
        });
        root.addView(page, new LinearLayout.LayoutParams(-1, 0, 1));
        setContentView(root);
        int flags = WindowInsetsController.APPEARANCE_LIGHT_STATUS_BARS
            | WindowInsetsController.APPEARANCE_LIGHT_NAVIGATION_BARS;
        getWindow().getInsetsController().setSystemBarsAppearance(dark ? 0 : flags, flags);
        getWindow().setNavigationBarContrastEnforced(false);
        // 状态栏跟随内置浏览器的工具栏底色，避免出现一条灰带
        getWindow().setStatusBarColor(background);
        getWindow().setNavigationBarColor(background);
        if (Build.VERSION.SDK_INT >= 33) {
            getOnBackInvokedDispatcher().registerOnBackInvokedCallback(
                OnBackInvokedDispatcher.PRIORITY_DEFAULT, this::goBack);
        }
        if (state == null || page.restoreState(state) == null) {
            page.loadUrl(initial.toString());
        }
    }

    @Override
    protected void onSaveInstanceState(Bundle state) {
        if (page != null) page.saveState(state);
        super.onSaveInstanceState(state);
    }

    private void goBack() {
        if (page != null && page.canGoBack()) page.goBack();
        else finish();
    }

    @Override
    @SuppressWarnings("deprecation")
    public void onBackPressed() {
        goBack();
    }

    @Override
    protected void onDestroy() {
        if (page != null) {
            root.removeView(page);
            page.destroy();
            page = null;
        }
        super.onDestroy();
    }

    private int dp(float value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }

    private static final class ToolbarIcon extends View {
        private final boolean external;
        private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);

        ToolbarIcon(Context context, boolean external, int color) {
            super(context);
            this.external = external;
            paint.setColor(color);
            paint.setStyle(Paint.Style.STROKE);
            paint.setStrokeWidth(1.8f);
            paint.setStrokeCap(Paint.Cap.ROUND);
            paint.setStrokeJoin(Paint.Join.ROUND);
        }

        @Override
        protected void onDraw(Canvas canvas) {
            super.onDraw(canvas);
            float density = getResources().getDisplayMetrics().density;
            canvas.save();
            canvas.translate(getWidth() / 2f + (external ? 2 : -2) * density, getHeight() / 2f);
            canvas.scale(density, density);
            if (external) {
                Path outline = new Path();
                outline.moveTo(-2, -7);
                outline.lineTo(-5, -7);
                outline.quadTo(-7, -7, -7, -5);
                outline.lineTo(-7, 5);
                outline.quadTo(-7, 7, -5, 7);
                outline.lineTo(5, 7);
                outline.quadTo(7, 7, 7, 5);
                outline.lineTo(7, 2);
                canvas.drawPath(outline, paint);
                canvas.drawLine(0, 0, 8, -8, paint);
                canvas.drawLine(2, -8, 8, -8, paint);
                canvas.drawLine(8, -8, 8, -2, paint);
            } else {
                canvas.drawLine(-6, -6, 6, 6, paint);
                canvas.drawLine(6, -6, -6, 6, paint);
            }
            canvas.restore();
        }
    }
}
