import sqlite3

conn = sqlite3.connect("app/data/appdata/amplify.db")

try:
    # Find all Traverse quizzes
    traverse_ids = [row[0] for row in conn.execute("SELECT quiz_id FROM quizzes WHERE template_name = 'TRAVERSE'")]
    for qid in traverse_ids:
        # keep only the first question
        conn.execute("DELETE FROM quiz_questions WHERE quiz_id = ? AND question_order > 1", (qid,))
        
        # update n_questions
        c = conn.execute("SELECT COUNT(*) FROM quiz_questions WHERE quiz_id = ?", (qid,)).fetchone()[0]
        conn.execute("UPDATE quizzes SET n_questions = ? WHERE quiz_id = ?", (c, qid))

    conn.commit()
    print("Fixed Traverse quizzes!")
except Exception as e:
    conn.rollback()
    print("Error:", e)
