import re

STOP_WORDS = {
    "là", "gì", "của", "và", "có", "cho", "trong",
    "thế", "nào", "hãy", "giải", "thích", "về",
}

def tokenize(text):
    words = re.findall(r"\w+", text.lower())
    return [word for word in words if word not in STOP_WORDS]

def retrieve_chunks(question, chunks, top_k=3):
    question_words = set(tokenize(question))
    results = []
    for chunk in chunks:
        chunk_words = tokenize(chunk["text"])
        score = sum(1 for word in question_words if word in chunk_words)
        if score > 0:
            results.append({
                "page": chunk["page"],
                "text": chunk["text"],
                "score": score,
            })
    results.sort(key=lambda result: result["score"], reverse=True)
    return results[:top_k]