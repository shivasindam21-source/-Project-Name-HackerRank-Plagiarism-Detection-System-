from pymongo import MongoClient
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

# DB
client = MongoClient("mongodb://localhost:27017/")
db = client["Contests"]
col = db["codes"]

docs = list(col.find({}, {
    "teamname": 1,
    "copiedfrom": 1,
    "lang": 1,
    "code": 1
}))

THRESHOLD = 0.5

def normalize_code(code, lang):
    code = code.lower()

    if lang.lower() == "python" or lang.lower() == "py":
        code = re.sub(r'#.*', '', code)
    else:
        code = re.sub(r'//.*', '', code)
        code = re.sub(r'/\*[\s\S]*?\*/', '', code)

    code = re.sub(r'\s+', '', code)
    return code

# loop by language
for lang in set(d["lang"] for d in docs):
    lang_docs = [d for d in docs if d["lang"] == lang]

    if len(lang_docs) < 2:
        continue

    codes = [normalize_code(d["code"], lang) for d in lang_docs]

    vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(3, 5))
    tfidf = vectorizer.fit_transform(codes)
    sim_matrix = cosine_similarity(tfidf)

    for i in range(len(lang_docs)):
        for j in range(i + 1, len(lang_docs)):
            if sim_matrix[i][j] >= THRESHOLD:
                # update copiedfrom instead of copied_from
                col.update_one(
                    {"_id": lang_docs[j]["_id"]},
                    {"$set": {"copiedfrom": lang_docs[i]["teamname"]}}
                )

print("Done")
