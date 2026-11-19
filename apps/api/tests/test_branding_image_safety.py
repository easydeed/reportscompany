"""LR-007 (Jerry's option 1): pasted image links are imported, never saved as-is.

Four parts, each driven through the real code:
  * the image pipeline: phone multi-picture JPEGs accepted (primary image),
    metadata stripped by re-encoding, orientation applied, clear refusals;
  * the guarded fetcher, including a REAL local TLS server to prove the
    connection is pinned to the checked address while TLS is verified
    against the hostname;
  * the import route;
  * branding saves accept only our storage URLs or values already stored.
"""
import asyncio
import datetime
import ipaddress
import os
import socket
import ssl
import threading
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from io import BytesIO
from unittest.mock import Mock

import psycopg
import pytest
from fastapi import HTTPException, UploadFile
from PIL import Image
from starlette.datastructures import Headers

from api.services import branding_urls, safe_fetch, upload

DB_URL = os.getenv("DATABASE_URL")
PUBLIC = "https://assets.example.com"
OURS = f"{PUBLIC}/branding/acct/logo_20261119_abcd1234.png"


def jpeg_with_gps(size=(300, 200), orientation=None):
    exif = Image.Exif()
    exif[0x8825] = {2: (34.0, 8.0, 0.0), 1: "N"}                  # GPS IFD
    exif[0x0110] = "Secret Camera Model"
    if orientation:
        exif[0x0112] = orientation
    buf = BytesIO()
    Image.new("RGB", size, "white").save(buf, format="JPEG", exif=exif.tobytes())
    data = buf.getvalue()
    # An XMP packet in its own APP1 segment, right after SOI (Pillow 10 cannot write one).
    payload = b"http://ns.adobe.com/xap/1.0/\x00<x:xmpmeta>secret-xmp</x:xmpmeta>"
    segment = b"\xff\xe1" + (len(payload) + 2).to_bytes(2, "big") + payload
    return data[:2] + segment + data[2:]


def phone_mpo():
    buf = BytesIO()
    primary = Image.new("RGB", (400, 300), "red")
    primary.save(buf, format="MPO", save_all=True, append_images=[Image.new("RGB", (160, 120), "blue")])
    return buf.getvalue()


def submit(data, filename, mime):
    return asyncio.run(upload.validate_image(
        UploadFile(file=BytesIO(data), filename=filename, headers=Headers({"content-type": mime}))))


# ── the image pipeline ──────────────────────────────────────────────────────

def test_a_phone_multi_picture_jpeg_is_accepted_as_its_primary_image():
    data = phone_mpo()
    with Image.open(BytesIO(data)) as raw:
        assert raw.format == "MPO" and getattr(raw, "n_frames", 1) == 2     # what a phone sends
    stored, ext, mime = submit(data, "IMG_0042.jpg", "image/jpeg")
    assert (ext, mime) == ("jpg", "image/jpeg")
    with Image.open(BytesIO(stored)) as kept:
        assert kept.format == "JPEG" and kept.size == (400, 300)
        assert getattr(kept, "n_frames", 1) == 1                            # depth/preview frames dropped
        assert kept.getpixel((10, 10))[0] > 200                             # the red primary, not the blue


def test_re_encoding_strips_gps_camera_and_xmp():
    data = jpeg_with_gps()
    assert b"secret-xmp" in data and Image.open(BytesIO(data)).getexif().get_ifd(0x8825)
    stored, _, _ = submit(data, "me.jpg", "image/jpeg")
    with Image.open(BytesIO(stored)) as kept:
        exif = kept.getexif()
        assert not exif.get_ifd(0x8825) and 0x0110 not in exif
        assert "xmp" not in kept.info and "exif" not in kept.info
    assert b"secret-xmp" not in stored and b"Secret Camera" not in stored


def test_a_sideways_phone_photo_is_stored_upright():
    data = jpeg_with_gps(size=(300, 200), orientation=6)                 # "rotate 90 to display"
    stored, _, _ = submit(data, "me.jpg", "image/jpeg")
    with Image.open(BytesIO(stored)) as kept:
        assert kept.size == (200, 300)                                    # orientation applied to pixels
        assert kept.getexif().get(0x0112) in (None, 1)                    # and not applied twice


def test_bytes_appended_after_the_image_are_not_stored():
    buf = BytesIO()
    Image.new("RGBA", (120, 120), (0, 0, 0, 0)).save(buf, format="PNG")
    data = buf.getvalue() + b"<script>alert(1)</script>"
    stored, _, _ = submit(data, "logo.png", "image/png")
    assert b"<script>" not in stored
    with Image.open(BytesIO(stored)) as kept:
        assert kept.format == "PNG" and kept.mode == "RGBA"               # transparency kept


