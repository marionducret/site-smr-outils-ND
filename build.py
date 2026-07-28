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
- .password et .salt ne doivent JAMAIS être poussés sur GitHub (voir .gitignore).
"""

import base64
import json
import os
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


def get_password() -> str:
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


def encrypt_page(html: str, key: bytes) -> tuple[str, str]:
    nonce = secrets.token_bytes(12)
    ct = AESGCM(key).encrypt(nonce, html.encode("utf-8"), None)
    return base64.b64encode(nonce).decode(), base64.b64encode(ct).decode()


def main():
    password = get_password()
    salt = get_salt()
    key = derive_key(password, salt)

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
        nonce_b64, ct_b64 = encrypt_page(html, key)
        payload = json.dumps({
            "salt": base64.b64encode(salt).decode(),
            "iterations": PBKDF2_ITERATIONS,
            "nonce": nonce_b64,
            "ciphertext": ct_b64,
        })
        out = (GATE_TEMPLATE
               .replace("__PAYLOAD__", payload)
               .replace("__TITLE__", "SOLIMED — Accès protégé"))
        (DOCS / page.name).write_text(out, encoding="utf-8")
        print(f"  ✔ {page.name} chiffré → docs/{page.name}")

    print(f"\nBuild terminé : {len(pages)} pages dans docs/. "
          f"Poussez le dossier docs/ sur GitHub pour publier.")


if __name__ == "__main__":
    main()
