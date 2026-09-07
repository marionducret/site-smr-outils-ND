/**
 * API du portail Outils SMR Ducret — Cloudflare Worker + KV.
 *
 * Stocke trois listes dans le KV (binding PORTAL) :
 *   heures     : relevé des interventions de Marion
 *   problemes  : signalements et leur état
 *   updates    : journal des mises à jour du portail
 *
 * Authentification : en-tête « X-Portal-Token ».
 * Le jeton est calculé DANS LE NAVIGATEUR à partir du mot de passe du portail
 * (SHA-256 de la clé PBKDF2 déjà utilisée pour déchiffrer les pages, avec un
 * suffixe de domaine). Le Worker ne connaît que les deux empreintes attendues,
 * stockées en variables secrètes :
 *   TOKEN_ADMIN  → Marion : lecture + écriture partout
 *   TOKEN_USER   → Nathalie : lecture + création d'un signalement uniquement
 *
 * Aucune donnée patient ne transite ici : uniquement du suivi d'activité.
 */

const ORIGINES_AUTORISEES = [
  "https://outils-smr-ducret.pages.dev",
  "http://localhost:8000",
];

const CLES = ["heures", "problemes", "updates"];
const MOIS_RE = /^\d{4}-\d{2}$/;

/* ---------- utilitaires ---------- */

function cors(origin) {
  const ok = ORIGINES_AUTORISEES.includes(origin) ? origin : ORIGINES_AUTORISEES[0];
  return {
    "Access-Control-Allow-Origin": ok,
    "Access-Control-Allow-Methods": "GET, POST, PATCH, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, X-Portal-Token",
    "Access-Control-Max-Age": "86400",
    "Vary": "Origin",
  };
}

function json(data, status, origin) {
  return new Response(JSON.stringify(data), {
    status: status || 200,
    headers: { "Content-Type": "application/json; charset=utf-8", ...cors(origin) },
  });
}

