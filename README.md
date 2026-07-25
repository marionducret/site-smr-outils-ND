# Portail des outils SOLIMED

Site statique qui regroupe tous les outils SOLIMED pour les médecins DIM :
**Rapport mensuel** (app Streamlit), **Analyse GME**, **Convertisseur RHS → ENC**,
**Comparaison recettes**, **Analyse live dépendances**, **Filtre dépendances** et
**CSAR Thesaurus**, avec tutoriels intégrés. Protégé par un mot de passe partagé. Fonctionne sur Mac
et Windows, dans le navigateur, sans rien installer. 100 % gratuit.

## Structure

```
├── src/                  ← pages sources (repo privé : versionnées sur GitHub)
│   ├── index.html        ← accueil + tutoriels
│   ├── rapport.html      ← intégration de l'app Streamlit
│   ├── gme.html          ← outil Analyse GME (copie d'Evolution_GME.html + lien retour portail)
│   ├── rhs.html          ← convertisseur RHS → ENC (Python dans le navigateur via Pyodide)
│   ├── recettes.html     ← comparaison recettes (comparaison_recettes.py porté web)
│   ├── analyse-dep.html  ← analyse live dépendances (rhs_analyse_live.py porté web)
│   ├── filtre-dep.html   ← filtre dépendances (rhs_filtre_dependance.py porté web)
│   ├── csar.html         ← CSAR Thesaurus (CSAR_excel_tool.py porté web)
│   └── assets/           ← logo + wheels Python (xlsxwriter, openpyxl, et_xmlfile)
│       └── csar2026/     ← référentiels CSAR 2026 (attendus, descr, fichier ATIH, inter_noms)
├── docs/                 ← version CHIFFRÉE publiée sur GitHub Pages (générée par build.py)
├── build.py              ← chiffre src/ → docs/ (AES-256-GCM, PBKDF2 600k itérations)
├── gate_template.html    ← écran de saisie du mot de passe
├── .password             ← mot de passe actuel (JAMAIS sur GitHub)
├── .salt                 ← sel de dérivation (JAMAIS sur GitHub)
└── tests/                ← RHS synthétique + générateur, pour tester sans données réelles
```

## Hébergement actuel

- Repo GitHub **privé** : `marionducret/site-solimed` (sources `src/` versionnées,
  `.password` et `.salt` exclus par `.gitignore`).
- Déploiement : **Netlify**, branché sur le repo, dossier de publication `docs`.
  Chaque `git push` redéploie automatiquement (~30 s).

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

## Mettre à jour les référentiels CSAR

L'outil CSAR Thesaurus embarque les 4 référentiels 2026 dans
`src/assets/csar2026/`. Quand l'ATIH publie une nouvelle version :
remplacer les fichiers dans ce dossier (mêmes noms), rebuilder, pousser.
Si les noms de fichiers changent (ex. CSAR_2027_…), les adapter aussi dans
`src/csar.html` (bloc `extraSetup` + `_ns["FICHIERS"]`).

## Outils « 100 % local » : comment ça marche

- Le code Python de chaque outil est embarqué **tel quel** dans sa page
  (`rhs.html` ← app_txt_rhs/main.py ; `recettes.html` ← comparaison_recettes.py ;
  `analyse-dep.html` ← rhs_analyse_live.py ; `filtre-dep.html` ← rhs_filtre_dependance.py ;
  `csar.html` ← CSAR_excel_tool.py) et exécuté dans le navigateur par
  [Pyodide](https://pyodide.org) (Python compilé en WebAssembly, chargé depuis le
  CDN jsdelivr au premier usage, ~15–25 Mo, mis en cache).
- Les wheels `xlsxwriter`, `openpyxl` et `et_xmlfile` sont auto-hébergées dans
  `src/assets/` (pas de dépendance PyPI).
- **Aucune donnée patient ne quitte le poste du médecin** : lecture, conversion et
  écriture de l'Excel se font entièrement en local dans l'onglet du navigateur.
- Sortie strictement identique à l'outil Python d'origine (vérifié octet par octet
  sur le RHS synthétique de `tests/`).
- Si un script Python évolue : recopier son contenu dans la page correspondante
  entre les balises `<script type="text/x-python" id="main-py">` et `</script>`,
  rebuilder, pousser (ou me demander de le faire).

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
Des données de test synthétiques (aucune donnée réelle) sont fournies dans `tests/` :
`RHS_test.txt` (convertisseur RHS), `RHS_synthetique.xlsx` (analyse/filtre dépendances),
`600000001.2026.MM.SMR.VisualValoSejours.csv` (comparaison recettes) et
`600000001.2026.12.ano-rha-sha.t1d2csarr.zip` (CSAR Thesaurus).
