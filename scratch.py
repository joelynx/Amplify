import sqlite3
import json
from app.core.stats import subject_distribution, compute_stats, source_attribution
from app.ipc.api import Api

conn = sqlite3.connect("app/data/appdata/amplify.db")

api = Api(conn)
res = api.get_subject_distribution(mode="quiz")
print("quiz mode:", json.dumps(res, indent=2))

res = api.get_subject_distribution(mode="generate")
print("generate mode:", json.dumps(res, indent=2))

res = api.get_stats(mode="quiz")
print("stats quiz:", json.dumps(res, indent=2))