/** Comparaison à temps constant (évite de renseigner un attaquant par le timing). */
function memeJeton(a, b) {
  if (typeof a !== "string" || typeof b !== "string" || a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

function role(request, env) {
  const jeton = request.headers.get("X-Portal-Token") || "";
  if (env.TOKEN_ADMIN && memeJeton(jeton, env.TOKEN_ADMIN)) return "admin";
  if (env.TOKEN_USER && memeJeton(jeton, env.TOKEN_USER)) return "user";
  return null;
}

async function lire(env, cle) {
  const brut = await env.PORTAL.get(cle);
  if (!brut) return [];
  try { const v = JSON.parse(brut); return Array.isArray(v) ? v : []; } catch { return []; }
}

/** Facturation : un état par MOIS (Marion ne facture pas heure par heure). */
async function lireFacturation(env) {
  const brut = await env.PORTAL.get("facturation");
  if (!brut) return {};
  try {
    const v = JSON.parse(brut);
    return v && typeof v === "object" && !Array.isArray(v) ? v : {};
  } catch { return {}; }
}

async function ecrire(env, cle, liste) {
  await env.PORTAL.put(cle, JSON.stringify(liste));
}

function identifiant() {
  return Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 8);
}

/** Ne garde que des chaînes courtes : pas de charge utile surprise dans le KV. */
function texte(v, max) {
  if (v === undefined || v === null) return "";
  return String(v).slice(0, max || 400);
}

/* ---------- routes ---------- */

export default {
  async fetch(request, env) {
    const origin = request.headers.get("Origin") || "";
    const url = new URL(request.url);
    const chemin = url.pathname.replace(/\/+$/, "") || "/";

    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: cors(origin) });
    }
    if (!env.PORTAL) {
      return json({ erreur: "KV non configuré (binding PORTAL manquant)" }, 500, origin);
    }

    const r = role(request, env);
    if (!r) return json({ erreur: "Jeton absent ou invalide" }, 401, origin);

    const admin = r === "admin";
    const corps = ["POST", "PATCH", "PUT"].includes(request.method)
      ? await request.json().catch(() => ({}))
      : {};

    /* --- état complet (les deux rôles) --- */
    if (chemin === "/state" && request.method === "GET") {
      const [heures, problemes, updates] = await Promise.all(CLES.map(c => lire(env, c)));
      const facturation = await lireFacturation(env);
      return json({ role: r, heures, problemes, updates, facturation }, 200, origin);
    }

    /* --- facturation d'un mois entier (AAAA-MM) --- */
    if (chemin.startsWith("/facturation/") && request.method === "PATCH") {
      if (!admin) return json({ erreur: "Réservé à l'administratrice" }, 403, origin);
      const mois = chemin.slice("/facturation/".length);
      if (!MOIS_RE.test(mois)) return json({ erreur: "Mois attendu au format AAAA-MM" }, 400, origin);
      const facturation = await lireFacturation(env);
      if (corps.etat === "facture") {
        facturation[mois] = "facture";
      } else {
        delete facturation[mois];
      }
      await env.PORTAL.put("facturation", JSON.stringify(facturation));
      return json({ ok: true, facturation }, 200, origin);
    }

    /* --- signalements --- */
    if (chemin === "/problemes" && request.method === "POST") {
      // Nathalie peut créer un signalement ; elle ne peut pas en changer l'état.
      const liste = await lire(env, "problemes");
      const ticket = {
        id: identifiant(),
        cree_le: new Date().toISOString(),
        auteur: admin ? "Marion" : "Nathalie",
        outil: texte(corps.outil, 120),
        type: texte(corps.type, 120),
        urgence: texte(corps.urgence, 60),
        description: texte(corps.description, 4000),
        fichiers: texte(corps.fichiers, 400),
        etat: "a_traiter",
        note: "",
        maj_le: new Date().toISOString(),
      };
      liste.unshift(ticket);
      await ecrire(env, "problemes", liste.slice(0, 500));
      return json({ ok: true, ticket }, 201, origin);
    }

    if (chemin.startsWith("/problemes/") && ["PATCH", "DELETE"].includes(request.method)) {
      if (!admin) return json({ erreur: "Réservé à l'administratrice" }, 403, origin);
      const id = chemin.slice("/problemes/".length);
      const liste = await lire(env, "problemes");
      const i = liste.findIndex(p => p.id === id);
      if (i === -1) return json({ erreur: "Signalement introuvable" }, 404, origin);
      if (request.method === "DELETE") {
        liste.splice(i, 1);
      } else {
        const etats = ["a_traiter", "en_cours", "resolu", "sans_suite"];
        if (corps.etat && etats.includes(corps.etat)) liste[i].etat = corps.etat;
        if (corps.note !== undefined) liste[i].note = texte(corps.note, 2000);
        liste[i].maj_le = new Date().toISOString();
      }
      await ecrire(env, "problemes", liste);
      return json({ ok: true, problemes: liste }, 200, origin);
    }

    /* --- heures --- */
    if (chemin === "/heures" && request.method === "POST") {
      if (!admin) return json({ erreur: "Réservé à l'administratrice" }, 403, origin);
      const liste = await lire(env, "heures");
      liste.unshift({
        id: identifiant(),
        date: texte(corps.date, 20),
        perimetre: texte(corps.perimetre, 120),
        objet: texte(corps.objet, 600),
        duree: Math.max(0, Math.min(1000, Number(corps.duree) || 0)),
      });
      await ecrire(env, "heures", liste.slice(0, 2000));
      return json({ ok: true, heures: liste }, 201, origin);
    }

    if (chemin.startsWith("/heures/") && ["PATCH", "DELETE"].includes(request.method)) {
      if (!admin) return json({ erreur: "Réservé à l'administratrice" }, 403, origin);
      const id = chemin.slice("/heures/".length);
      const liste = await lire(env, "heures");
      const i = liste.findIndex(h => h.id === id);
      if (i === -1) return json({ erreur: "Ligne introuvable" }, 404, origin);
      if (request.method === "DELETE") {
        liste.splice(i, 1);
      } else {
        if (corps.date !== undefined) liste[i].date = texte(corps.date, 20);
        if (corps.perimetre !== undefined) liste[i].perimetre = texte(corps.perimetre, 120);
        if (corps.objet !== undefined) liste[i].objet = texte(corps.objet, 600);
        if (corps.duree !== undefined) liste[i].duree = Math.max(0, Math.min(1000, Number(corps.duree) || 0));
      }
      await ecrire(env, "heures", liste);
      return json({ ok: true, heures: liste }, 200, origin);
    }

    /* --- journal des mises à jour --- */
    if (chemin === "/updates" && request.method === "POST") {
      if (!admin) return json({ erreur: "Réservé à l'administratrice" }, 403, origin);
      const liste = await lire(env, "updates");
      liste.unshift({
        id: identifiant(),
        date: texte(corps.date, 20) || new Date().toISOString().slice(0, 10),
        perimetre: texte(corps.perimetre, 120),
        texte: texte(corps.texte, 2000),
      });
      await ecrire(env, "updates", liste.slice(0, 500));
      return json({ ok: true, updates: liste }, 201, origin);
    }

    if (chemin.startsWith("/updates/") && request.method === "DELETE") {
      if (!admin) return json({ erreur: "Réservé à l'administratrice" }, 403, origin);
      const id = chemin.slice("/updates/".length);
      const liste = await lire(env, "updates");
      const i = liste.findIndex(u => u.id === id);
      if (i === -1) return json({ erreur: "Entrée introuvable" }, 404, origin);
      liste.splice(i, 1);
      await ecrire(env, "updates", liste);
      return json({ ok: true, updates: liste }, 200, origin);
    }

    return json({ erreur: "Route inconnue", chemin, methode: request.method }, 404, origin);
  },
};