@pytest.mark.parametrize("data,name,mime,says", [
    (b"plain text", "logo.png", "image/png", "isn't a PNG, JPEG, WebP or GIF"),
    (b"<svg/>", "logo.svg", "image/svg+xml", "isn't a PNG, JPEG, WebP or GIF"),
    ("png", "logo.jpg", "image/jpeg", "is a PNG image, but its name or type says otherwise"),
    ("tiny", "logo.png", "image/png", "is 50x50 pixels"),
    ("truncated", "logo.jpg", "image/jpeg", "couldn't be read"),
])
def test_real_failures_say_what_is_wrong(data, name, mime, says):
    if data == "png":
        buf = BytesIO(); Image.new("RGB", (120, 120)).save(buf, format="PNG"); data = buf.getvalue()
    elif data == "tiny":
        buf = BytesIO(); Image.new("RGB", (50, 50)).save(buf, format="PNG"); data = buf.getvalue()
    elif data == "truncated":
        data = jpeg_with_gps()[:200]
    with pytest.raises(HTTPException) as refused:
        submit(data, name, mime)
    assert refused.value.status_code == 400 and says in refused.value.detail


# ── the guarded fetcher: refusals ───────────────────────────────────────────

@pytest.mark.parametrize("url,says", [
    ("http://images.example.com/a.png", "Only https"),
    ("https://user:pw@images.example.com/a.png", "username or password"),
    ("https://images.example.com:8443/a.png", "standard https port"),
    ("https://127.0.0.1/a.png", "private or reserved"),
    ("https://10.0.0.5/a.png", "private or reserved"),
    ("https://169.254.169.254/latest/meta-data/", "private or reserved"),
    ("https://[::1]/a.png", "private or reserved"),
    ("https://[::ffff:127.0.0.1]/a.png", "private or reserved"),
    ("https://localhost/a.png", "private or reserved"),
])
def test_the_fetcher_refuses_anything_but_a_public_https_host(url, says):
    with pytest.raises(safe_fetch.FetchRefused) as refused:
        safe_fetch.fetch(url, max_bytes=1024)
    assert says in str(refused.value)


def test_one_private_answer_among_public_ones_refuses_the_host(monkeypatch):
    def resolve(host, port, *args, **kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443)),
                (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.1.2.3", 443))]
    monkeypatch.setattr(socket, "getaddrinfo", resolve)
    with pytest.raises(safe_fetch.FetchRefused, match="private or reserved"):
        safe_fetch.fetch("https://mixed.example.com/a.png", max_bytes=1024)


# ── the guarded fetcher: a real TLS server ──────────────────────────────────

@pytest.fixture
def tls_server(tmp_path):
    """HTTPS on 127.0.0.1 with a certificate for images.example.com only."""
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.x509.oid import NameOID

    key = ec.generate_private_key(ec.SECP256R1())
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "images.example.com")])
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
            .serial_number(x509.random_serial_number()).not_valid_before(now - datetime.timedelta(days=1))
            .not_valid_after(now + datetime.timedelta(days=1))
            .add_extension(x509.SubjectAlternativeName([x509.DNSName("images.example.com")]), critical=False)
            .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
            .sign(key, hashes.SHA256()))
    cert_file, key_file = tmp_path / "cert.pem", tmp_path / "key.pem"
    cert_file.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    key_file.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                           serialization.NoEncryption()))
    seen, routes = [], {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            seen.append({"path": self.path, "host": self.headers.get("Host")})
            status, headers, body = routes.get(self.path, (404, {}, b""))
            self.send_response(status)
            for k, v in headers.items():
                self.send_header(k, v)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(cert_file, key_file)
    server.socket = ctx.wrap_socket(server.socket, server_side=True)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    client_ctx = ssl.create_default_context(cafile=str(cert_file))
    yield {"port": port, "seen": seen, "routes": routes, "verify": client_ctx}
    server.shutdown()


@pytest.fixture
def pinned(monkeypatch, tls_server):
    """Resolve the test names; only the test server's loopback counts as public."""
    names = {"images.example.com": "127.0.0.1", "internal.example.com": "10.0.0.7"}
    real_getaddrinfo, real_public = socket.getaddrinfo, safe_fetch._is_public

    def resolve(host, port, *args, **kwargs):
        if host in names:
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (names[host], port or 443))]
        return real_getaddrinfo(host, port, *args, **kwargs)

    monkeypatch.setattr(socket, "getaddrinfo", resolve)
    monkeypatch.setattr(safe_fetch, "_is_public", lambda a: a == "127.0.0.1" or real_public(a))
    # Connect to the test server's port wherever the fetcher pins 443.
    import httpcore
    real_connect = httpcore._backends.sync.SyncBackend.connect_tcp

    def connect_tcp(self, host, port, *args, **kwargs):
        if host == "127.0.0.1" and port == 443:
            port = tls_server["port"]
        return real_connect(self, host, port, *args, **kwargs)

    monkeypatch.setattr(httpcore._backends.sync.SyncBackend, "connect_tcp", connect_tcp)
    return tls_server


