from fastapi import FastAPI, Response
from fastapi.responses import HTMLResponse, PlainTextResponse
from pydantic import BaseModel
from typing import List, Optional

import sqlite3
import os
import uvicorn

app = FastAPI()

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "data.db")


class DataBase(BaseModel):
    id: Optional[int] = None
    value_1: str
    value_2: Optional[str] = None


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            value_1 TEXT NOT NULL,
            value_2 TEXT
        )
        """
    )
    conn.commit()
    conn.close()


@app.get("/data", response_model=List)
def read_data_items():
    conn = get_db_connection()
    items = conn.execute("SELECT id FROM data").fetchall()
    conn.close()
    return [item["id"] for item in items]


# FastAPIのデコレータ。GETリクエストで "/data/{item_id}"
# というパスにアクセスがあった場合に、この関数を実行する
# {item_id} はパスパラメータと呼ばれ、URLの一部として渡される値。
# 例えば /data/5 にアクセスすると item_id は 5 になる
@app.get("/data/{item_id}", response_model=DataBase)
def read_data_item(item_id: int):
    # データベースへの接続を取得する
    conn = get_db_connection()

    # TODO: 課題　idに対応するデータを取得するSQLをexecute内に書く
    # テーブル名は data
    item = conn.execute("SELECT * FROM data WHERE id = ?", (item_id,)).fetchone()

    # データベース接続を閉じる (リソースの解放)
    conn.close()

    # 取得したデータが存在する場合 (itemがNoneでない場合)
    if item:
        # APIのレスポンスとして、取得したデータをDataBaseモデルに基づいて返す
        return DataBase(
            id=item["id"],  # 取得したデータのid
            value_1=item["value_1"],  # 取得したデータのvalue_1
            value_2=item["value_2"],  # 取得したデータのvalue_2
        )

    # 取得したデータが存在しない場合 (itemがNoneの場合)
    # HTTPステータスコード404 (Not Found) を返すResponseオブジェクトを生成して返す
    # これにより、クライアントは指定されたIDのデータが見つからなかったことを知ることができる
    return Response(status_code=404)


@app.post("/data", response_model=DataBase, status_code=201)
def create_data_item(item: DataBase):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO data (value_1, value_2) VALUES (?, ?)",
        (item.value_1, item.value_2),
    )
    conn.commit()
    item_id = cursor.lastrowid
    conn.close()
    return DataBase(
        id=item_id,
        value_1=item.value_1,
        value_2=item.value_2,
    )


# ここから下は書き換えない
@app.get("/", response_class=HTMLResponse)
async def read_html():
    html_file_path = os.path.join(BASE_DIR, "client.html")
    with open(html_file_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content, status_code=200)


@app.get("/style.css")
def read_css():
    css_file_path = os.path.join(BASE_DIR, "style.css")
    with open(css_file_path, "r", encoding="utf-8") as f:
        css_content = f.read()
    return Response(content=css_content, media_type="text/css")


@app.get("/script.js", response_class=PlainTextResponse)
def read_js():
    js_file_path = os.path.join(BASE_DIR, "script.js")
    with open(js_file_path, "r", encoding="utf-8") as f:
        js_content = f.read()
    return PlainTextResponse(
        content=js_content, status_code=200, media_type="application/javascript"
    )


if __name__ == "__main__":
    initialize_db()
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
