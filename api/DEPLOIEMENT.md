# Brancher les pages Admin sur une base Cloudflare

Le portail est un site statique : à lui seul il ne peut rien mémoriser. Pour que
Nathalie voie ce que Marion remplit, les heures, les signalements et le journal
des mises à jour vivent dans un petit service Cloudflare (un « Worker » et une
base clé-valeur « KV »), sur le même compte gratuit que Cloudflare Pages.

Tout se fait dans le tableau de bord — **aucune ligne de commande**.

---

## 1. Choisir le mot de passe administratrice

Dans le dossier du projet, créer un fichier `.password_admin` contenant le
mot de passe **de Marion** (différent de celui du site, qui reste celui de
Nathalie et ne change pas) :

```bash
printf 'MonMotDePasseAdmin' > .password_admin
```

`.password_admin` et `.cek` sont déjà exclus par `.gitignore` : ils ne partent
jamais sur GitHub.

Puis rebuilder pour obtenir les deux jetons :

```bash
python3 build.py
```

La fin du build affiche :

```
  TOKEN_USER  = …
  TOKEN_ADMIN = …
```

Garder cette fenêtre ouverte : ces deux valeurs sont à coller à l'étape 4.
(Elles se recalculent à l'identique à chaque build tant que les mots de passe
et le sel ne changent pas.)

---

## 2. Créer la base KV

1. Aller sur <https://dash.cloudflare.com> → **Storage & Databases** → **KV**.
2. **Create a namespace**, le nommer `outils-smr-portal`, valider.

---

## 3. Créer le Worker

1. **Compute (Workers)** → **Create** → **Start with Hello World!** → nommer le
   Worker `outils-smr-api` → **Deploy**.
2. Une fois créé : **Edit code**, tout sélectionner dans l'éditeur, supprimer,
   et coller l'intégralité du fichier `api/worker.js` du projet. **Deploy**.
3. Onglet **Settings** → **Bindings** → **Add** → **KV namespace** :
   - Variable name : `PORTAL`  *(exactement ce nom)*
   - KV namespace : `outils-smr-portal`
   - **Deploy**.

---

## 4. Déclarer les deux jetons

**Settings** → **Variables and Secrets** → **Add** (deux fois), en choisissant
le type **Secret** :

| Nom           | Valeur                                   |
|---------------|------------------------------------------|
| `TOKEN_USER`  | la valeur `TOKEN_USER` affichée au build  |
| `TOKEN_ADMIN` | la valeur `TOKEN_ADMIN` affichée au build |

**Deploy** pour appliquer.

---

## 5. Relier le site au Worker

1. Copier l'URL du Worker (en haut de sa page, du type
   `https://outils-smr-api.<votre-compte>.workers.dev`).
2. La coller dans `api/url.txt` (une seule ligne, sans espace).
3. Vérifier que cette même URL figure dans `ORIGINES_AUTORISEES` **côté site** :
   dans `api/worker.js`, la liste doit contenir l'adresse du **portail**
   (`https://outils-smr-ducret.pages.dev`) — pas celle du Worker. Si le site
   déménage un jour, c'est là qu'il faut l'ajouter.
4. Rebuilder et pousser :

```bash
python3 build.py
git add -A && git commit -m "branche les pages Admin sur l'API" && git push
```

---

## 6. Vérifier

- Ouvrir le site avec le **mot de passe de Marion** : les pages Heures et Suivi
  affichent « 🔑 Mode administratrice » et les formulaires de saisie.
- Ouvrir avec le **mot de passe de Nathalie** (par exemple dans une fenêtre de
  navigation privée) : « 👁 Lecture seule », pas de formulaire, mais le relevé
  et les états sont visibles, et le formulaire de signalement fonctionne.

---

## Ce qui protège quoi

- Le **mot de passe** ouvre le site (les pages sont chiffrées) et détermine le
  profil affiché.
- Le **jeton** envoyé au Worker est dérivé de ce mot de passe mais n'est pas la
  clé de déchiffrement : Cloudflare ne peut pas lire le contenu du site avec.
- Les droits ne dépendent **pas** de l'interface : même en modifiant la page
  dans son navigateur, un profil utilisateur reçoit un refus du Worker (403)
  sur toute écriture autre que la création d'un signalement.
- Aucune donnée patient ne transite par cette API : uniquement du suivi
  d'activité (dates, durées, descriptions de problèmes).

## Coût

Plan gratuit Cloudflare : 100 000 requêtes de Worker par jour et 1 000 écritures
KV par jour. À deux utilisatrices, l'usage réel se compte en dizaines de
requêtes par jour.
