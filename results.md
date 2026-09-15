# Week 4 Practical — Task Set D (Insurance Claims): Results

## 1. Golden set (12 real adjuster questions, known-correct chunk_id)

Full machine-readable version: [golden_set.jsonl](golden_set.jsonl). Corpus: 3 editions of Form HO-0304 (Homeowners Special Form), 1 edition of the unrelated Form HO-0500 (decoy), two endorsements (HO-2306, HO-2405), and a real health-insurance claim form (New India Assurance) for corpus diversity — 110 chunks total, ingested via the app's own `/upload` endpoint (RecursiveCharacterTextSplitter, `all-MiniLM-L6-v2` embeddings, Pinecone).

| # | Question | Correct chunk_id | Hard token? |
|---|---|---|---|
| 1 | Under HO-0304 edition 01-22, does exclusion E-17 exclude water backup caused by heavy rainfall or a blocked municipal sewer line? | `HO-0304_ed-01-22.pdf-a42439a2-9` | ✅ E-17 / ed-01-22 |
| 2 | Under HO-0304 edition 02-23, is water backup through sewers or drains excluded under E-17 even if caused by mechanical or electrical failure of the sump pump itself? | `HO-0304_ed-02-23.pdf-2fb79e28-9` | ✅ E-17 / ed-02-23 |
| 3 | Does exclusion E-17 apply under form HO-0304 edition 03-24 to a sudden and accidental discharge of water from a household appliance? | `HO-0304_ed-03-24.pdf-54f590cb-9` | ✅ E-17 / ed-03-24 |
| 4 | What form number and edition date appear in the Declarations of the March 2024 homeowners special policy? | `HO-0304_ed-03-24.pdf-dc71e7da-0` | ✅ form/edition |
| 5 | Under Form HO-0500, what does exclusion F-3 say about water that backs up through sewers or drains? | `HO-0500_ed-01-23.pdf-08768ab3-3` | ✅ F-3 (decoy form) |
| 6 | What does Endorsement HO-2306 do, and to which editions of HO-0304 does it attach? | `Endorsement_HO-2306.pdf-e3b74437-0` | ✅ endorsement # |
| 7 | What is the per-occurrence Basic Limit of liability under Endorsement HO-2306? | `Endorsement_HO-2306.pdf-b423be67-1` | ✅ endorsement # |
| 8 | Can Endorsement HO-2405 be attached to a HO-0304 edition 01-22 policy? | `Endorsement_HO-2405.pdf-a9e6adde-3` | ✅ endorsement # |
| 9 | Is loss caused by flood or surface water covered under Coverage A of the HO-0304 homeowners special form? | `HO-0304_ed-01-22.pdf-3b560bf4-4` | plausible/easy |
| 10 | Is mold hidden within the walls that results from a covered plumbing leak covered under HO-0304 edition 01-22, and if so up to what amount? | `HO-0304_ed-01-22.pdf-3d30e7a3-7` | plausible/easy |
| 11 | What is the Coverage D Loss of Use limit shown in the Declarations for HO-0304 edition 01-22? | `HO-0304_ed-01-22.pdf-86901098-0` | plausible/easy |
| 12 | According to the claim documents checklist, is the Pre-authorization approval letter required to be submitted with a claim? | `Claim_Form.pdf-7047e058-37` | plausible/easy |

8 of 12 questions carry an exact exclusion/form/endorsement token (required minimum: 4).

## 2. Baseline hit-rate@3 (before any change)

**6 / 12 = 50.00%**  |  p50 latency: **320.92 ms**

| Q | Hit@3? | Correct chunk's actual rank (out of dense top-5 / top-25) |
|---|---|---|
| 1 | ❌ | rank 5 / 5 |
| 2 | ❌ | rank 5 / 5 |
| 3 | ❌ | not in top-5, **rank 21/25** |
| 4 | ✅ | rank 1 |
| 5 | ✅ | rank 1 |
| 6 | ✅ | rank 2 |
| 7 | ❌ | not in top-5, **rank 7/25** |
| 8 | ✅ | rank 2 |
| 9 | ❌ | not in top-5 (see evidence below — duplicate content elsewhere) |
| 10 | ✅ | rank 3 |
| 11 | ✅ | rank 2 |
| 12 | ❌ | not in top-5, **rank 8/25** |

## 3. R / G / Not-In-Corpus tally

**R: 6  |  G: 0  |  Not-In-Corpus: 0**

