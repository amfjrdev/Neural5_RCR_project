"""Semaine 3 — Graphe de connaissances (networkx) construit depuis la base SQLite.

À lancer APRÈS scripts/build_versions.py.
Nœuds : Texte, Article, Version, Concept. Arêtes : voir src/jurideazor/ontology.py et docs/ontologie.md.

Sorties :
  data/graph/graphe.graphml        (ouvrable dans Gephi / yEd)
  data/graph/graphe.json           (format node-link de networkx)
  docs/preuves/graphe_s03.md       (statistiques + requêtes d'exemple sur le graphe)
  docs/preuves/graphe_s03.html     (visualisation interactive des textes qui modifient la loi 90-11)
  docs/preuves/graphe_s03.png      (même vue, image ; seulement si matplotlib est installé)
Usage : python scripts/build_graph.py
"""
import json
import sqlite3
from collections import Counter

import networkx as nx
import yaml

from jurideazor.config import ROOT, load_config
from jurideazor.ontology import CONCEPTS, article_node, concepts_of, sort_key_article

LAW = "loi:90-11"


def build(conn) -> nx.MultiDiGraph:
    G = nx.MultiDiGraph()
    # ---- Textes du corpus (gardés par le filtre) + loi 90-11
    for tid, ttype, tnum, date, rank, title, url, circ in conn.execute(
            """SELECT id, text_type, text_number, sign_date, norm_rank, title, source_url, is_circular
               FROM texts WHERE (relevance='keep' AND lang='fr') OR (text_type='loi' AND text_number='90-11' AND lang='fr')"""):
        ref = f"{ttype}:{tnum}" if tnum else f"{ttype}:sans-numero-{tid}"
        G.add_node(ref, kind="Texte", type=ttype or "", numero=tnum or "", date=date or "", rang=rank or 0,
                   titre=(title or "")[:200], source_url=url, circulaire=bool(circ), dans_corpus=True, text_id=tid)
    ids = {d["text_id"]: n for n, d in G.nodes(data=True) if d.get("kind") == "Texte"}

    # ---- Articles et versions
    rows = conn.execute("""SELECT a.text_ref, a.article_no, v.id, v.lang, v.valid_from, v.valid_to, v.status,
                                  v.source_text_id, v.content
                           FROM articles a JOIN article_versions v ON v.article_id = a.id
                           ORDER BY a.text_ref, a.article_no, v.lang, v.valid_from""").fetchall()
    by_article = {}
    for ref, no, vid, lang, vfrom, vto, status, src, content in rows:
        if ref not in G:
            G.add_node(ref, kind="Texte", type=ref.split(":")[0], numero=ref.split(":")[1], dans_corpus=True)
        an = article_node(ref, no)
        if an not in G:
            G.add_node(an, kind="Article", texte=ref, numero=no)
            G.add_edge(ref, an, key="contient", rel="contient")
        vn = f"version:{vid}"
        G.add_node(vn, kind="Version", lang=lang, valid_from=vfrom or "", valid_to=vto or "", status=status,
                   extrait=(content or "")[:160])
        G.add_edge(an, vn, key="a_version", rel="a_version")
        if src in ids:
            G.add_edge(ids[src], vn, key="introduit", rel="introduit")
        by_article.setdefault((an, lang), []).append(vn)
        if status == "en_vigueur" or vto is None:
            for c in concepts_of(content or ""):
                G.add_edge(an, f"concept:{c}", key="traite_de", rel="traite_de")
    for (an, lang), vs in by_article.items():
        for a, b in zip(vs, vs[1:]):
            G.add_edge(a, b, key="remplacee_par", rel="remplacee_par")
    for key, c in CONCEPTS.items():
        G.add_node(f"concept:{key}", kind="Concept", label=c["label"])

    # ---- Relations entre textes (modifie / complete / abroge / vise)
    for src, rel, target_ref, target_art in conn.execute(
            "SELECT src_text_id, relation, target_text_ref, target_article FROM relations"):
        s = ids.get(src)
        if s is None:
            continue
        if target_art:
            tgt = article_node(target_ref, target_art)
            if tgt not in G:
                G.add_node(tgt, kind="Article", texte=target_ref, numero=target_art)
        else:
            tgt = target_ref
            if tgt not in G:  # texte cité dans un visa mais absent du corpus
                t, _, n = tgt.partition(":")
                G.add_node(tgt, kind="Texte", type=t, numero=n, dans_corpus=False)
        if s != tgt:
            G.add_edge(s, tgt, key=rel, rel=rel)

    # ---- Renvois : article abrogé -> article qui reprend la règle (data/amendements.yaml)
    conf = yaml.safe_load((ROOT / "data" / "amendements.yaml").read_text(encoding="utf-8"))
    for t in conf["textes"]:
        for old, new in (t.get("renvois") or {}).items():
            G.add_edge(article_node(LAW, old), article_node(t["ref"], new.replace("art. ", "")),
                       key="repris_dans", rel="repris_dans")
    return G


