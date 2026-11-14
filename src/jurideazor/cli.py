"""Ligne de commande : python -m jurideazor <commande>

Chaîne de la semaine 1 :
  init-db        crée la base SQLite
  check-robots   affiche robots.txt des sources (à archiver dans docs/)
  download       télécharge les numéros de config/targets.yaml (rejouable)
  import-pdf     enregistre un PDF obtenu à la main / corpus de dépannage
  process        extraction + découpage + filtre de tous les numéros téléchargés
  stats          état de la base
  sample-filter  tire l'échantillon à annoter (eval/filter_sample.csv)
  eval-filter    calcule précision / rappel du filtre sur l'échantillon annoté
  llm-ping       un appel de test au modèle commun (mis en cache)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import ROOT, load_config
from .db import init_db


def main(argv=None):
    ap = argparse.ArgumentParser(prog="jurideazor")
    ap.add_argument("--config", help="chemin de config.yaml")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init-db")
    sub.add_parser("check-robots")
    d = sub.add_parser("download")
    d.add_argument("--targets", default=str(ROOT / "config" / "targets.yaml"))
    d.add_argument("--index-csv", help="index Upgrowth local (sinon : téléchargement, sinon motif d'URL)")
    d.add_argument("--no-sample", action="store_true", help="ne pas prendre l'échantillon récent")
    d.add_argument("--dry-run", action="store_true")
    ip = sub.add_parser("import-pdf")
    ip.add_argument("pdf")
    ip.add_argument("--year", type=int, required=True)
    ip.add_argument("--number", type=int, required=True)
    ip.add_argument("--edition", choices=["fr", "ar"], required=True)
    ip.add_argument("--url", help="lien source officiel (reconstruit si absent)")
    ip.add_argument("--origin", default="import_local")
    p = sub.add_parser("process")
    p.add_argument("--no-ocr", action="store_true")
    p.add_argument("--issue-id", type=int)
    sub.add_parser("stats")
    s = sub.add_parser("sample-filter")
    s.add_argument("--n", type=int, default=20)
    s.add_argument("--out", default=str(ROOT / "eval" / "filter_sample.csv"))
    e = sub.add_parser("eval-filter")
    e.add_argument("--csv", default=str(ROOT / "eval" / "filter_sample.csv"))
    e.add_argument("--review-as", choices=["keep", "reject"], default="keep")
    e.add_argument("--out", default=str(ROOT / "eval" / "filter_report.md"))
    sub.add_parser("llm-ping")
    a = ap.parse_args(argv)

    cfg = load_config(a.config)
    conn = init_db(cfg["paths"]["db"])

    if a.cmd == "init-db":
        print(f"Base prête : {cfg['paths']['db']}")

    elif a.cmd == "check-robots":
        import requests
        from .collect.download import RobotsGuard
        s = requests.Session()
        s.headers["User-Agent"] = cfg["project"]["user_agent"]
        g = RobotsGuard(s, cfg["project"]["user_agent"])
        for url in [cfg["collect"]["url_fr"].format(year=1990, num3="017"), cfg["collect"]["index_csv_url"]]:
            print(f"{url}\n  autorisé : {g.allowed(url)} | crawl-delay : {g.crawl_delay(url) or '-'}")
        for host, txt in g.report.items():
            print(f"\n===== {host}/robots.txt =====\n{txt}")

    elif a.cmd == "download":
        from .collect.index import issues_from_targets, load_index_csv
        index = None
        if a.index_csv:
            index = load_index_csv(a.index_csv)
        else:
            local = cfg["paths"]["data_dir"] / "joradp_index.csv"
            if not local.exists():
                try:
                    import requests
                    r = requests.get(cfg["collect"]["index_csv_url"], timeout=60,
                                     headers={"User-Agent": cfg["project"]["user_agent"]})
                    r.raise_for_status()
                    local.write_text(r.text, encoding="utf-8")
                    print(f"Index Upgrowth enregistré : {local}")
                except Exception as ex:  # noqa: BLE001
                    print(f"Index indisponible ({ex.__class__.__name__}) : URL reconstruites par motif.")
            if local.exists():
                index = load_index_csv(local)
        refs = issues_from_targets(cfg, Path(a.targets), index, include_sample=not a.no_sample)
        print(f"{len(refs)} PDF à traiter")
        from .collect.download import download_issues
        st = download_issues(conn, cfg, refs, dry_run=a.dry_run)
        print({k: v for k, v in st.items() if k != "robots"})

    elif a.cmd == "import-pdf":
        from .collect.download import import_local_pdf
        iid = import_local_pdf(conn, cfg, Path(a.pdf), a.year, a.number, a.edition, a.url, a.origin)
        print(f"importé : issue {iid}")

    elif a.cmd == "process":
        from .pipeline import process_issue
        q = "SELECT i.id, i.year, i.number, i.edition FROM issues i JOIN downloads d ON d.issue_id=i.id WHERE d.error IS NULL"
        args = ()
        if a.issue_id:
            q += " AND i.id=?"
            args = (a.issue_id,)
        for r in conn.execute(q, args).fetchall():
            c = process_issue(conn, cfg, r["id"], allow_ocr=not a.no_ocr)
            print(f"{r['edition'].upper()} {r['year']} n°{r['number']}: {c}")

    elif a.cmd == "stats":
        q = lambda sql: conn.execute(sql).fetchall()  # noqa: E731
        print("Numéros :", dict(q("SELECT edition, COUNT(*) FROM issues GROUP BY edition")))
        print("Téléchargés :", q("SELECT COUNT(*) FROM downloads WHERE error IS NULL")[0][0],
              "| échecs :", q("SELECT COUNT(*) FROM downloads WHERE error IS NOT NULL")[0][0])
        print("Pages OCR / total :", q("SELECT SUM(method='ocr'), COUNT(*) FROM pages")[0][:])
        print("Textes par décision :", dict(q("SELECT relevance, COUNT(*) FROM texts GROUP BY relevance")))
        print("Textes gardés par type :", dict(q(
            "SELECT text_type, COUNT(*) FROM texts WHERE relevance='keep' GROUP BY text_type")))
        for r in q("SELECT text_type, text_number, sign_date, lang, substr(title,1,90) t FROM texts "
                   "WHERE relevance='keep' AND text_type IN ('loi','ordonnance','decret_legislatif') ORDER BY sign_date"):
            print(f"  [{r['lang']}] {r['text_type']} {r['text_number']} ({r['sign_date']}) {r['t']}")

    elif a.cmd == "sample-filter":
        from .evaluate import sample_for_annotation
        n = sample_for_annotation(conn, Path(a.out), a.n)
        print(f"{n} textes à annoter dans {a.out} (colonne gold : keep / reject)")

    elif a.cmd == "eval-filter":
        from .evaluate import evaluate_filter, write_report
        res = evaluate_filter(conn, Path(a.csv), a.review_as)
        if res["n"] == 0:
            sys.exit("Aucune ligne annotée (colonne gold vide).")
        write_report(res, Path(a.out))
        print(f"n={res['n']} précision={res['precision']:.2f} rappel={res['recall']:.2f} "
              f"F1={res['f1']:.2f} -> {a.out}")

    elif a.cmd == "llm-ping":
        from .llm.client import LLMClient
        llm = LLMClient(cfg)
        print(llm.generate("Réponds en une phrase : quel est l'objet de la loi algérienne n° 90-11 ? "
                           "Si tu n'es pas sûr, dis-le."))
        print(llm.stats)


if __name__ == "__main__":
    main()
