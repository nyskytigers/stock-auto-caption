# Optional CLIP relevance extension (design only)

Default behavior remains BLIP plus KeyBERT or supplied metadata. No CLIP package,
weights or network request is required or added to normal installation.

Proposed interface: rank(image, candidate_keywords) -> ordered list of
{keyword, similarity, original_index}. Inject this scorer into a future processing
options object, disabled by default. Keep the original candidate set and a stable
original-order tie break. Reorder only; never manufacture keywords, infer identities
or use scores to prove locations, dates or licensing. Do not impose a universal
similarity threshold: scores vary by model, domain and prompt.

An optional open_clip adapter could encode one RGB image and prompts such as
"a photo of {keyword}" under inference mode, L2 normalize embeddings and compute
cosine similarities. Batch text encodings, cap device memory, offer CPU and allow
offline local weight paths. Make cache location and downloads explicit. Store no
images in a shared cache. Weight licenses must be reviewed separately from code.

Failure behavior: report that scoring failed, retain original keywords, and never
block baseline export. Maintain an audit of proposed order and let users override it.
Tests should inject a deterministic fake scorer for ordering, ties, unavailable
backend, nonfinite scores and recovery. A separately opted-in model smoke test
must verify real image/text embeddings. Evaluate relevance on manually labeled
tattoo/illustration/photo sets before choosing any production threshold.
