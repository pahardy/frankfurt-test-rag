"""
scrape.py — Fetch texts from the web and save them as .txt files in texts/.

Three entry formats are supported in the TEXTS dict:

    "name": "https://..."
        Single page — fetches one URL and saves it. (existing behaviour)

    "name": {"index": "https://..."}
        Multi-page (auto) — fetches the index URL, discovers all chapter links
        in the same directory, then fetches and concatenates them in order.

    "name": {"pages": ["https://...", "https://...", ...]}
        Multi-page (explicit) — fetches each URL in the given order and
        concatenates them. Use when auto-discovery picks up the wrong links.

Run once, then re-run ingest.py to embed the new texts.
Usage: uv run scrape.py
"""

import config
import os
import time
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urljoin, urlparse

TEXTS_DIR = Path("texts")
CERT = os.getenv("SSL_CERT_FILE")

TEXTS = {
    # -------------------------------------------------------------------------
    # Sigmund Freud — public domain translations from Project Gutenberg
    # -------------------------------------------------------------------------

    # Civilization and Its Discontents (1930, Riviere trans.) — the single most
    # cited Freud text in Critical Theory: repression, instinct, and social order.
    "freud_civilization_and_its_discontents":
        "https://www.gutenberg.org/cache/epub/78221/pg78221-images.html",

    # Beyond the Pleasure Principle (1920) — introduces Eros and Thanatos
    # (life/death drives); the theoretical foundation of Marcuse's Eros and Civilization.
    "freud_beyond_the_pleasure_principle":
        "https://www.gutenberg.org/cache/epub/76031/pg76031-images.html",

    # Group Psychology and the Analysis of the Ego (1921, Strachey trans. 1922) —
    # drives Adorno and Horkheimer's work on mass psychology and authoritarianism.
    "freud_group_psychology_and_analysis_of_ego":
        "https://www.gutenberg.org/cache/epub/35877/pg35877-images.html",

    # Totem and Taboo (1913, Brill trans.) — applies psychoanalysis to culture
    # and social origins; directly engaged in Dialectic of Enlightenment.
    "freud_totem_and_taboo":
        "https://www.gutenberg.org/cache/epub/41214/pg41214-images.html",

    # Three Contributions to the Theory of Sex (1905, Brill trans.) — foundational
    # theory of drives, sexuality, and repression underlying Frankfurt School critique.
    "freud_three_essays_theory_of_sexuality":
        "https://www.gutenberg.org/cache/epub/14969/pg14969-images.html",

    # The Future of an Illusion (1927) — Freud's critique of religion and ideology;
    # resonates directly with Frankfurt School's critique of culture and false consciousness.
    "freud_future_of_an_illusion":
        "https://www.gutenberg.org/cache/epub/76774/pg76774-images.html",

    # -------------------------------------------------------------------------
    # Karl Marx
    # -------------------------------------------------------------------------

    # Economic and Philosophic Manuscripts of 1844 — Marx's most Hegelian work;
    # develops alienation, estranged labour, and species-being. Direct bridge
    # from Hegel to the Frankfurt School.
    "marx_economic_philosophic_manuscripts_1844": {
        "pages": [
            "https://www.marxists.org/archive/marx/works/1844/manuscripts/preface.htm",
            "https://www.marxists.org/archive/marx/works/1844/manuscripts/wages.htm",
            "https://www.marxists.org/archive/marx/works/1844/manuscripts/capital.htm",
            "https://www.marxists.org/archive/marx/works/1844/manuscripts/rent.htm",
            "https://www.marxists.org/archive/marx/works/1844/manuscripts/labour.htm",
            "https://www.marxists.org/archive/marx/works/1844/manuscripts/second.htm",
            "https://www.marxists.org/archive/marx/works/1844/manuscripts/third.htm",
            "https://www.marxists.org/archive/marx/works/1844/manuscripts/comm.htm",
            "https://www.marxists.org/archive/marx/works/1844/manuscripts/needs.htm",
            "https://www.marxists.org/archive/marx/works/1844/manuscripts/power.htm",
            "https://www.marxists.org/archive/marx/works/1844/manuscripts/hegel.htm",
        ]
    },

    # Theses on Feuerbach (1845) — eleven short theses, foundational for
    # materialist philosophy: "Philosophers have only interpreted the world..."
    "marx_theses_on_feuerbach":
        "https://www.marxists.org/archive/marx/works/1845/theses/theses.htm",

    # The German Ideology (1845, with Engels) — on ideology, base/superstructure,
    # historical materialism, and consciousness.
    "marx_german_ideology": {
        "index": "https://www.marxists.org/archive/marx/works/1845/german-ideology/index.htm"
    },

    # The Communist Manifesto (1848, with Engels).
    "marx_communist_manifesto": {
        "index": "https://www.marxists.org/archive/marx/works/1848/communist-manifesto/index.htm"
    },

    # Grundrisse (1857-58) — Marx's philosophical notebooks; more relevant
    # to critical theory than Capital. Covers money, capital, labour,
    # alienation, and the Fragment on Machines.
    "marx_grundrisse": {
        "index": "https://www.marxists.org/archive/marx/works/1857/grundrisse/index.htm"
    },

    # Capital, Volume 1 (1867) — especially Part 1 (commodities, fetishism)
    # which Lukács's reification theory directly builds on.
    "marx_capital_vol1": {
        "index": "https://www.marxists.org/archive/marx/works/1867-c1/index.htm"
    },

    # -------------------------------------------------------------------------
    # Walter Benjamin
    # -------------------------------------------------------------------------
    "benjamin_on_the_concept_of_history":
        "https://www.marxists.org/reference/archive/benjamin/1940/history.htm",
    "benjamin_author_as_producer":
        "https://www.marxists.org/reference/archive/benjamin/1970/author-producer.htm",
    "benjamin_work_of_art":
        "https://www.marxists.org/reference/subject/philosophy/works/ge/benjamin.htm",

    # -------------------------------------------------------------------------
    # Max Horkheimer
    # -------------------------------------------------------------------------
    "horkheimer_present_situation_of_social_philosophy":
        "https://www.marxists.org/reference/archive/horkheimer/1931/present-situation.htm",
    "horkheimer_social_function_of_philosophy":
        "https://www.marxists.org/reference/archive/horkheimer/1939/social-function.htm",
    "horkheimer_theism_and_atheism":
        "https://www.marxists.org/reference/archive/horkheimer/1963/theism-atheism.htm",
    "horkheimer_feudal_lord_customer_specialist":
        "https://www.marxists.org/reference/archive/horkheimer/1964/customer.htm",

    # -------------------------------------------------------------------------
    # Theodor Adorno
    # -------------------------------------------------------------------------
    "adorno_culture_industry":
        "https://www.marxists.org/reference/archive/adorno/1944/culture-industry.htm",
    "adorno_late_capitalism_or_industrial_society":
        "https://www.marxists.org/reference/archive/adorno/1968/late-capitalism.htm",

    # -------------------------------------------------------------------------
    # Herbert Marcuse
    # -------------------------------------------------------------------------
    "marcuse_socialist_humanism":
        "https://www.marxists.org/reference/archive/marcuse/works/1965/socialist-humanism.htm",
    "marcuse_aggressiveness_in_advanced_industrial_society":
        "https://www.marxists.org/reference/archive/marcuse/works/aggressiveness.htm",
    "marcuse_end_of_utopia":
        "https://www.marxists.org/reference/archive/marcuse/works/1967/end-utopia.htm",
    "marcuse_problem_of_violence":
        "https://www.marxists.org/reference/archive/marcuse/works/1967/violence.htm",
    "marcuse_essay_on_liberation":
        "https://www.marxists.org/reference/archive/marcuse/works/1969/essay-liberation.htm",

    # -------------------------------------------------------------------------
    # Jürgen Habermas
    # -------------------------------------------------------------------------
    "habermas_knowledge_and_human_interests":
        "https://www.marxists.org/reference/archive/habermas/1968/theory-knowledge.htm",
    "habermas_communicative_ethics":
        "https://www.marxists.org/reference/archive/habermas/1998/communicative-ethics.htm",

    # -------------------------------------------------------------------------
    # Georg Lukács
    # -------------------------------------------------------------------------
    "lukacs_what_is_orthodox_marxism":
        "https://www.marxists.org/archive/lukacs/works/history/orthodox.htm",
    "lukacs_class_consciousness":
        "https://www.marxists.org/archive/lukacs/works/history/lukacs3.htm",
    "lukacs_phenomenon_of_reification":
        "https://www.marxists.org/archive/lukacs/works/history/hcc05.htm",
    "lukacs_antinomies_of_bourgeois_thought":
        "https://www.marxists.org/archive/lukacs/works/history/lukacs1.htm",

    # -------------------------------------------------------------------------
    # Classical Hermetic texts
    # -------------------------------------------------------------------------

    # The Corpus Hermeticum — the central collection of Hermetic tractates.
    # This is the 1650 Everard translation ("The Divine Pymander"), the earliest
    # English version, reprinted widely and fully public domain.
    "corpus_hermeticum_divine_pymander": {
        "index": "https://sacred-texts.com/eso/pym/index.htm"
    },

    # The Virgin of the World — covers the Asclepius, the Stobaean fragments,
    # and other Hermetic material not in the Corpus. Kingsford/Maitland 1885.
    "hermetic_virgin_of_the_world_and_asclepius": {
        "index": "https://sacred-texts.com/eso/vow/index.htm"
    },

    # Mead's Thrice-Greatest Hermes (1906) — the definitive scholarly edition.
    # Three volumes: Vol 1 is introductory essays, Vols 2–3 contain translations
    # with commentary. All valuable as secondary scholarly material.
    "mead_thrice_greatest_hermes_vol1": {
        "index": "https://sacred-texts.com/gno/th1/index.htm"
    },
    "mead_thrice_greatest_hermes_vol2": {
        "index": "https://sacred-texts.com/gno/th2/index.htm"
    },
    "mead_thrice_greatest_hermes_vol3": {
        "index": "https://sacred-texts.com/gno/th3/index.htm"
    },

    # The Emerald Tablet — the founding text of the alchemical tradition.
    # Short but foundational: "As above, so below."
    "emerald_tablet":
        "https://sacred-texts.com/alc/emerald.htm",

    # The Golden Tractate of Hermes Trismegistus — a key alchemical-Hermetic text.
    "golden_tractate_of_hermes":
        "https://sacred-texts.com/alc/goldtrac.htm",

    # -------------------------------------------------------------------------
    # Paracelsus — alchemical-philosophical treatises (Waite trans., 1894)
    # Four short texts from sacred-texts.com/alc/, all single pages.
    # -------------------------------------------------------------------------
    "paracelsus_coelum_philosophorum":
        "https://sacred-texts.com/alc/coelum.htm",
    "paracelsus_tincture_of_philosophers":
        "https://sacred-texts.com/alc/paracel2.htm",
    "paracelsus_treasure_of_treasures":
        "https://sacred-texts.com/alc/paracel1.htm",
    "paracelsus_aurora_of_philosophers":
        "https://sacred-texts.com/alc/paracel3.htm",

    # "Of the Nature of Things" (nine books) by Paracelsus — his most
    # philosophical work, including a full book on the Doctrine of Signatures.
    # Bundled in this Gutenberg volume with "A New Light of Alchymie" by
    # Michael Sendivogius (1566–1636), a major figure in the same tradition.
    # Both are relevant; the RAG treats the file as a single source.
    "paracelsus_nature_of_things_and_sendivogius":
        "https://www.gutenberg.org/cache/epub/61112/pg61112-images.html",

    # -------------------------------------------------------------------------
    # Jakob Böhme — two primary texts from sacred-texts.com/eso/
    # -------------------------------------------------------------------------

    # The Signature of All Things (Signatura Rerum, 1621) — his most important
    # philosophical work: the doctrine that the inner essence of every thing is
    # legible in its outward form. Directly influenced Hegel and Schelling.
    "boehme_signature_of_all_things": {
        "index": "https://sacred-texts.com/eso/sat/index.htm"
    },

    # The Confessions of Jacob Boehme (ed. Palmer, 1920) — a well-selected
    # anthology from across his works, with an introduction by Evelyn Underhill.
    # A good entry point into his broader system.
    "boehme_confessions": {
        "index": "https://sacred-texts.com/eso/cjb/index.htm"
    },

    # -------------------------------------------------------------------------
    # Renaissance Hermetic texts — the Rosicrucian Manifestos (1614–1616)
    # The three founding documents of the Rosicrucian movement, preserved in
    # Waite's "Real History of the Rosicrucians" (1887).
    # -------------------------------------------------------------------------
    "rosicrucian_fama_fraternitatis":
        "https://sacred-texts.com/sro/rhr/rhr06.htm",
    "rosicrucian_confessio_fraternitatis":
        "https://sacred-texts.com/sro/rhr/rhr07.htm",
    "rosicrucian_chemical_wedding": {
        "pages": [
            "https://sacred-texts.com/sro/rhr/rhr08.htm",  # intro
            "https://sacred-texts.com/sro/rhr/rhr09.htm",  # first day
            "https://sacred-texts.com/sro/rhr/rhr10.htm",  # second day
            "https://sacred-texts.com/sro/rhr/rhr11.htm",  # third day
            "https://sacred-texts.com/sro/rhr/rhr12.htm",  # fourth day
            "https://sacred-texts.com/sro/rhr/rhr13.htm",  # fifth day
            "https://sacred-texts.com/sro/rhr/rhr14.htm",  # sixth day
            "https://sacred-texts.com/sro/rhr/rhr15.htm",  # seventh day
        ]
    },

    # -------------------------------------------------------------------------
    # G.W.F. Hegel — fragments available on marxists.org
    # The Shorter Logic and Philosophical Propaedeutic are multi-page works;
    # the others are single pages (prefaces and selected chapters).
    # -------------------------------------------------------------------------
    "hegel_phenomenology_preface_and_master_slave": {
        "pages": [
            "https://www.marxists.org/reference/archive/hegel/works/ph/phprefac.htm",
            "https://www.marxists.org/reference/archive/hegel/works/ph/phba.htm",
        ]
    },
    "hegel_philosophy_of_right_preface_and_introduction": {
        "pages": [
            "https://www.marxists.org/reference/archive/hegel/works/pr/preface.htm",
            "https://www.marxists.org/reference/archive/hegel/works/pr/printrod.htm",
        ]
    },
    "hegel_philosophy_of_history_introduction":
        "https://www.marxists.org/reference/archive/hegel/works/hi/introduction.htm",
    "hegel_history_of_philosophy_introduction":
        "https://www.marxists.org/reference/archive/hegel/works/hp/hpintroduction.htm",
    "hegel_shorter_logic": {
        "index": "https://www.marxists.org/reference/archive/hegel/works/sl/slconten.htm"
    },
    "hegel_philosophical_propaedeutic": {
        "index": "https://www.marxists.org/reference/archive/hegel/works/pp/index.htm"
    },

    # -------------------------------------------------------------------------
    # Hegel — full works (public domain translations)
    # -------------------------------------------------------------------------

    # Philosophy of History (full) — J. Sibree trans., 1857. Hosted on
    # marxists.org (educational/non-commercial use). The main lecture content
    # lives in lectures1-4.htm (linked from lectures.htm, not the index),
    # so explicit pages are required.
    "hegel_philosophy_of_history_full": {
        "pages": [
            "https://www.marxists.org/reference/archive/hegel/works/hi/preface-lectures.htm",
            "https://www.marxists.org/reference/archive/hegel/works/hi/introduction-lectures.htm",
            "https://www.marxists.org/reference/archive/hegel/works/hi/lectures1.htm",  # Oriental World
            "https://www.marxists.org/reference/archive/hegel/works/hi/lectures2.htm",  # Greek World
            "https://www.marxists.org/reference/archive/hegel/works/hi/lectures3.htm",  # Roman World
            "https://www.marxists.org/reference/archive/hegel/works/hi/lectures4.htm",  # German World
        ]
    },

    # Philosophy of Mind (Encyclopedia Part 3) — William Wallace trans., 1894.
    # Same translator as the Shorter Logic already in the database.
    # Full text as a single HTML page on Project Gutenberg.
    "hegel_philosophy_of_mind_wallace":
        "https://www.gutenberg.org/cache/epub/39064/pg39064-images.html",
}


