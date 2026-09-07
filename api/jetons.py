#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Affiche (ou copie) les jetons à déclarer dans le Worker Cloudflare.

  python3 api/jetons.py            → affiche les deux jetons
  python3 api/jetons.py user       → copie TOKEN_USER dans le presse-papiers
  python3 api/jetons.py admin      → copie TOKEN_ADMIN dans le presse-papiers

Ne rebuilde rien, ne touche à aucun fichier.
"""
import base64
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ITERATIONS = 600_000


def lire(nom):
    f = ROOT / nom
    if not f.exists():
        sys.exit(f"Fichier {nom} introuvable — lancez d'abord python3 build.py")
    return f.read_text(encoding="utf-8").strip()


def jeton(mot_de_passe, sel):
    cle = hashlib.pbkdf2_hmac("sha256", mot_de_passe.encode(), sel, ITERATIONS, 32)
    return base64.b64encode(hashlib.sha256(cle + b"smr-api-v1").digest()).decode()


# build.py stocke le sel en hexadécimal dans .salt
sel = bytes.fromhex(lire(".salt"))

jetons = {
    "user": jeton(lire(".password"), sel),
    "admin": jeton(lire(".password_admin"), sel),
}

quoi = sys.argv[1].lower() if len(sys.argv) > 1 else None
if quoi in jetons:
    subprocess.run(["pbcopy"], input=jetons[quoi].encode(), check=True)
    print(f"TOKEN_{quoi.upper()} copié dans le presse-papiers "
          f"({len(jetons[quoi])} caractères). Collez-le dans Cloudflare avec ⌘V.")
else:
    print("À déclarer dans le Worker Cloudflare (type « Secret ») :\n")
    print(f"  TOKEN_USER  = {jetons['user']}")
    print(f"  TOKEN_ADMIN = {jetons['admin']}\n")
    print("Pour copier sans risque d'erreur :")
    print("  python3 api/jetons.py user")
    print("  python3 api/jetons.py admin")
