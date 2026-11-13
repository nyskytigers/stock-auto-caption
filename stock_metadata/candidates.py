"""Evidence-bound keyword candidates for human review; never quota padding."""
from .core import clean_keywords


def keyword_candidates(model_keywords, confirmed_visible_terms=()):
    """Keep provenance and flag new terms as proposals, never auto-approved exports.

    Terms must come from an existing model proposal or explicitly confirmed visual
    evidence. No category expansion, thesaurus stuffing, minimum count or CLIP.
    """
    candidates = []
    positions = {}
    for source, terms in (("model", model_keywords), ("human_confirmed_visible_term", confirmed_visible_terms)):
        for term in clean_keywords(terms):
            key = term.casefold()
            if key in positions:
                candidates[positions[key]]["sources"].append(source)
            else:
                positions[key] = len(candidates)
                candidates.append({"keyword": term, "sources": [source], "review_required": True})
    return candidates
