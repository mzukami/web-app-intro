from fastapi import FastAPI, Response, Depends, HTTPException, status, Body, Query
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from typing import List, Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
import sqlite3
import os
import uvicorn
from datetime import datetime, timedelta

app = FastAPI()

# ==== パス・DB ====
BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "data.db")

# ==== モデル ====
class DataBase(BaseModel):
    id: Optional[int] = None
    value_1: str
    value_2: Optional[str] = None

class Answer(BaseModel):
    id: Optional[int]
    question_id: int
    user_id: int
    content: str
    created_at: Optional[str]
    likes: int = Field(default=0)  # いいね数

class QuestionWithAnswers(DataBase):
    answers: List[Answer] = []
    likes: int = Field(default=0)  # いいね数

class UserProfileUpdate(BaseModel):
    profile: str

# ==== セキュリティ設定 ====
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# ==== DB接続・初期化 ====
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # dataテーブル（質問）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            value_1 TEXT NOT NULL,
            value_2 TEXT
        )
    """)

    # usersテーブル
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            profile TEXT DEFAULT '',
            is_admin INTEGER DEFAULT 0
        )
    """)

    # answersテーブル
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(question_id) REFERENCES data(id)
        )
    """)

    # ratingsテーブル（いいね・評価）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            target_type TEXT NOT NULL,
            target_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, target_type, target_id)
        )
    """)

    conn.commit()
    conn.close()

# ==== パスワード処理 ====
def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# ==== JWT トークン発行・認証 ====
def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="認証に失敗しました",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    if user is None:
        raise credentials_exception
    return user

def get_admin_user(current_user: dict = Depends(get_current_user)):
    if current_user["is_admin"] != 1:
        raise HTTPException(status_code=403, detail="管理者権限が必要です")
    return current_user

# ==== エンドポイント ====

# 質問一覧（回答なし）
@app.get("/data", response_model=List[DataBase])
def read_data_items():
    conn = get_db_connection()
    items = conn.execute("SELECT * FROM data").fetchall()
    conn.close()
    return [DataBase(**dict(item)) for item in items]

# 質問一覧（回答つき、いいね数つき）
@app.get("/data_with_answers", response_model=List[QuestionWithAnswers])
def read_data_items_with_answers():
    conn = get_db_connection()
    questions = conn.execute("SELECT * FROM data").fetchall()
    results = []
    for q in questions:
        answers = conn.execute("SELECT * FROM answers WHERE question_id = ?", (q["id"],)).fetchall()
        ans_objs = []
        for a in answers:
            like_count = conn.execute(
                "SELECT COUNT(*) FROM ratings WHERE target_type='answer' AND target_id=?", (a["id"],)
            ).fetchone()[0]
            ans_objs.append(Answer(**dict(a), likes=like_count))
        q_like_count = conn.execute(
            "SELECT COUNT(*) FROM ratings WHERE target_type='question' AND target_id=?", (q["id"],)
        ).fetchone()[0]
        results.append(
            QuestionWithAnswers(
                id=q["id"], value_1=q["value_1"], value_2=q["value_2"], answers=ans_objs, likes=q_like_count
            )
        )
    conn.close()
    return results

# 質問投稿（ログイン必須）
@app.post("/data", response_model=DataBase, status_code=201)
def create_data_item(item: DataBase, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO data (value_1, value_2) VALUES (?, ?)",
        (item.value_1, item.value_2),
    )
    conn.commit()
    item_id = cursor.lastrowid
    conn.close()
    return DataBase(id=item_id, value_1=item.value_1, value_2=item.value_2)

# 回答投稿（ログイン必須）
@app.post("/answers", status_code=201)
def create_answer(answer: Answer, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO answers (question_id, user_id, content) VALUES (?, ?, ?)",
        (answer.question_id, current_user["id"], answer.content),
    )
    conn.commit()
    answer_id = cursor.lastrowid
    conn.close()
    return {"id": answer_id, "question_id": answer.question_id, "user_id": current_user["id"], "content": answer.content}