def fetch_text(url: str) -> str:
    """Fetch a single page and return its body as clean plain text."""
    response = requests.get(url, timeout=30, verify=CERT)
    response.raise_for_status()

    # Decode as Latin-1 — every byte maps to a valid character, so this never
    # fails. Old sites like sacred-texts.com use Latin-1 (or plain ASCII), and
    # UTF-8 auto-detection often misfires on pages with binary artifacts.
    html = response.content.decode("latin-1")
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup.find_all(["nav", "header", "footer", "script", "style"]):
        tag.decompose()

    body = soup.find("body") or soup
    text = body.get_text(separator="\n")

    lines = [line.strip() for line in text.splitlines()]
    return "\n\n".join(" ".join(chunk) for chunk in _group_lines(lines) if chunk)


def fetch_chapter_urls(index_url: str) -> list[str]:
    """
    Fetch an index page and return the URLs of chapter pages linked from it.
    Only returns links that share the same directory as the index URL,
    avoiding navigation links that point elsewhere on the site.
    """
    response = requests.get(index_url, timeout=30, verify=CERT)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "html.parser")
    parsed_index = urlparse(index_url)
    base_dir = parsed_index.path.rsplit("/", 1)[0] + "/"

    seen, urls = set(), []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith("#") or href.startswith("mailto:"):
            continue
        if any(href.endswith(ext) for ext in (".pdf", ".epub", ".gz", ".zip", ".txt", ".jpg", ".jpeg", ".png", ".gif")):
            continue

        full_url = urljoin(index_url, href).split("#")[0]
        parsed = urlparse(full_url)

        if parsed.netloc != parsed_index.netloc:
            continue
        if not parsed.path.startswith(base_dir):
            continue
        if full_url == index_url or full_url in seen:
            continue

        seen.add(full_url)
        urls.append(full_url)

    return urls


