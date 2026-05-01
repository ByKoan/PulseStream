package com.example.webviewer

import android.app.AlertDialog
import android.content.SharedPreferences
import android.os.Bundle
import android.view.Menu
import android.view.MenuItem
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView
    private lateinit var prefs: SharedPreferences

    companion object {
        private const val PREF_HOST = "host"
        private const val PREF_PORT = "port"
        private const val PREF_PROTO = "proto"
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        prefs = getSharedPreferences("WebViewerPrefs", MODE_PRIVATE)
        webView = findViewById(R.id.webview)

        val settings = webView.settings
        settings.javaScriptEnabled = true
        settings.domStorageEnabled = true
        settings.loadWithOverviewMode = true
        settings.useWideViewPort = true
        settings.mixedContentMode = WebSettings.MIXED_CONTENT_ALWAYS_ALLOW

        webView.webViewClient = WebViewClient()

        val host = prefs.getString(PREF_HOST, null)

        if (host.isNullOrEmpty()) {
            showConfigDialog(true)
        } else {
            loadUrl()
        }
    }

    private fun loadUrl() {
        val proto = prefs.getString(PREF_PROTO, "http") ?: "http"
        val host = prefs.getString(PREF_HOST, "192.168.1.1") ?: "192.168.1.1"
        val port = prefs.getString(PREF_PORT, "") ?: ""

        val url = if (port.isEmpty()) {
            "$proto://$host"
        } else {
            "$proto://$host:$port"
        }

        title = "WebViewer"
        webView.loadUrl(url)
    }

    private fun showConfigDialog(firstTime: Boolean) {
        val savedProto = prefs.getString(PREF_PROTO, "http") ?: "http"
        val savedHost = prefs.getString(PREF_HOST, "") ?: ""
        val savedPort = prefs.getString(PREF_PORT, "") ?: ""

        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            val pad = (16 * resources.displayMetrics.density).toInt()
            setPadding(pad, pad, pad, pad)
        }

        fun addLabel(text: String) {
            layout.addView(TextView(this).apply {
                this.text = text
            })
        }

        fun addInput(initial: String, hint: String): EditText {
            return EditText(this).apply {
                setText(initial)
                this.hint = hint
                layout.addView(this)
            }
        }

        addLabel("Protocolo:")
        val etProto = addInput(savedProto, "http o https")

        addLabel("IP / Host:")
        val etHost = addInput(savedHost, "192.168.1.100 o miservidor.local")

        addLabel("Puerto (opcional):")
        val etPort = addInput(savedPort, "8080 (dejar vacío si no hace falta)")

        val builder = AlertDialog.Builder(this)
            .setTitle("Configurar servidor")
            .setView(layout)
            .setPositiveButton("Conectar") { _, _ ->
                var proto = etProto.text.toString().trim()
                val host = etHost.text.toString().trim()
                val port = etPort.text.toString().trim()

                if (proto.isEmpty()) proto = "http"

                prefs.edit()
                    .putString(PREF_PROTO, proto)
                    .putString(PREF_HOST, host)
                    .putString(PREF_PORT, port)
                    .apply()

                loadUrl()
            }

        if (!firstTime) {
            builder.setNegativeButton("Cancelar", null)
        }

        builder.setCancelable(!firstTime).show()
    }

    override fun onCreateOptionsMenu(menu: Menu): Boolean {
        menu.add(0, 1, 0, "Configurar servidor")
        menu.add(0, 2, 1, "Recargar")
        return true
    }

    override fun onOptionsItemSelected(item: MenuItem): Boolean {
        return when (item.itemId) {
            1 -> {
                showConfigDialog(false)
                true
            }
            2 -> {
                webView.reload()
                true
            }
            else -> super.onOptionsItemSelected(item)
        }
    }

    @Deprecated("Deprecated in Java")
    override fun onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack()
        } else {
            super.onBackPressed()
        }
    }
}