All 6 misses are labeled **R** — determined by actually opening the inspection view (`eval_full_answers.py` output) and confirming that on every one of the 6 *hits*, the LLM's generated answer was correct and fully grounded (no G-failures found: a hit at top-3 never produced a wrong final answer in this run).

| Q | Label | Evidence |
|---|---|---|
| 1 | R | Correct chunk (`...a42439a2-9`) scored 0.6201, ranked 5th — outscored by two `Endorsement_HO-2306.pdf` chunks (0.68, 0.64) whose "water backs up through sewers... sump pump" language is nearly identical to E-17's own wording. |
| 2 | R | Correct chunk scored 0.6819, ranked 5th, edged out by ed-01-22's own E-17 chunk (0.6822) — the biencoder can't tell the two editions' near-duplicate E-17 text apart. |
| 3 | R | Correct chunk (the *revised* E-17 in ed-03-24) didn't even make the dense top-5; it ranked **21st of 25**. Top-5 were dominated by `Endorsement_HO-2405.pdf` and `Endorsement_HO-2306.pdf` chunks and ed-01-22's *old* E-17 text — exactly the "three fluent, semantically-adjacent water-damage clauses, none of them right" failure the assignment describes. |
| 7 | R | Correct chunk (the one with "$5,000... Basic Limit") never appeared in top-5 (rank 7/25); the LLM correctly said "I don't know" rather than hallucinate a number — safe failure, but still a retrieval miss. |
| 9 | R (benign) | The E-3 flood clause text is byte-identical across all three HO-0304 editions. Retrieval grabbed the *ed-03-24* copy instead of the golden-tagged *ed-01-22* copy, so hit-rate@3 recorded a miss even though the LLM's answer was still correct (duplicate-content artifact of the golden set, not an actual retrieval failure an adjuster would notice). |
| 12 | R | Correct checklist chunk (with "Copy of the Pre-authorization approval letter") ranked 8th/25; the LLM instead saw a different, plausible-looking checklist section from Part A and confidently answered **"No"** — which is factually wrong (the source document does list it). This is a genuine, adjuster-visible wrong-answer failure. |

No G-failures and no Not-In-Corpus failures were found — every correct chunk existed in the index; the problem was purely retrieval ranking.

## 4. The one change, and why

**Change made: cross-encoder rerank (`cross-encoder/ms-marco-MiniLM-L-6-v2`) over the top-25 dense candidates**, replacing the flat top-K dense query. Not BM25+RRF.

Justification, from the tally directly: BM25+RRF fixes the case where the correct chunk is **missing from the dense candidate pool entirely** (lexical retrieval catches an exact code the embedding model ignores). That's not what the tally showed — every single R-failure's correct chunk was already sitting inside the dense top-25 (ranks 5, 5, 21, 7, 8). The failure mode here is a **ranking** problem: the biencoder can't fine-distinguish near-duplicate water-backup language across three form editions and two endorsements. A cross-encoder jointly scores (query, chunk) pairs and is specifically good at exactly this kind of fine-grained, high-lexical-overlap disambiguation — so it's the correctly-targeted fix for what the evidence actually showed, not a default reach for "add BM25 because the brief mentions exact codes."

Only one change was made — no BM25 was added alongside it — so the delta below is attributable to this change alone.

## 5. Before → after

| Metric | Before | After | Δ |
|---|---|---|---|
| hit-rate@3 | 6/12 (50.00%) | 8/12 (66.67%) | **+16.67 pp** |
| p50 latency / query | 320.92 ms | 880.54 ms | **+559.62 ms (~2.7×)** |

(Cold-start model-load outliers on Q1 in both runs were correctly excluded by using the median.)

## 6. Per-question fixed / unfixed / still-broken

| Q | Before | After | Status |
|---|---|---|---|
| 1 | ❌ miss | ❌ miss | **Still broken** |
| 2 | ❌ miss | ❌ miss | **Still broken** |
| 3 | ❌ miss | ❌ miss | **Still broken** |
| 4 | ✅ hit | ✅ hit | unaffected |
| 5 | ✅ hit | ✅ hit | unaffected |
| 6 | ✅ hit | ✅ hit | unaffected |
| 7 | ❌ miss | ✅ hit | **Fixed** |
| 8 | ✅ hit | ✅ hit | unaffected |
| 9 | ❌ miss | ❌ miss | **Still broken** (duplicate-content artifact, see §3) |
| 10 | ✅ hit | ✅ hit | unaffected |
| 11 | ✅ hit | ✅ hit | unaffected |
| 12 | ❌ miss | ✅ hit | **Fixed** — answer flipped from a wrong "No" to the correct "Yes" |

