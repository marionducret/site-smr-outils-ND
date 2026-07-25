# Portail des outils SOLIMED

Site statique qui regroupe tous les outils SOLIMED pour les médecins DIM :
**Rapport mensuel** (app Streamlit), **Analyse GME** et **Convertisseur RHS → ENC**,
avec tutoriels intégrés. Protégé par un mot de passe partagé. Fonctionne sur Mac
et Windows, dans le navigateur, sans rien installer. 100 % gratuit.

## Structure

```
├── src/                  ← pages EN CLAIR (à ne PAS pousser sur un repo public)
│   ├── index.html        ← accueil + tutoriels
│   ├── rapport.html      ← intégration de l'app Streamlit (URL à renseigner, voir plus bas)
│   ├── gme.html          ← outil Analyse GME (copie d'Evolution_GME.html + lien retour portail)
│   ├── rhs.html          ← convertisseur RHS → ENC (Python dans le navigateur via Pyodide)
│   └── assets/           ← logo + wheel xlsxwriter (auto-hébergée)
├── docs/                 ← version CHIFFRÉE publiée sur GitHub Pages (générée par build.py)
├── build.py              ← chiffre src/ → docs/ (AES-256-GCM, PBKDF2 600k itérations)
├── gate_template.html    ← écran de saisie du mot de passe
├── .password             ← mot de passe actuel (JAMAIS sur GitHub)
├── .salt                 ← sel de dérivation (JAMAIS sur GitHub)
└── tests/                ← RHS synthétique + générateur, pour tester sans données réelles
```

## Déploiement initial sur GitHub Pages (une seule fois)

1. Créer un repo **public** sur GitHub, par ex. `solimed-outils`
   (⚠️ avec un compte GitHub gratuit, Pages ne fonctionne que sur un repo public —
   c'est pour ça que `src/` est dans `.gitignore` : seule la version chiffrée `docs/` est publiée).
2. Dans ce dossier :
   ```bash
   git init
   git add .
   git commit -m "Portail outils SOLIMED"
   git branch -M main
   git remote add origin https://github.com/marionducret/solimed-outils.git
   git push -u origin main
   ```
3. Sur GitHub : **Settings → Pages → Branch : `main`, dossier : `/docs`** → Save.
4. Après ~1 minute, le site est en ligne sur
   `https://marionducret.github.io/solimed-outils/`.
   Transmettre cette URL + le mot de passe aux médecins DIM (via Nathalie).

> Si tu as un compte GitHub Pro, tu peux mettre le repo en **privé** et retirer
> `src/` du `.gitignore` pour tout versionner au même endroit.

## Mettre à jour un outil ou une page

1. Modifier le fichier dans `src/` (par ex. remplacer `src/gme.html` par une
   nouvelle version d'Evolution_GME.html — penser à réinjecter le lien retour,
   ou me redemander).
2. Rebuilder puis pousser :
   ```bash
   python3 build.py
   git add docs && git commit -m "maj outil X" && git push
   ```

## Changer le mot de passe

```bash
python3 build.py "NouveauMotDePasse"
git add docs && git commit -m "nouveau mot de passe" && git push
```
Le mot de passe actuel est dans `.password`. Les utilisateurs devront ressaisir
le nouveau mot de passe (le « se souvenir de moi » est invalidé automatiquement).

## Renseigner l'URL de l'app Rapport mensuel

Dans `src/rapport.html`, remplacer la ligne :
```js
const STREAMLIT_URL = "https://VOTRE-APP.streamlit.app";
```
par l'URL réelle de l'app Streamlit, puis rebuilder (`python3 build.py`) et pousser.

## Convertisseur RHS : comment ça marche

- Le code de `ENC/app_txt_rhs/main.py` est embarqué **tel quel** dans `src/rhs.html`
  et exécuté dans le navigateur par [Pyodide](https://pyodide.org) (Python compilé
  en WebAssembly, chargé depuis le CDN jsdelivr au premier usage, ~15 Mo, mis en cache).
- La wheel `xlsxwriter` est auto-hébergée dans `src/assets/` (pas de dépendance PyPI).
- **Aucune donnée patient ne quitte le poste du médecin** : lecture, conversion et
  écriture de l'Excel se font entièrement en local dans l'onglet du navigateur.
- Sortie strictement identique à l'outil Python d'origine (vérifié octet par octet
  sur le RHS synthétique de `tests/`).
- Si `main.py` évolue : recopier son contenu dans `src/rhs.html` entre les balises
  `<script type="text/x-python" id="main-py">` et `</script>`, rebuilder, pousser
  (ou me demander de le faire).

## Sécurité — ce qu'il faut savoir

- Chaque page publiée est chiffrée en **AES-256-GCM**, clé dérivée du mot de passe
  par **PBKDF2-SHA256 (600 000 itérations)**. Sans le mot de passe, le contenu
  publié sur GitHub est illisible.
- Le mot de passe protège l'**accès aux outils**, pas des données patient : aucune
  donnée patient n'est stockée sur le site. Les outils « 100 % local » traitent
  les fichiers dans le navigateur ; l'app Streamlit (Rapport mensuel) reste sur
  Streamlit Community Cloud comme aujourd'hui.
- « Se souvenir de moi » stocke la clé dérivée dans le navigateur de l'utilisateur
  (localStorage) — pas le mot de passe lui-même.

## Tester en local (optionnel)

```bash
cd docs && python3 -m http.server 8000
# puis ouvrir http://localhost:8000
```
Un fichier RHS synthétique (aucune donnée réelle) est fourni dans `tests/RHS_test.txt`.