def png_bytes():
    buf = BytesIO()
    Image.new("RGB", (150, 150), "green").save(buf, format="PNG")
    return buf.getvalue()


def test_a_public_host_is_fetched_pinned_with_tls_verified_against_its_name(pinned):
    pinned["routes"]["/logo.png"] = (200, {"Content-Type": "image/png"}, png_bytes())
    body = safe_fetch.fetch("https://images.example.com/logo.png", max_bytes=1 << 20, verify=pinned["verify"])
    assert body == png_bytes()
    # Connected to the checked address, yet the request named the host: the
    # certificate (valid only for images.example.com) verified, so SNI and
    # hostname verification used the name, not the IP.
    assert pinned["seen"][-1] == {"path": "/logo.png", "host": "images.example.com"}


def test_a_redirect_to_a_private_address_is_refused(pinned):
    pinned["routes"]["/hop"] = (302, {"Location": "https://internal.example.com/secret"}, b"")
    with pytest.raises(safe_fetch.FetchRefused, match="private or reserved"):
        safe_fetch.fetch("https://images.example.com/hop", max_bytes=1 << 20, verify=pinned["verify"])


def test_too_many_redirects_and_oversized_bodies_are_refused(pinned):
    for i in range(5):
        pinned["routes"][f"/r{i}"] = (302, {"Location": f"/r{i + 1}"}, b"")
    with pytest.raises(safe_fetch.FetchRefused, match="too many times"):
        safe_fetch.fetch("https://images.example.com/r0", max_bytes=1 << 20, verify=pinned["verify"])
    pinned["routes"]["/big.png"] = (200, {}, b"x" * 5000)
    with pytest.raises(safe_fetch.FetchRefused, match="too large"):
        safe_fetch.fetch("https://images.example.com/big.png", max_bytes=4000, verify=pinned["verify"])


def test_a_certificate_for_another_name_is_refused(pinned, monkeypatch):
    """The pinned IP must not weaken TLS: a name the certificate doesn't cover fails."""
    real = socket.getaddrinfo
    monkeypatch.setattr(socket, "getaddrinfo",
                        lambda host, port, *a, **k: real("images.example.com", port, *a, **k)
                        if host == "evil.example.com" else real(host, port, *a, **k))
    with pytest.raises(safe_fetch.FetchRefused, match="certificate"):
        safe_fetch.fetch("https://evil.example.com/logo.png", max_bytes=1 << 20, verify=pinned["verify"])


# ── branding saves ──────────────────────────────────────────────────────────

@pytest.fixture
def ours(monkeypatch):
    monkeypatch.setattr(upload, "R2_PUBLIC_URL", PUBLIC)
    monkeypatch.setattr(upload, "get_r2_client", lambda: Mock())


def test_the_save_rule(ours):
    check = branding_urls.check_image_urls
    check({"logo_url": OURS})                                             # our storage
    check({"logo_url": None, "footer_logo_url": ""})                      # not sent, cleared
    legacy = "https://cdn.pct.example/logo.svg"
    check({"logo_url": legacy, "email_logo_url": legacy}, [legacy, None]) # kept, and copied across fields
    for bad in ("https://evil.example/x.png", f"{PUBLIC}/elsewhere/x.png", "http://assets.example.com/branding/x.png",
                f"{PUBLIC}/branding/../secrets.png", "javascript:alert(1)"):
        with pytest.raises(HTTPException) as refused:
            check({"logo_url": bad}, [legacy])
        assert refused.value.status_code == 400 and "paste an image URL" in refused.value.detail


PASSWORD = "lr007-test-pass-1"