# 評価（いいね）投稿（重複不可）
@app.post("/ratings", status_code=201)
def create_rating(
    target_type: str = Body(..., embed=True),
    target_id: int = Body(..., embed=True),
    current_user: dict = Depends(get_current_user)
):
    if target_type not in ["question", "answer"]:
        raise HTTPException(status_code=400, detail="target_typeは'question'か'answer'のみ有効です")

    conn = get_db_connection()
    cursor = conn.cursor()
    exists = cursor.execute(
        "SELECT * FROM ratings WHERE user_id = ? AND target_type = ? AND target_id = ?",
        (current_user["id"], target_type, target_id)
    ).fetchone()
    if exists:
        conn.close()
        raise HTTPException(status_code=400, detail="すでに評価済みです")

    cursor.execute(
        "INSERT INTO ratings (user_id, target_type, target_id) VALUES (?, ?, ?)",
        (current_user["id"], target_type, target_id),
    )
    conn.commit()
    conn.close()
    return {"message": "評価を登録しました"}

# ユーザー登録
@app.post("/register")
def register_user(form: OAuth2PasswordRequestForm = Depends()):
    conn = get_db_connection()
    cursor = conn.cursor()
    existing = cursor.execute("SELECT * FROM users WHERE username = ?", (form.username,)).fetchone()
    if existing:
        conn.close()
        raise HTTPException(status_code=400, detail="ユーザー名は既に使われています")
    hashed_pw = get_password_hash(form.password)
    cursor.execute(
        "INSERT INTO users (username, hashed_password) VALUES (?, ?)", (form.username, hashed_pw)
    )
    conn.commit()
    conn.close()
    return {"message": "ユーザー登録成功"}

# ログイン（トークン発行）
@app.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends()):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (form.username,)).fetchone()
    conn.close()
    if user is None or not verify_password(form.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="ユーザー名かパスワードが間違っています")

    access_token = create_access_token(
        data={"sub": user["username"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

# プロフィール取得
@app.get("/users/me")
def get_my_profile(current_user: dict = Depends(get_current_user)):
    return {"username": current_user["username"], "profile": current_user["profile"]}

# プロフィール編集
@app.put("/users/me/profile")
def update_profile(profile_data: UserProfileUpdate, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET profile = ? WHERE id = ?", (profile_data.profile, current_user["id"]))
    conn.commit()
    conn.close()
    return {"message": "プロフィールを更新しました"}

# 管理者専用API例：質問削除
@app.delete("/admin/questions/{question_id}")
def delete_question(question_id: int, admin_user: dict = Depends(get_admin_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM data WHERE id = ?", (question_id,))
    conn.commit()
    conn.close()
    return {"message": f"質問ID {question_id} を削除しました"}

# 検索API（質問・回答を全文検索）
@app.get("/search")
def search_items(q: str = Query(..., min_length=1)):
    conn = get_db_connection()
    questions = conn.execute("SELECT * FROM data WHERE value_1 LIKE ?", (f"%{q}%",)).fetchall()
    answers = conn.execute("SELECT * FROM answers WHERE content LIKE ?", (f"%{q}%",)).fetchall()

    results = []

    for qrow in questions:
        results.append({"type": "question", "id": qrow["id"], "content": qrow["value_1"]})

    for arow in answers:
        results.append({"type": "answer", "id": arow["id"], "question_id": arow["question_id"], "content": arow["content"]})

    conn.close()
    return results

# フロントファイル配信
@app.get("/", response_class=HTMLResponse)
def read_html():
    path = os.path.join(BASE_DIR, "client.html")
    with open(path, encoding="utf-8") as f:
        return f.read()

@app.get("/style.css")
def read_css():
    path = os.path.join(BASE_DIR, "style.css")
    with open(path, encoding="utf-8") as f:
        return Response(content=f.read(), media_type="text/css")

@app.get("/script.js", response_class=PlainTextResponse)
def read_js():
    path = os.path.join(BASE_DIR, "script.js")
    with open(path, encoding="utf-8") as f:
        return PlainTextResponse(content=f.read(), media_type="application/javascript")

@app.get("/favicon.ico")
def read_favicon():
    path = os.path.join(BASE_DIR, "favicon.ico")
    with open(path, "rb") as f:
        return Response(content=f.read(), media_type="image/x-icon")

# ==== アプリ起動 ====
if __name__ == "__main__":
    initialize_db()
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
