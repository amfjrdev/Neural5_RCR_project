"""Semaine 2 - Base vectorielle : passages de tous les textes gardés + index FAISS.

1. Passages : articles de la loi 90-11 (data/articles/*.jsonl) + découpage des autres
   textes gardés par le filtre (relevance = keep) : par article quand c'est possible,
   sinon en fenêtres d'environ 1 000 caractères (chevauchement 150).
2. Embeddings multilingual-e5 (préfixe « passage: »), normalisés, enregistrés.
3. Index FAISS (produit scalaire = cosinus) enregistré sur disque, avec les métadonnées.
4. Contrôle : sur les questions-test, FAISS donne le même classement que le calcul direct.

Sorties : data/index/passages.jsonl, data/index/<modele>.npy, data/index/faiss.index,
          docs/preuves/index_s02.md
Usage : python scripts/build_index.py [--model intfloat/multilingual-e5-small]
"""
import os

# macOS : torch et faiss embarquent chacun OpenMP ; les charger ensemble peut provoquer un
# « segmentation fault ». On limite à 1 thread et on encode tout AVANT d'importer faiss.
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import argparse
import csv
import json
import re
import sqlite3

import numpy as np

from jurideazor.config import ROOT, load_config

ART = re.compile(r"(?m)^\W{0,3}(?:[AÂÃ]rt(?:icle|\.)?\s*(\d{1,3}(?:[- ]?\d{0,2})?(?:\s*bis)?)\s*[.,:]*\s*[-—–:]"
                 r"|[ء-ي]{1,5}دة\s*(\d{1,3}|الأولى|الاولى)\s*(?:مكرر)?\s*[:：])")


def windows(text, size=1000, overlap=150):
    out, i = [], 0
    while i < len(text):
        out.append(text[i:i + size])
        i += size - overlap
    return out


def chunk_text(body):
    body = re.sub(r"<<<PAGE \d+>>>", " ", body)
    marks = list(ART.finditer(body))
    pieces = []
    if len(marks) >= 2:
        if marks[0].start() > 200:
            pieces.append((None, body[:marks[0].start()]))  # visas / préambule
        for k, m in enumerate(marks):
            end = marks[k + 1].start() if k + 1 < len(marks) else len(body)
            pieces.append(((m.group(1) or m.group(2) or "").strip(), body[m.start():end]))
    else:
        pieces = [(None, body)]
    out = []
    for no, txt in pieces:
        txt = re.sub(r"\s+", " ", txt).strip()
        if len(txt) < 40:
            continue
        for w in (windows(txt) if len(txt) > 1500 else [txt]):
            out.append((no, w))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="intfloat/multilingual-e5-small")
    a = ap.parse_args()
    cfg = load_config()
    idx_dir = cfg["paths"]["data_dir"] / "index"
    idx_dir.mkdir(exist_ok=True)

    passages = []
    for f in sorted((cfg["paths"]["data_dir"] / "articles").glob("*.jsonl")):
        for l in open(f, encoding="utf-8"):
            d = json.loads(l)
            passages.append({"pid": d["id"], "text_ref": f"loi:{d['loi']}", "lang": d["lang"],
                             "article_no": d["article_no"], "date": d["valid_from"],
                             "source_url": d["source_url"], "norm_rank": 2, "content": d["content"]})
    split_refs = {p["text_ref"] for p in passages}
    conn = sqlite3.connect(cfg["paths"]["db"])
    rows = conn.execute("""SELECT t.id, t.lang, t.text_type, t.text_number, t.sign_date, t.source_url,
                                  t.norm_rank, t.is_circular, t.body
                           FROM texts t WHERE t.relevance = 'keep' ORDER BY t.id""").fetchall()
    n_texts = 0
    for tid, lang, ttype, tnum, date, url, rank, circ, body in rows:
        ref = f"{ttype}:{tnum or 'sans-numero-' + str(tid)}"
        if ref in split_refs:
            continue
        n_texts += 1
        for k, (no, txt) in enumerate(chunk_text(body)):
            passages.append({"pid": f"t{tid}:{k}", "text_ref": ref, "lang": lang, "article_no": no,
                             "date": date, "source_url": url, "norm_rank": rank,
                             "circulaire": bool(circ), "content": txt})
    with open(idx_dir / "passages.jsonl", "w", encoding="utf-8") as f:
        for p in passages:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    print(f"{len(passages)} passages ({len(split_refs)} loi découpée en articles + {n_texts} autres textes gardés)")

    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(a.model)
    tag = a.model.split("/")[-1]
    vec_path = idx_dir / f"{tag}.npy"
    D = model.encode(["passage: " + p["content"][:2000] for p in passages], normalize_embeddings=True,
                     batch_size=16, show_progress_bar=True).astype("float32")
    np.save(vec_path, D)
    qs = [q for q in csv.DictReader(open(ROOT / "eval/questions_test.csv", encoding="utf-8"))
          if q["hors_perimetre"] != "oui" and q["article_attendu"].strip()]
    Q = model.encode(["query: " + q["question"] for q in qs], normalize_embeddings=True).astype("float32")
    del model  # libère torch avant de charger faiss

    try:
        import faiss
        faiss.omp_set_num_threads(1)
        index = faiss.IndexFlatIP(D.shape[1])  # vecteurs normalisés : produit scalaire = cosinus
        index.add(D)
        faiss.write_index(index, str(idx_dir / "faiss.index"))
        backend = f"FAISS IndexFlatIP ({index.ntotal} vecteurs, dimension {D.shape[1]})"
    except ImportError:
        index, backend = None, "FAISS non installé : recherche exacte numpy (même résultat)"

    # Contrôle FAISS vs calcul direct, et rappel sur l'index complet
    direct = np.argsort(-(Q @ D.T), axis=1)[:, :5]
    same = "non testé"
    if index is not None:
        _, I = index.search(Q, 5)
        same = "identique" if (I == direct).all() else "différent"
    hits = 0
    lines = []
    for i, q in enumerate(qs):
        gold = {int(x) for x in re.findall(r"(?<![\d-])(\d{1,3})(?!\d)",
                                          q["article_attendu"].split("(")[0] if "version" in q["article_attendu"] else q["article_attendu"])}
        top = [passages[j] for j in direct[i]]
        ok = any(p["text_ref"] == "loi:90-11" and p["article_no"] and int(re.match(r"\d+", p["article_no"]).group()) in gold for p in top)
        hits += ok
        lines.append(f"| {q['id']} | {q['langue']} | {'oui' if ok else 'non'} | " +
                     " ; ".join(f"{p['text_ref']} art.{p['article_no'] or '-'} ({p['lang']})" for p in top[:3]) + " |")
    md = ["# Base vectorielle (semaine 2)\n",
          f"- Passages indexés : **{len(passages)}** (loi 90-11 article par article en FR et AR + {n_texts} autres textes gardés par le filtre, découpés par article ou en fenêtres de 1 000 caractères).",
          f"- Modèle : {a.model} (préfixes query: / passage:), vecteurs normalisés enregistrés dans data/index/{tag}.npy.",
          f"- Index : {backend} ; contrôle FAISS vs calcul direct sur les questions-test : **{same}**.",
          f"- Rappel@5 sur l'index complet (article attendu de la 90-11 dans les 5 premiers) : **{hits}/{len(qs)}**.\n",
          "| Question | Langue | Article attendu dans le top 5 | 3 premiers résultats |", "|---|---|---|---|"] + lines
    (ROOT / "docs/preuves/index_s02.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