def export_html(G, path):
    """Vue interactive (vis-network) : textes qui modifient la 90-11 et articles touchés."""
    sub_edges = [(u, v, d["rel"]) for u, v, d in G.edges(data=True)
                 if d["rel"] in ("modifie", "complete", "abroge", "repris_dans")]
    nodes = {u for u, v, _ in sub_edges} | {v for u, v, _ in sub_edges}
    color = {"Texte": "#0f5e6e", "Article": "#e0a030"}
    ecol = {"modifie": "#c0392b", "complete": "#2c6e3f", "abroge": "#000000", "repris_dans": "#7d3c98"}
    vn = []
    for n in nodes:
        d = G.nodes[n]
        label = n.split("#")[-1] if d.get("kind") == "Article" else n
        if d.get("kind") == "Article" and not n.startswith(LAW):
            label = n.replace("#", " ")
        vn.append({"id": n, "label": label, "color": color.get(d.get("kind"), "#999"),
                   "shape": "box" if d.get("kind") == "Texte" else "ellipse",
                   "font": {"color": "#fff" if d.get("kind") == "Texte" else "#000"}})
    ve = [{"from": u, "to": v, "label": r, "color": ecol[r], "arrows": "to", "font": {"size": 9}} for u, v, r in sub_edges]
    html = f"""<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8"><title>Jurideazor – textes modifiant la loi 90-11</title>
<script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
<style>body{{font-family:sans-serif;margin:0}}#g{{width:100vw;height:92vh}}p{{margin:6px 12px}}</style></head>
<body><p><b>Graphe Jurideazor</b> : textes modificatifs (boîtes) → articles de la loi 90-11 (ellipses).
Rouge = modifie, vert = complète/crée, noir = abroge, violet = règle reprise dans.</p><div id="g"></div>
<script>new vis.Network(document.getElementById('g'),{{nodes:new vis.DataSet({json.dumps(vn, ensure_ascii=False)}),
edges:new vis.DataSet({json.dumps(ve, ensure_ascii=False)})}},{{physics:{{stabilization:true}}}});</script></body></html>"""
    path.write_text(html, encoding="utf-8")


def export_png(G, path):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return False
    H = nx.DiGraph()
    for u, v, d in G.edges(data=True):
        if d["rel"] in ("modifie", "complete", "abroge"):
            H.add_edge(u, v.split("#")[-1], rel=d["rel"])
    texts = [n for n in H if ":" in n]
    pos = nx.shell_layout(H, nlist=[texts, [n for n in H if n not in texts]])
    plt.figure(figsize=(14, 14))
    col = {"modifie": "#c0392b", "complete": "#2c6e3f", "abroge": "#000000"}
    nx.draw_networkx_nodes(H, pos, nodelist=texts, node_color="#0f5e6e", node_size=2600, node_shape="s")
    nx.draw_networkx_nodes(H, pos, nodelist=[n for n in H if n not in texts], node_color="#f3c46b", node_size=700)
    abbr = {"loi": "Loi", "ordonnance": "Ord.", "decret_legislatif": "D.L."}
    nx.draw_networkx_labels(H, pos, labels={n: f"{abbr.get(n.split(':')[0], '')} {n.split(':')[1]}" for n in texts},
                            font_color="white", font_size=9, font_weight="bold")
    nx.draw_networkx_labels(H, pos, labels={n: n.replace("art.", "") for n in H if n not in texts}, font_size=7)
    for r, c in col.items():
        nx.draw_networkx_edges(H, pos, edgelist=[(u, v) for u, v, d in H.edges(data=True) if d["rel"] == r],
                               edge_color=c, arrows=True, arrowsize=10, width=1.2, alpha=0.8)
    plt.title("Textes qui modifient la loi 90-11 (rouge = modifie, vert = complète/crée, noir = abroge)")
    plt.axis("off"); plt.tight_layout(); plt.savefig(path, dpi=110); plt.close()
    return True


