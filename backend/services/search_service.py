import re

from qdrant import client, collection_name, embedding_model


def _tokens(text):
    return set(re.findall(r"[a-z0-9+#.]+", (text or "").lower()))


def _compact(text):
    return re.sub(r"[^a-z0-9+#.]+", "", (text or "").lower())


def _skill_phrases(skills):
    return [
        phrase.strip().lower()
        for phrase in (skills or "").split(",")
        if phrase.strip()
    ]


def _keyword_score(query_text, stored_skills):
    """Return a human-friendly keyword score for exact skill overlap."""
    query = (query_text or "").lower().strip()
    skills = (stored_skills or "").lower()

    if not query or not skills:
        return 0.0

    phrases = _skill_phrases(skills)
    query_tokens = _tokens(query)
    skill_tokens = _tokens(skills)
    compact_query = _compact(query)
    compact_skills = _compact(skills)

    if query in skills or (compact_query and compact_query in compact_skills):
        return 1.0

    if query_tokens:
        token_overlap = len(query_tokens & skill_tokens) / len(query_tokens)
    else:
        token_overlap = 0.0

    phrase_hits = 0
    for phrase in phrases:
        phrase_tokens = _tokens(phrase)
        if phrase and (phrase in query or phrase_tokens.issubset(query_tokens)):
            phrase_hits += 1

    phrase_overlap = phrase_hits / len(phrases) if phrases else 0.0
    return max(token_overlap, phrase_overlap)


def _scroll_candidate_points():
    points = []
    next_page_offset = None
    while True:
        batch, next_page_offset = client.scroll(
            collection_name=collection_name,
            limit=100,
            offset=next_page_offset,
            with_payload=True,
            with_vectors=False
        )
        points.extend(batch)
        if next_page_offset is None:
            break
    return points


def _build_match(point, vector_score, query, required_skill):
    stored_skills = point.payload.get("skills", "") or ""
    name = point.payload.get("name", "Unknown")
    keyword_score = _keyword_score(required_skill or query, stored_skills)
    combined_score = max(vector_score, keyword_score)

    print(
        f" - Candidate: {name} | Vector: {round(vector_score, 4)} "
        f"| Keyword: {round(keyword_score, 4)} | Skills: {stored_skills}"
    )

    if required_skill and keyword_score == 0 and vector_score < 0.35:
        print("   [FILTERED] No textual skill overlap and vector score is weak.")
        return None

    return {
        "id": str(point.id),
        "name": name,
        "resume_url": point.payload.get("resume_url", ""),
        "skills": stored_skills,
        "match_percentage": f"{max(0.0, min(100.0, round(combined_score * 100, 1)))}%",
        "score": round(combined_score, 4),
        "vector_score": round(vector_score, 4),
        "keyword_score": round(keyword_score, 4)
    }


def search_candidates(query_text, limit=20, threshold=0.01, required_skill=None):
    """Search candidate resume vectors and return normalized candidate matches."""
    query = (query_text or "").strip()
    if not query:
        print("[SEARCH] Empty query text provided. Returning empty list.")
        return []

    print(f"\n[SEARCH] Running semantic search query: '{query}' (limit={limit}, threshold={threshold})")
    
    query_embedding = embedding_model.encode(query).tolist()
    print(f"[SEARCH] Generated query vector of size: {len(query_embedding)}")

    point_scores = {}
    try:
        search_result = client.query_points(
            collection_name=collection_name,
            query=query_embedding,
            using="skills",
            limit=limit
        )
        print(f"[SEARCH] Qdrant search returned {len(search_result.points)} raw match points.")
        point_scores = {
            str(point.id): (point, point.score or 0)
            for point in search_result.points
        }
    except Exception as err:
        print(f"[SEARCH ERROR] Failed to query Qdrant collection '{collection_name}': {err}")
        print("[SEARCH] Falling back to Qdrant payload scan for exact/keyword matching.")

    try:
        for point in _scroll_candidate_points():
            keyword_score = _keyword_score(required_skill or query, point.payload.get("skills", ""))
            if keyword_score > 0:
                point_scores.setdefault(str(point.id), (point, 0.0))
    except Exception as err:
        print(f"[SEARCH ERROR] Payload scan failed for collection '{collection_name}': {err}")
        if not point_scores:
            raise err

    matches = []

    for point, vector_score in point_scores.values():
        match = _build_match(point, vector_score, query, required_skill)
        if not match:
            continue
        if match["score"] < threshold:
            print(f"   [FILTERED] Score {match['score']} is below threshold {threshold}")
            continue
        matches.append(match)

    matches.sort(key=lambda item: item["score"], reverse=True)
    matches = matches[:limit]
    print(f"[SEARCH SUCCESS] Found {len(matches)} finalized matches after threshold filtering.\n")
    return matches


def public_search_results(matches):
    """Remove internal scoring fields before returning matches to clients."""
    return [
        {
            key: value
            for key, value in match.items()
            if key not in {"score", "vector_score", "keyword_score"}
        }
        for match in matches
    ]