**Which R-failures the change fixed:** Q7 and Q12 — both had the correct chunk within dense top-25 at a moderate depth (rank 7 and 8), close enough for the cross-encoder to promote into top-3.

**Which R-failures it did NOT touch:** Q1 and Q2 — the correct chunk was already close (rank 5) but a competing near-duplicate chunk from a *different document* (`Endorsement_HO-2306.pdf`) still out-scored it even after rerank; the cross-encoder reduces but doesn't eliminate confusion between textually-similar E-17 clauses across editions/endorsements. Q3 — rank 21/25 was too deep for reranking alone to fully recover in this run. Q9 is not a real fix target (duplicate-content artifact, not a retrieval defect).

## 7. Shipping decision

**Ship it, with a caveat.** hit-rate@3 improved by a meaningful +16.67 points (50%→66.67%) on a golden set deliberately loaded with hard exact-token questions, and it fixed one *adjuster-visible wrong answer* (Q12 flipped from a confidently wrong "No" to the correct "Yes") at a real but tolerable cost — p50 latency going from ~320ms to ~880ms is still well within interactive range for a claims-lookup tool that isn't latency-critical the way autocomplete is.

The caveat: reranking did **not** fix the specific failure named in the assignment's own motivating scenario — the E-17-under-ed-03-24 question (Q3) is still wrong, because dense retrieval ranked the correct chunk 21st of 25, too deep even for a cross-encoder to reliably recover. If a second change were budgeted, the next candidate would be BM25+RRF fusion specifically to pull exact-token matches (E-17, form/edition strings) higher into the dense-adjacent candidate pool before reranking — but that is a second change and out of scope for this task's "exactly one change" constraint. As shipped, this fix is real progress, not a full fix, and should be labeled as such rather than oversold.

## 8. Code diff (exactly one retrieval change)

```diff
diff --git a/app/retrieval.py b/app/retrieval.py
index 15586a2..a5db79c 100644
--- a/app/retrieval.py
+++ b/app/retrieval.py
@@ -1,4 +1,8 @@
+from dataclasses import dataclass
+from functools import lru_cache
+
 from groq import Groq
+from sentence_transformers import CrossEncoder
 
 from app.config import GROQ_API_KEY, GROQ_MODEL, TOP_K
 from app.embeddings import embed_query
@@ -12,14 +16,47 @@ SYSTEM_PROMPT = (
     "Never use outside knowledge and never guess."
 )
 
+# Retrieval change (Week 4 Task Set D): dense retrieval alone was ranking the
+# correct chunk outside the top-3 in every observed failure, while it was
+# still present somewhere in the wider dense candidate pool. A cross-encoder
+# reranker jointly scores (query, chunk) pairs and reorders that pool, which
+# fixes ranking mistakes without needing a second (lexical) retrieval path.
+RERANK_CANDIDATE_POOL = 25
+RERANKER_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"
+
 _groq_client = Groq(api_key=GROQ_API_KEY)
 
 
+@dataclass
+class RankedMatch:
+    id: str
+    score: float
+    metadata: dict
+
+
+@lru_cache(maxsize=1)
+def get_reranker() -> CrossEncoder:
+    return CrossEncoder(RERANKER_MODEL_NAME)
+
+
 def search(query: str, top_k: int = TOP_K):
     vector = embed_query(query)
     index = get_index()
-    response = index.query(vector=vector, top_k=top_k, include_metadata=True)
-    return response.matches
+    response = index.query(vector=vector, top_k=RERANK_CANDIDATE_POOL, include_metadata=True)
+    candidates = response.matches
+    if not candidates:
+        return []
+
+    reranker = get_reranker()
+    pairs = [(query, (c.metadata or {}).get("text", "")) for c in candidates]
+    rerank_scores = reranker.predict(pairs)
+
+    reranked = sorted(zip(candidates, rerank_scores), key=lambda pair: pair[1], reverse=True)
+
+    return [
+        RankedMatch(id=c.id, score=float(score), metadata=c.metadata)
+        for c, score in reranked[:top_k]
+    ]
```

## Submission checklist

- [x] `golden_set.jsonl` — 12 real adjuster questions with known-correct chunk_id
- [x] Baseline hit-rate@3 (50.00%), written down before any change
- [x] R/G/Not-In-Corpus tally with one line of evidence per failure (§3)
- [x] Before → after hit-rate@3 and p50 latency, in one table (§5)
- [x] Per-question fixed/unfixed table (§6)
- [x] Code diff showing exactly one retrieval change (§8)
