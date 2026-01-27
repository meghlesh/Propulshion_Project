import base64
import os
import sys
import traceback

from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


# Default iterations; keep same in JS and server
KDF_ITERATIONS = getattr(settings, "PAGE_ENCRYPT_KDF_ITERATIONS", 200000)


class EncryptHTMLMiddleware(MiddlewareMixin):
    """
    Returns ciphertext wrapper only when explicitly requested by the client:
      - query param ?encrypted=1
      - OR request header X-ENCRYPT: 1

    Otherwise the page is served normally.
    """

    EXCLUDE_PREFIXES = getattr(
        settings,
        "PAGE_ENCRYPT_EXCLUDE_PREFIXES",
        ["/static/", "/media/", "/api/"]
    )

    def _client_requested_encrypted(self, request):
        # query param
        if request.GET.get("encrypted") == "1":
            return True
        # header (HTTP_X_ENCRYPT because Django exposes headers as HTTP_*)
        if request.META.get("HTTP_X_ENCRYPT") == "1":
            return True
        return False

    def _should_encrypt(self, request, response):
        # Only consider HTML 200 responses
        content_type = response.get("Content-Type", "")
        if not content_type.startswith("text/html"):
            return False
        if response.status_code != 200:
            return False

        path = request.path or ""

        # Only allow encryption for admin-login (custom) OR django admin login
        if not (path.startswith("/admin/login") or path.startswith("/admin-login")):
            return False

        # exclude static/media
        for prefix in self.EXCLUDE_PREFIXES:
            if path.startswith(prefix):
                return False

        # global toggle
        if not getattr(settings, "ENABLE_PAGE_ENCRYPTION", True):
            return False

        # Finally: only encrypt if client explicitly asked for encryption
        return self._client_requested_encrypted(request)

    def process_response(self, request, response):
        try:
            if not self._should_encrypt(request, response):
                return response

            pwd = getattr(settings, "PAGE_ENCRYPT_PASSWORD", None)
            if not pwd:
                return response

            # get bytes
            if isinstance(response.content, str):
                plaintext = response.content.encode(response.charset or "utf-8")
            else:
                plaintext = response.content

            salt = os.urandom(16)
            iv = os.urandom(12)

            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=KDF_ITERATIONS,
            )
            key = kdf.derive(pwd.encode("utf-8"))

            aesgcm = AESGCM(key)
            ct = aesgcm.encrypt(iv, plaintext, None)

            ct_b64 = base64.b64encode(ct).decode("utf-8")
            iv_b64 = base64.b64encode(iv).decode("utf-8")
            salt_b64 = base64.b64encode(salt).decode("utf-8")

            # wrapper (double braces in f-string where needed)
            wrapper_html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>Encrypted Admin Login</title>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <style>
    html,body{{height:100%;margin:0;font-family:Inter,Arial,sans-serif;background:#0f172a;color:#fff}}
    .wrap{{padding:22px;max-width:980px;margin:40px auto}}
    .card{{background:#fff;color:#111;padding:18px;border-radius:8px;box-shadow:0 8px 30px rgba(0,0,0,.25)}}
    .title{{font-size:18px;font-weight:700;margin-bottom:10px}}
    textarea.cipher{{width:100%;height:220px;resize:vertical;font-family:monospace;font-size:12px;white-space:pre-wrap;word-break:break-all}}
    .controls{{display:flex;gap:8px;align-items:center;margin-top:10px}}
    input[type=password]{{padding:8px;border-radius:6px;border:1px solid #ddd;min-width:240px}}
    button{{padding:8px 12px;border-radius:6px;border:0;background:#0f172a;color:#fff;cursor:pointer}}
    .note{{margin-top:10px;color:#555;font-size:13px}}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card">
      <div class="title">Encrypted Admin Login — Ciphertext Only</div>
      <div>
        The server returned the admin login page as encrypted data. The real login form is not present until you decrypt locally.
      </div>
      <div style="margin-top:12px">
        <label style="font-weight:600;font-size:13px">Ciphertext (base64):</label>
        <textarea class="cipher" readonly id="cipherArea">{ct_b64}</textarea>
      </div>

      <div class="controls">
        <input id="enc_pw" type="password" placeholder="Enter password to decrypt" aria-label="Password"/>
        <button id="decBtn">Decrypt</button>
      </div>

      <div class="note">
        Tip: inspect Network → Preview/Response to confirm the server response contains only ciphertext. Elements will show only this wrapper until you decrypt here.
      </div>
      <pre id="debug" style="display:none"></pre>
    </div>
  </div>

  <script>
  (function(){{
    const ctB64 = "{ct_b64}";
    const ivB64 = "{iv_b64}";
    const saltB64 = "{salt_b64}";
    const iterations = {KDF_ITERATIONS};

    function b64ToArrayBuffer(b64){{
      return Uint8Array.from(atob(b64), c => c.charCodeAt(0)).buffer;
    }}

    async function deriveKey(password, saltBuffer){{
      const pwUtf8 = new TextEncoder().encode(password);
      const baseKey = await crypto.subtle.importKey('raw', pwUtf8, 'PBKDF2', false, ['deriveKey']);
      return crypto.subtle.deriveKey(
        {{name:'PBKDF2', salt: saltBuffer, iterations: iterations, hash:'SHA-256'}},
        baseKey,
        {{name:'AES-GCM', length:256}},
        false,
        ['decrypt']
      );
    }}

    async function decryptAndRender(password){{
      try {{
        const salt = new Uint8Array(b64ToArrayBuffer(saltB64));
        const iv = new Uint8Array(b64ToArrayBuffer(ivB64));
        const ct = b64ToArrayBuffer(ctB64);

        const key = await deriveKey(password, salt);
        const plainBuf = await crypto.subtle.decrypt({{name:'AES-GCM', iv: iv}}, key, ct);
        const decoder = new TextDecoder();
        const html = decoder.decode(plainBuf);

        document.open();
        document.write(html);
        document.close();
      }} catch(err) {{
        console.error('decrypt failed', err);
        alert('Decryption failed — wrong password or corrupted content.');
      }}
    }}

    document.getElementById('decBtn').addEventListener('click', function(){{
      const pw = document.getElementById('enc_pw').value || prompt('Password:');
      if (!pw) return alert('Password required');
      decryptAndRender(pw);
    }});
  }})();
  </script>
</body>
</html>"""

            response.content = wrapper_html.encode("utf-8")
            response["Content-Length"] = str(len(response.content))
            response["Content-Type"] = "text/html; charset=utf-8"
            return response

        except Exception:
            traceback.print_exc(file=sys.stderr)
            return response
