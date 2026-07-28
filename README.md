# Portail des outils Outils SMR Ducret

Site statique qui regroupe tous les outils Outils SMR Ducret pour les médecins DIM :
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
├── docs/                 ← version CHIFFRÉE publiée sur Cloudflare Pages (générée par build.py)
├── build.py              ← chiffre src/ → docs/ (AES-256-GCM, PBKDF2 600k itérations)
│                           + injecte nav.html dans chaque page (lien actif automatique)
├── nav.html              ← barre de navigation UNIQUE du site (injectée au build)
├── footer.html           ← pied de page UNIQUE (mention d'usage restreint, injecté au build)
├── gate_template.html    ← écran de saisie du mot de passe
├── .password             ← mot de passe actuel (JAMAIS sur GitHub)
├── .salt                 ← sel de dérivation (JAMAIS sur GitHub)
└── tests/                ← RHS synthétique + générateur, pour tester sans données réelles
```

## Hébergement actuel

- Repo GitHub **privé** : `marionducret/site-solimed` (sources `src/` versionnées,
  `.password` et `.salt` exclus par `.gitignore`).
- Déploiement : **Cloudflare Pages**, projet `outils-smr-ducret`, branché sur le
  repo, dossier de publication `docs` (build command vide). Chaque `git push`
  redéploie automatiquement (~1 min).
- URL du site : **https://outils-smr-ducret.pages.dev**
- Plan gratuit Cloudflare : 500 builds/mois, bande passante et visites illimitées
  pour un site statique — pas de système de crédits (contrairement à Netlify,
  abandonné pour cette raison en juillet 2026).

## Modifier la barre de navigation (menu en haut de page)

La nav n'est plus dupliquée dans chaque page : elle vit dans **`nav.html`** à la
racine. Au build, `build.py` remplace le bloc `<nav>…</nav>` de chaque page de
`src/` par le contenu de `nav.html`, et pose automatiquement la classe
`active` sur le lien de la page courante. Dans les pages de `src/`, le bloc
`<nav>` ne contient plus qu'un commentaire — ne rien y écrire.

Pour changer un libellé, ajouter ou retirer un lien :

1. Éditer `nav.html` (uniquement ce fichier).
2. Rebuilder et pousser :
   ```bash
   python3 build.py
   git add -A && git commit -m "maj navigation" && git push
   ```

Cas particulier : `gme.html` n'a pas de barre de navigation (c'est l'outil
autonome Evolution_GME avec son propre en-tête et son bouton flottant
« retour portail ») — le build le laisse tel quel.

## Modifier le pied de page (mention d'usage restreint)

Même principe que la nav : le footer vit dans **`footer.html`** à la racine et
est injecté au build juste avant `</body>` de **chaque** page, y compris
`gme.html` (la mention figure donc aussi dans les copies enregistrées via
« Enregistrer une copie » — mais pas dans l'export « version client », qui
utilise son propre template). Il porte la mention :

> Outils développés pour l'usage professionnel strict du Dr Nathalie DUCRET,
> médecin DIM. Toute utilisation par une autre personne ou structure est interdite.

Pour changer le texte : éditer `footer.html` uniquement, rebuilder, pousser.

## Rebuild automatique au commit (hook git)

Un hook `pre-commit` (fichier `.git/hooks/pre-commit`, local à ce Mac) lance
automatiquement `python3 build.py` et ajoute `docs/` au commit dès que le
commit touche `src/`, `nav.html`, `footer.html`, `gate_template.html` ou
`build.py`. Concrètement : modifier une page dans `src/`, commiter + pousser
dans VS Code, et c'est en ligne ~1 min après — plus besoin de penser au build.
Si `build.py` échoue, le commit est annulé (rien n'est publié à moitié).

⚠️ Les hooks ne sont pas versionnés par git : sur un nouveau clone ou un autre
ordinateur, recréer `.git/hooks/pre-commit` (ou relancer `build.py` à la main).

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