def fetch_multipage_text(entry: dict) -> tuple[str, int]:
    """
    Fetch and concatenate text from multiple pages.
    Returns the combined text and the number of pages fetched.
    """
    if "pages" in entry:
        urls = entry["pages"]
        print(f"    {len(urls)} pages (explicit)")
    elif "index" in entry:
        urls = fetch_chapter_urls(entry["index"])
        if not urls:
            raise ValueError(f"No chapter links found at: {entry['index']}")
        print(f"    {len(urls)} pages discovered from index")
    else:
        raise ValueError(f"Entry must have 'pages' or 'index' key: {entry}")

    parts = []
    for url in urls:
        parts.append(fetch_text(url))
        time.sleep(0.5)

    return "\n\n".join(parts), len(urls)


def _group_lines(lines: list[str]) -> list[list[str]]:
    """Group non-empty lines into paragraphs separated by blank lines."""
    groups, current = [], []
    for line in lines:
        if line:
            current.append(line)
        elif current:
            groups.append(current)
            current = []
    if current:
        groups.append(current)
    return groups


def scrape():
    TEXTS_DIR.mkdir(exist_ok=True)
    skipped, saved, failed = [], [], []

    for name, entry in TEXTS.items():
        path = TEXTS_DIR / f"{name}.txt"
        if path.exists():
            skipped.append(name)
            print(f"  skip   {name}")
            continue

        print(f"  fetch  {name}")
        try:
            if isinstance(entry, str):
                text = fetch_text(entry)
            else:
                text, _ = fetch_multipage_text(entry)

            path.write_text(text, encoding="utf-8")
            saved.append(name)
            print(f"         saved  {len(text.split()):,} words")
        except Exception as e:
            failed.append((name, str(e)))
            print(f"         ERROR  {e}")

        time.sleep(1)

    print(f"\nDone — {len(saved)} saved, {len(skipped)} skipped, {len(failed)} failed.")
    if failed:
        for name, err in failed:
            print(f"  {name}: {err}")


if __name__ == "__main__":
    scrape()