@pytest.fixture
def agent():
    if not DB_URL:
        pytest.skip("DATABASE_URL (a disposable local database) is needed")
    uid = str(uuid.uuid4())
    email = f"lr007-{uid[:8]}@example.com"
    legacy = f"https://cdn.pct.example/{uid[:6]}/logo.svg"
    with psycopg.connect(DB_URL) as conn, conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
        cur.execute("""INSERT INTO accounts (id, name, slug, account_type, plan_slug, status, is_active,
                                             logo_url, created_at, updated_at)
                       VALUES (%s, 'LR007', %s, 'REGULAR', 'free', 'active', true, %s, now(), now())""",
                    (uid, f"lr007-{uid[:8]}", legacy))
        cur.execute("""INSERT INTO users (id, account_id, email, password_hash, role, email_verified, is_active,
                                          is_platform_admin, first_name, avatar_url, created_at, updated_at)
                       VALUES (%s, %s, %s, crypt(%s, gen_salt('bf')), 'OWNER', true, true, false, 'Ann', %s,
                               now(), now())""", (uid, uid, email, PASSWORD, legacy))
        cur.execute("INSERT INTO account_users (account_id, user_id, role, created_at) VALUES (%s, %s, 'OWNER', now())",
                    (uid, uid))
        conn.commit()
    yield {"id": uid, "email": email, "legacy": legacy}
    with psycopg.connect(DB_URL) as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM account_users WHERE user_id = %s", (uid,))
        cur.execute("DELETE FROM users WHERE id = %s", (uid,))
        cur.execute("DELETE FROM accounts WHERE id = %s", (uid,))
        conn.commit()


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient
    from api.main import app
    return TestClient(app)


def login(client, email):
    r = client.post("/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def account_logos(uid):
    with psycopg.connect(DB_URL) as conn:
        return conn.execute("SELECT logo_url, email_logo_url FROM accounts WHERE id = %s", (uid,)).fetchone()


def test_an_agent_cannot_save_a_link_to_another_site(client, agent, ours):
    auth = login(client, agent["email"])
    r = client.patch("/v1/account/branding", headers=auth, json={"logo_url": "https://evil.example/x.png"})
    assert r.status_code == 400 and "paste an image URL" in r.json()["detail"]
    assert account_logos(agent["id"])[0] == agent["legacy"]                # nothing written
    r = client.patch("/v1/users/me", headers=auth, json={"avatar_url": "https://evil.example/me.jpg"})
    assert r.status_code == 400


def test_existing_and_imported_images_still_save(client, agent, ours):
    auth = login(client, agent["email"])
    # The branding page sends the unchanged legacy logo, copied into the email logo too.
    r = client.patch("/v1/account/branding", headers=auth,
                     json={"logo_url": agent["legacy"], "email_logo_url": agent["legacy"], "primary_color": "#123456"})
    assert r.status_code == 200, r.text
    assert account_logos(agent["id"]) == (agent["legacy"], agent["legacy"])
    r = client.patch("/v1/account/branding", headers=auth, json={"logo_url": OURS})
    assert r.status_code == 200 and account_logos(agent["id"])[0] == OURS
    assert client.patch("/v1/users/me", headers=auth, json={"avatar_url": agent["legacy"]}).status_code == 200


def test_the_import_route_stores_a_checked_copy(client, agent, ours, monkeypatch):
    auth = login(client, agent["email"])
    store = Mock()
    monkeypatch.setattr(upload, "get_r2_client", lambda: store)
    from api.routes import upload as upload_routes
    monkeypatch.setattr(upload_routes.safe_fetch, "fetch", lambda url, max_bytes: phone_mpo())
    r = client.post("/v1/upload/branding/headshot/import", headers=auth, json={"url": "https://images.example.com/me.jpg"})
    assert r.status_code == 200, r.text
    put = store.put_object.call_args.kwargs
    assert put["ContentType"] == "image/jpeg" and put["Key"].startswith(f"branding/{agent['id']}/headshot_")
    with Image.open(BytesIO(put["Body"])) as kept:                       # checked and re-encoded, not raw
        assert kept.format == "JPEG" and getattr(kept, "n_frames", 1) == 1 and kept.size == (400, 300)
    assert r.json()["url"] == f"{PUBLIC}/{put['Key']}"
    assert branding_urls.is_own_storage_url(r.json()["url"])               # so the form can save it

    def refuse(url, max_bytes):
        raise safe_fetch.FetchRefused("That link points to a private or reserved network address.")
    monkeypatch.setattr(upload_routes.safe_fetch, "fetch", refuse)
    store.reset_mock()
    r = client.post("/v1/upload/branding/logo/import", headers=auth, json={"url": "https://169.254.169.254/x"})
    assert r.status_code == 400 and "private or reserved" in r.json()["detail"]
    store.put_object.assert_not_called()


def test_every_route_that_writes_a_branding_image_checks_it():
    """A new writer of these columns must call check_image_urls (LR-007)."""
    import re
    from pathlib import Path
    routes = Path(upload.__file__).resolve().parents[1] / "routes"
    writes = re.compile(r"(logo_url|avatar_url|rep_photo_url)\s*=\s*%s"
                        r"|INSERT INTO (affiliate_branding|accounts|users)\s*\([^)]*(logo_url|avatar_url|rep_photo_url)")
    for path in routes.glob("*.py"):
        text = path.read_text()
        if writes.search(text):
            assert "check_image_urls" in text, f"{path.name} writes a branding image URL without check_image_urls"
