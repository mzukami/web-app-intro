from fastapi import FastAPI, Response
from fastapi.responses import HTMLResponse, PlainTextResponse
import os
import uvicorn
import random  # random モジュールをインポート

app = FastAPI()

BASE_DIR = os.path.dirname(__file__)

# 天気予報のリスト
weather_forecasts = ["晴れ", "曇り", "雨", "雪", "快晴", "強風"]


# ランダムな天気予報を返す API エンドポイント
@app.get("/weather")
async def get_weather():
    forecast = random.choice(weather_forecasts)
    return {"weather": forecast}


@app.get("/weather-forecast")
async def get_weather_forecast():
    forecast = random.choice(weather_forecasts)
    return {"weather": forecast}


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
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
