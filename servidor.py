"""
ScanSUS - Servidor Local HTTPS
Gera certificado autoassinado. Compatível com acesso pelo celular via HTTPS.
"""
import http.server, ssl, os, sys, webbrowser, threading, subprocess, tempfile, socket, time

PORT = 4443
HOST = "0.0.0.0"
APP_FILE = "scanner-sus-v4.html"


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def _gerar_com_cryptography(cert_path, key_path):
    try:
        for mod in list(sys.modules.keys()):
            if "cryptography" in mod:
                del sys.modules[mod]

        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.x509 import IPAddress
        import ipaddress, datetime

        ip_local = get_local_ip()

        pk = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        nome = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, u"scansus-local")])

        san_entries = [
            x509.DNSName(u"localhost"),
            x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
        ]
        try:
            san_entries.append(x509.IPAddress(ipaddress.IPv4Address(ip_local)))
        except Exception:
            pass

        cert_obj = (
            x509.CertificateBuilder()
            .subject_name(nome).issuer_name(nome)
            .public_key(pk.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime.utcnow())
            .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=3650))
            .add_extension(
                x509.SubjectAlternativeName(san_entries),
                critical=False)
            .sign(pk, hashes.SHA256())
        )
        with open(key_path, "wb") as f:
            f.write(pk.private_bytes(serialization.Encoding.PEM,
                    serialization.PrivateFormat.TraditionalOpenSSL,
                    serialization.NoEncryption()))
        with open(cert_path, "wb") as f:
            f.write(cert_obj.public_bytes(serialization.Encoding.PEM))
        print("      Certificado gerado com sucesso (inclui IP local)!")
        return True
    except Exception as e:
        print(f"      Erro cryptography: {e}")
        return False


def gerar_certificado():
    tmp  = tempfile.gettempdir()
    cert = os.path.join(tmp, "scansus_cert.pem")
    key  = os.path.join(tmp, "scansus_key.pem")

    if os.path.exists(cert) and os.path.exists(key):
        print("      Certificado existente reutilizado.")
        return cert, key

    # Tentativa 1: openssl (inclui IP no SAN)
    ip_local = get_local_ip()
    san_str = f"subjectAltName=DNS:localhost,IP:127.0.0.1,IP:{ip_local}"
    ext_file = os.path.join(tmp, "scansus_ext.cnf")
    with open(ext_file, "w") as f:
        f.write(san_str)

    for exe in ["openssl",
                os.path.join(os.path.dirname(sys.executable), "openssl.exe"),
                r"C:\Program Files\Git\usr\bin\openssl.exe"]:
        try:
            subprocess.run(
                [exe, "req", "-x509", "-newkey", "rsa:2048",
                 "-keyout", key, "-out", cert, "-days", "3650",
                 "-nodes", "-subj", "/CN=scansus-local",
                 "-addext", san_str],
                check=True, capture_output=True, timeout=30)
            print("      Certificado gerado via openssl (com SAN).")
            return cert, key
        except Exception:
            pass
        try:
            subprocess.run(
                [exe, "req", "-x509", "-newkey", "rsa:2048",
                 "-keyout", key, "-out", cert, "-days", "3650",
                 "-nodes", "-subj", f"/CN={ip_local}"],
                check=True, capture_output=True, timeout=30)
            print("      Certificado gerado via openssl.")
            return cert, key
        except Exception:
            continue

    if _gerar_com_cryptography(cert, key):
        return cert, key

    print("      Instalando dependencia SSL (so acontece uma vez)...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "cryptography", "-q",
             "--disable-pip-version-check", "--no-warn-script-location"],
            timeout=180, check=True, capture_output=True)
    except Exception as e:
        raise RuntimeError(f"Falha ao instalar cryptography: {e}")

    if _gerar_com_cryptography(cert, key):
        return cert, key

    raise RuntimeError(
        "Nao foi possivel gerar certificado SSL.\n"
        "Instale o Git for Windows (https://git-scm.com) que inclui o openssl, depois tente novamente."
    )


def abrir_navegador(url):
    def _open():
        time.sleep(2.0)
        webbrowser.open(url)
    threading.Thread(target=_open, daemon=True).start()


def print_qr(url):
    """Exibe o URL de forma destacada para acesso pelo celular."""
    print()
    print("  ┌─────────────────────────────────────────────┐")
    print("  │           ACESSO PELO CELULAR               │")
    print("  ├─────────────────────────────────────────────┤")
    print(f"  │  {url:<43} │")
    print("  └─────────────────────────────────────────────┘")
    print()
    print("  PASSOS para abrir no celular:")
    print("  1. Conecte o celular no mesmo Wi-Fi do computador")
    print("  2. Abra o link acima no Chrome ou Safari")
    print("  3. Aparecerá aviso 'site não seguro' — é normal")
    print('  4. Toque "Avançado" → "Ir para o site (não seguro)"')
    print("  5. Permita o acesso à câmera quando solicitado")


def main():
    base = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(base, APP_FILE)

    if not os.path.exists(app_path):
        print(f"\n[ERRO] '{APP_FILE}' nao encontrado em: {base}")
        print(f"Certifique-se que servidor.py e {APP_FILE} estao na mesma pasta.")
        input("\nPressione Enter para fechar...")
        sys.exit(1)

    print()
    print("=" * 54)
    print("  ScanSUS v4 - Servidor Local HTTPS")
    print("=" * 54)
    print()
    print("[1/3] Gerando certificado HTTPS...")

    try:
        cert, key = gerar_certificado()
    except RuntimeError as e:
        print(f"\n[ERRO] {e}")
        input("\nPressione Enter para fechar...")
        sys.exit(1)

    print("[2/3] Iniciando servidor...")
    os.chdir(base)

    class SilentHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, fmt, *args):
            # Mostra apenas erros
            if args and str(args[1]).startswith(('4','5')):
                print(f"  [req] {args[0]} {args[1]}")

    try:
        httpd = http.server.HTTPServer((HOST, PORT), SilentHandler)
    except OSError:
        print(f"\n[ERRO] Porta {PORT} ja em uso.")
        print("Feche outros processos usando essa porta e tente novamente.")
        input("\nPressione Enter para fechar...")
        sys.exit(1)

    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(cert, key)
    httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)

    ip = get_local_ip()
    url_pc      = f"https://localhost:{PORT}/{APP_FILE}"
    url_celular = f"https://{ip}:{PORT}/{APP_FILE}"

    print("      OK!")
    print("[3/3] Abrindo navegador no computador...")
    abrir_navegador(url_pc)

    print()
    print("=" * 54)
    print("  NAO FECHE ESTA JANELA enquanto usar o app!")
    print("=" * 54)
    print()
    print(f"  Computador : {url_pc}")

    print_qr(url_celular)

    print("=" * 54)
    print()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n  Servidor encerrado (Ctrl+C).")


if __name__ == "__main__":
    main()