def main():
    cfg = load_config()
    conn = sqlite3.connect(cfg["paths"]["db"])
    G = build(conn)
    out = cfg["paths"]["data_dir"] / "graph"
    out.mkdir(exist_ok=True)
    nx.write_graphml(G, out / "graphe.graphml")
    (out / "graphe.json").write_text(json.dumps(nx.node_link_data(G, edges="links"), ensure_ascii=False), encoding="utf-8")
    prev = ROOT / "docs" / "preuves"
    export_html(G, prev / "graphe_s03.html")
    png = export_png(G, prev / "graphe_s03.png")

    kinds = Counter(d.get("kind") for _, d in G.nodes(data=True))
    rels = Counter(d["rel"] for _, _, d in G.edges(data=True))
    modifiers = sorted({u for u, v, d in G.edges(data=True) if d["rel"] in ("modifie", "complete", "abroge") and v.startswith(LAW)})
    touched = Counter(v for u, v, d in G.edges(data=True) if d["rel"] in ("modifie", "complete", "abroge") and v.startswith(LAW))
    cited = Counter(v for u, v, d in G.edges(data=True) if d["rel"] == "vise")
    concept_arts = Counter(v for u, v, d in G.edges(data=True) if d["rel"] == "traite_de")

    def arts_of(concept):
        arts = sorted({u.split("#art.")[1] for u, v, d in G.in_edges(f"concept:{concept}", data=True)
                       if d["rel"] == "traite_de" and u.startswith(LAW)}, key=sort_key_article)
        return ", ".join(arts)

    md = ["# Semaine 3 : graphe de connaissances\n",
          "Construit par `python scripts/build_graph.py` depuis la base SQLite (après `build_versions.py`). "
          "Ontologie : `docs/ontologie.md`.\n",
          "## Taille du graphe\n", "| Type de nœud | Nombre |", "|---|---|",
          *[f"| {k} | {v} |" for k, v in sorted(kinds.items())], "",
          "| Type d'arête | Nombre |", "|---|---|", *[f"| {k} | {v} |" for k, v in sorted(rels.items())], "",
          "## Requêtes d'exemple sur le graphe\n",
          f"**1. Quels textes modifient, complètent ou abrogent la loi 90-11 ?** {', '.join(modifiers)}.\n",
          "**2. Articles de la loi 90-11 les plus touchés :** "
          + ", ".join(f"art. {a.split('#art.')[1]} ({n})" for a, n in touched.most_common(8)) + ".\n",
          "**3. Textes les plus cités dans les visas (« Vu … ») :** "
          + ", ".join(f"{t} ({n})" for t, n in cited.most_common(8)) + ".\n",
          f"**4. Articles de la 90-11 qui traitent du CDD :** {arts_of('cdd')}.\n",
          f"**5. Articles de la 90-11 qui traitent du licenciement :** {arts_of('licenciement')}.\n",
          "**6. Concepts les plus présents :** "
          + ", ".join(f"{CONCEPTS[c.split(':')[1]]['label']} ({n})" for c, n in concept_arts.most_common(6)) + ".\n",
          "**7. Chemin dans le graphe** (abrogation puis reprise de la règle) : "
          + " → ".join(nx.shortest_path(G, "ordonnance:97-03", article_node("ordonnance:97-03", "2"))) + " ; "
          + f"{article_node(LAW, '22')} → repris_dans → {article_node('ordonnance:97-03', '2')}.\n",
          "## Fichiers\n", "- `data/graph/graphe.graphml` (Gephi, yEd), `data/graph/graphe.json`",
          "- `docs/preuves/graphe_s03.html` : vue interactive (ouvrir dans un navigateur)",
          f"- `docs/preuves/graphe_s03.png` : {'vue statique' if png else 'non générée (pip install matplotlib)'}"]
    (prev / "graphe_s03.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
