#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build du portail SOLIMED : chiffre les pages de src/ vers docs/ (GitHub Pages).

Usage :
    python3 build.py                    # utilise le mot de passe du fichier .password
    python3 build.py "MonMotDePasse"    # utilise ce mot de passe (et le sauvegarde dans .password)

- Chaque page HTML de src/ est chiffrée en AES-256-GCM, clé dérivée du mot de
  passe par PBKDF2-SHA256 (600 000 itérations, sel commun stocké dans .salt).
- Le sel commun permet le « se souvenir de moi » : un seul mot de passe saisi
  débloque toutes les pages du site sur cet ordinateur.
- src/assets/ est copié tel quel (logo, wheel Python — rien de sensible).
- La barre de navigation est centralisée dans nav.html (à la racine) : au build,
  elle remplace le bloc <nav>…</nav> de chaque page, avec la classe « active »
  posée automatiquement sur le lien de la page courante. Pour modifier la nav,
  éditer UNIQUEMENT nav.html puis rebuilder. (gme.html n'a pas de bloc <nav>
  et garde son bouton flottant « retour portail » : il n'est pas touché.)
- Le pied de page est centralisé de la même façon dans footer.html : injecté
  au build avant la balise </body> de CHAQUE page (gme.html compris — la
  mention d'usage restreint figure ainsi aussi dans les copies enregistrées).
- .password et .salt ne doivent JAMAIS être poussés sur GitHub (voir .gitignore).
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import secrets
import shutil
import sys
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
DOCS = ROOT / "docs"
PBKDF2_ITERATIONS = 600_000

GATE_TEMPLATE = (ROOT / "gate_template.html").read_text(encoding="utf-8")
NAV_TEMPLATE = (ROOT / "nav.html").read_text(encoding="utf-8").strip()
NAV_BLOCK_RE = re.compile(r"<nav\b[^>]*>.*?</nav>", re.DOTALL)
FOOTER_TEMPLATE = (ROOT / "footer.html").read_text(encoding="utf-8").strip()


def inject_footer(html: str) -> str:
    """Insère footer.html juste avant la DERNIÈRE balise </body> de la page.
    (« dernière » : gme.html contient un </body> échappé dans un template JS,
    seul le vrai </body> final doit être visé.)"""
    pos = html.rfind("</body>")
    if pos == -1:
        return html
    return html[:pos] + FOOTER_TEMPLATE + "\n" + html[pos:]


def inject_nav(html: str, page_name: str) -> tuple[str, bool]:
    """Remplace le bloc <nav>…</nav> de la page par nav.html,
    en marquant le lien de la page courante avec class="active".
    Retourne (html, True) si une nav a été injectée, (html, False) sinon."""
    if not NAV_BLOCK_RE.search(html):
        return html, False
    nav = NAV_TEMPLATE.replace(f'<a href="{page_name}">',
                               f'<a href="{page_name}" class="active">', 1)
    return NAV_BLOCK_RE.sub(lambda _m: nav, html, count=1), True


def get_password() -> str:
    """Mot de passe UTILISATEUR (profil lecture seule — celui du Dr Ducret)."""
    pw_file = ROOT / ".password"
    if len(sys.argv) > 1:
        pw = sys.argv[1]
        pw_file.write_text(pw, encoding="utf-8")
        print(f"Mot de passe enregistré dans {pw_file.name}")
        return pw
    if pw_file.exists():
        return pw_file.read_text(encoding="utf-8").strip()
    print("Erreur : aucun mot de passe. Lancez : python3 build.py \"VotreMotDePasse\"")
    sys.exit(1)


def get_admin_password() -> str | None:
    """Mot de passe ADMINISTRATRICE (profil de Marion), dans .password_admin.

    Absent → le site se construit avec un seul profil, comme avant."""
    pw_file = ROOT / ".password_admin"
    if not pw_file.exists():
        return None
    pw = pw_file.read_text(encoding="utf-8").strip()
    return pw or None


def get_salt() -> bytes:
    salt_file = ROOT / ".salt"
    if salt_file.exists():
        return bytes.fromhex(salt_file.read_text().strip())
    salt = secrets.token_bytes(16)
    salt_file.write_text(salt.hex(), encoding="utf-8")
    print("Nouveau sel généré (.salt) — le « se souvenir de moi » des utilisateurs sera réinitialisé.")
    return salt


def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt,
                     iterations=PBKDF2_ITERATIONS)
    return kdf.derive(password.encode("utf-8"))


def encrypt_bytes(data: bytes, key: bytes) -> tuple[str, str]:
    """Chiffre des octets en AES-256-GCM ; renvoie (nonce_b64, ciphertext_b64)."""
    nonce = secrets.token_bytes(12)
    ct = AESGCM(key).encrypt(nonce, data, None)
    return base64.b64encode(nonce).decode(), base64.b64encode(ct).decode()


def encrypt_page(html: str, key: bytes) -> tuple[str, str]:
    return encrypt_bytes(html.encode("utf-8"), key)


def get_content_key() -> bytes:
    """Clé de contenu (CEK) : c'est ELLE qui chiffre les pages.

    Chaque mot de passe la reçoit sous enveloppe (« key wrapping »), ce qui
    permet d'ouvrir le MÊME site avec deux mots de passe différents et de
    savoir lequel a servi — donc de connaître le profil (admin / utilisateur).
    Comme .password et .salt, ce fichier ne doit JAMAIS être poussé."""
    cek_file = ROOT / ".cek"
    if cek_file.exists():
        return bytes.fromhex(cek_file.read_text().strip())
    cek = secrets.token_bytes(32)
    cek_file.write_text(cek.hex(), encoding="utf-8")
    print("Nouvelle clé de contenu générée (.cek).")
    return cek


def api_token(derived_key: bytes) -> str:
    """Jeton présenté à l'API (Worker Cloudflare).

    Dérivé de la clé du mot de passe, mais distinct d'elle : le Worker ne peut
    donc pas déchiffrer les pages du site avec ce qu'il connaît."""
    return base64.b64encode(
        hashlib.sha256(derived_key + b"smr-api-v1").digest()).decode()


def get_api_url() -> str:
    """URL du Worker (api/url.txt). Vide = pages Admin en lecture seule locale."""
    f = ROOT / "api" / "url.txt"
    if not f.exists():
        return ""
    return f.read_text(encoding="utf-8").strip()


def main():
    password = get_password()
    admin_password = get_admin_password()
    salt = get_salt()
    key = derive_key(password, salt)
    content_key = get_content_key()
    api_url = get_api_url()

    # Enveloppes : la clé de contenu, chiffrée par la clé de chaque mot de passe.
    wraps = {}
    n, c = encrypt_bytes(content_key, key)
    wraps["user"] = {"nonce": n, "ciphertext": c}
    admin_key = None
    if admin_password:
        if admin_password == password:
            print("Erreur : le mot de passe admin doit être différent de celui des utilisateurs.")
            sys.exit(1)
        admin_key = derive_key(admin_password, salt)
        n, c = encrypt_bytes(content_key, admin_key)
        wraps["admin"] = {"nonce": n, "ciphertext": c}

    # Écrasement en place (pas de suppression : compatible avec tous les
    # environnements, y compris ceux où l'effacement est restreint).
    DOCS.mkdir(exist_ok=True)

    # Assets copiés en clair (logo, wheels Python, référentiels : non sensibles)
    if (SRC / "assets").exists():
        shutil.copytree(SRC / "assets", DOCS / "assets", dirs_exist_ok=True)

    # .nojekyll : indispensable pour que GitHub Pages serve tous les fichiers tels quels
    (DOCS / ".nojekyll").write_text("")

    # Icônes à la racine du site (Safari et certains navigateurs les cherchent là)
    for icon in ("favicon.ico", "apple-touch-icon.png"):
        icon_path = SRC / "assets" / icon
        if icon_path.exists():
            shutil.copy(icon_path, DOCS / icon)

    pages = sorted(SRC.glob("*.html"))
    for page in pages:
        html = page.read_text(encoding="utf-8")
        html, nav_ok = inject_nav(html, page.name)
        html = inject_footer(html)
        nonce_b64, ct_b64 = encrypt_page(html, content_key)
        payload = json.dumps({
            "salt": base64.b64encode(salt).decode(),
            "iterations": PBKDF2_ITERATIONS,
            "nonce": nonce_b64,
            "ciphertext": ct_b64,
            "wraps": wraps,
            "api": api_url,
        })
        out = (GATE_TEMPLATE
               .replace("__PAYLOAD__", payload)
               .replace("__TITLE__", "Outils SMR — Accès protégé"))
        (DOCS / page.name).write_text(out, encoding="utf-8")
        nav_note = "nav injectée" if nav_ok else "pas de bloc <nav> (page laissée telle quelle)"
        print(f"  ✔ {page.name} chiffré → docs/{page.name} ({nav_note})")

    print(f"\nBuild terminé : {len(pages)} pages dans docs/. "
          f"Poussez le dossier docs/ sur GitHub pour publier.")

    if admin_key is not None:
        print("\nProfils : utilisateur (.password) + administratrice (.password_admin).")
        print("Jetons à déclarer dans le Worker Cloudflare (Settings → Variables, "
              "en cochant « Encrypt ») :")
        print(f"  TOKEN_USER  = {api_token(key)}")
        print(f"  TOKEN_ADMIN = {api_token(admin_key)}")
        if not api_url:
            print("  ⚠️  api/url.txt est vide : renseignez-y l'URL du Worker puis rebuildez.")
    else:
        print("\nProfil unique (pas de .password_admin) : le site s'ouvre comme avant.")


if __name__ == "__main__":
    main()
