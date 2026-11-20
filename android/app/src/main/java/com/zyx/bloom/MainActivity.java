package com.zyx.bloom;

import android.content.Intent;
import android.net.Uri;
import android.app.Activity;
import android.os.Bundle;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import androidx.webkit.WebViewAssetLoader;

public class MainActivity extends Activity {
    private static final String ASSET_HOST = "appassets.androidplatform.net";
    private static final String API_URL = "https://bloom-world.onrender.com";
    private WebView webView;
    private WebViewAssetLoader assetLoader;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        assetLoader = new WebViewAssetLoader.Builder()
                .addPathHandler("/", new WebViewAssetLoader.AssetsPathHandler(this))
                .build();
        webView = new WebView(this);
        webView.getSettings().setJavaScriptEnabled(true);
        webView.getSettings().setMediaPlaybackRequiresUserGesture(false);
        webView.getSettings().setDomStorageEnabled(true);
        webView.getSettings().setLoadWithOverviewMode(true);
        webView.getSettings().setUseWideViewPort(true);
        webView.getSettings().setSupportMultipleWindows(true);
        webView.getSettings().setJavaScriptCanOpenWindowsAutomatically(true);
        webView.setWebViewClient(new WebViewClient() {
            @Override
            public android.webkit.WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
                if (ASSET_HOST.equals(request.getUrl().getHost())) {
                    return assetLoader.shouldInterceptRequest(request.getUrl());
                }
                return super.shouldInterceptRequest(view, request);
            }

            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                Uri uri = request.getUrl();
                if (ASSET_HOST.equals(uri.getHost())) return false;
                openExternal(uri);
                return true;
            }
        });
        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onCreateWindow(WebView view, boolean isDialog, boolean isUserGesture, android.os.Message resultMsg) {
                WebView popup = new WebView(MainActivity.this);
                popup.setWebViewClient(new WebViewClient() {
                    @Override
                    public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                        openExternal(request.getUrl());
                        return true;
                    }
                });
                WebView.WebViewTransport transport = (WebView.WebViewTransport) resultMsg.obj;
                transport.setWebView(popup);
                resultMsg.sendToTarget();
                return true;
            }
        });
        setContentView(webView);
        String url = "https://" + ASSET_HOST + "/index.html?api=" + Uri.encode(API_URL);
        webView.loadUrl(url);
    }

    private void openExternal(Uri uri) {
        String scheme = uri.getScheme();
        if ("https".equalsIgnoreCase(scheme) || "http".equalsIgnoreCase(scheme)) {
            try { startActivity(new Intent(Intent.ACTION_VIEW, uri)); } catch (Exception ignored) { }
        }
    }

    @Override
    public void onBackPressed() {
        if (webView != null && webView.canGoBack()) webView.goBack();
        else super.onBackPressed();
    }
}
