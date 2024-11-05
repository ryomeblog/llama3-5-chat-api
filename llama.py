from flask import Flask, request, jsonify
from flask_openapi3 import OpenAPI, Info, Tag
from pydantic import BaseModel
from llama3 import Llama3Model
import datetime
import json
import os

# OpenAPIの基本情報を設定
info = Info(title="Chat API", version="1.0.0")

# FlaskアプリケーションをOpenAPIで初期化
app = OpenAPI(__name__, info=info)

# Llama3モデルの初期化
model = Llama3Model()

# 会話ログを保存するファイル名
conversation_log_file = "conversation_log.json"

# OpenAPIのタグを設定
chat_tag = Tag(name="chat", description="チャットに関連する操作")
log_tag = Tag(name="log", description="会話ログに関連する操作")

# チャットリクエストのデータモデルを定義
class ChatRequest(BaseModel):
    conversation_id: int = None  # 会話ID（任意）
    prompt: str  # プロンプト（必須）

# ログリクエストのデータモデルを定義
class LogRequest(BaseModel):
    conversation_id: int  # 会話ID（必須）

# 会話ログを読み込む関数
def load_conversation_log():
    if os.path.exists(conversation_log_file):
        with open(conversation_log_file, "r", encoding="utf-8") as file:
            return json.load(file)
    return {}

# 会話ログを保存する関数
def save_conversation_log(log):
    with open(conversation_log_file, "w", encoding="utf-8") as file:
        json.dump(log, file, ensure_ascii=False, indent=4)

# チャットエンドポイントを定義
@app.post("/chat", tags=[chat_tag])
def chat(body: ChatRequest):
    """
    モデルにプロンプトを送信し、応答を取得する。
    """
    data = body.dict()  # リクエストボディを辞書に変換
    conversation_id = data.get("conversation_id", int(datetime.datetime.now().timestamp()))  # 会話IDを取得（なければタイムスタンプを使用）
    prompt = data.get("prompt")  # プロンプトを取得
    
    if not prompt:
        return jsonify({"error": "プロンプトが必要です"}), 400  # プロンプトがない場合はエラーを返す
    
    conversation_log = load_conversation_log()  # 会話ログを読み込む
    
    if conversation_id not in conversation_log:
        conversation_log[conversation_id] = []  # 会話IDが存在しない場合は新規作成
    
    # 過去の会話履歴をプロンプトに追加
    past_conversation = "\n".join(conversation_log[conversation_id])
    full_prompt = f"{past_conversation}\nあなた: {prompt}"
    
    response = model.prompt(full_prompt)  # モデルにプロンプトを送信し、応答を取得
    
    # 会話ログに追加
    conversation_log[conversation_id].append(f"あなた: {prompt}")
    conversation_log[conversation_id].append(f"モデル: {response}")
    
    save_conversation_log(conversation_log)  # 会話ログを保存
    
    return jsonify({"conversation_id": conversation_id, "response": response})  # 応答を返す

# ログ取得エンドポイントを定義
@app.get("/log", tags=[log_tag])
def get_log(query: LogRequest):
    """
    会話IDで会話ログを取得する。
    """
    conversation_id = query.conversation_id  # 会話IDを取得
    
    if not conversation_id:
        return jsonify({"error": "会話IDが必要です"}), 400  # 会話IDがない場合はエラーを返す
    
    conversation_log = load_conversation_log()  # 会話ログを読み込む
    
    if conversation_id not in conversation_log:
        return jsonify({"error": "会話が見つかりません"}), 400  # 会話IDが存在しない場合はエラーを返す
    
    return jsonify({"conversation_id": conversation_id, "log": conversation_log[conversation_id]})  # 会話ログを返す

# アプリケーションをデバッグモードで実行
if __name__ == "__main__":
    app.run(debug=True)
