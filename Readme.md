# Llama3.5 Chat API

このプロジェクトは、FlaskとOpenAPIを使用して構築されたチャットAPIです。Llama3モデルを使用して、ユーザーからのプロンプトに応答します。また、会話ログを保存し、特定の会話IDに基づいてログを取得する機能も提供します。

## 必要条件

以下のパッケージが必要です。`requirements.txt`ファイルを使用してインストールできます。

```sh
pip install -r requirements.txt
```

`requirements.txt`の内容は以下の通りです：

```
flask
flask-openapi3[swagger,redoc,rapidoc,rapipdf,scalar,elements]
pydantic
llama3-package
requests
```

## 使用方法

### 1. リポジトリをクローンする

```sh
git clone <リポジトリのURL>
cd <リポジトリのディレクトリ>
```

### 2. 必要なパッケージをインストールする

```sh
pip install -r requirements.txt
```

### 3. アプリケーションを実行する

```sh
python <ファイル名>.py
```

### 4. OpenAPIドキュメントにアクセスする

アプリケーションを実行した後、以下のURLにアクセスしてSwagger UIでAPIドキュメントを確認できます。

```
http://127.0.0.1:5000/openapi
```

## エンドポイント

### POST /chat

モデルにプロンプトを送信し、応答を取得します。

- **リクエストボディ**:
  - `conversation_id` (int, 任意): 会話ID。指定しない場合は新しいIDが生成されます。
  - `prompt` (str, 必須): モデルに送信するプロンプト。

- **レスポンス**:
  - `conversation_id` (int): 会話ID。
  - `response` (str): モデルからの応答。

#### 例

```sh
curl -X POST "http://127.0.0.1:5000/chat" -H "Content-Type: application/json" -d '{"prompt": "こんにちは"}'
```

### GET /log

特定の会話IDに基づいて会話ログを取得します。

- **クエリパラメータ**:
  - `conversation_id` (int, 必須): 会話ID。

- **レスポンス**:
  - `conversation_id` (int): 会話ID。
  - `log` (list): 会話ログ。

#### 例

```sh
curl -X GET "http://127.0.0.1:5000/log?conversation_id=1234567890"
```

## コードの説明

### モジュールのインポート

```python
from flask import Flask, request, jsonify
from flask_openapi3 import OpenAPI, Info, Tag
from pydantic import BaseModel
from llama3 import Llama3Model
import datetime
import json
import os
```

### OpenAPIの基本情報を設定

```python
info = Info(title="Chat API", version="1.0.0")
app = OpenAPI(__name__, info=info)
```

### Llama3モデルの初期化

```python
model = Llama3Model()
conversation_log_file = "conversation_log.json"
```

### OpenAPIのタグを設定

```python
chat_tag = Tag(name="chat", description="チャットに関連する操作")
log_tag = Tag(name="log", description="会話ログに関連する操作")
```

### データモデルの定義

```python
class ChatRequest(BaseModel):
    conversation_id: int = None
    prompt: str

class LogRequest(BaseModel):
    conversation_id: int
```

### 会話ログの読み込みと保存

```python
def load_conversation_log():
    if os.path.exists(conversation_log_file):
        with open(conversation_log_file, "r", encoding="utf-8") as file:
            return json.load(file)
    return {}

def save_conversation_log(log):
    with open(conversation_log_file, "w", encoding="utf-8") as file:
        json.dump(log, file, ensure_ascii=False, indent=4)
```

### チャットエンドポイント

```python
@app.post("/chat", tags=[chat_tag])
def chat(body: ChatRequest):
    data = body.dict()
    conversation_id = data.get("conversation_id", int(datetime.datetime.now().timestamp()))
    prompt = data.get("prompt")
    
    if not prompt:
        return jsonify({"error": "プロンプトが必要です"}), 400
    
    conversation_log = load_conversation_log()
    
    if conversation_id not in conversation_log:
        conversation_log[conversation_id] = []
    
    past_conversation = "\n".join(conversation_log[conversation_id])
    full_prompt = f"{past_conversation}\nあなた: {prompt}"
    
    response = model.prompt(full_prompt)
    
    conversation_log[conversation_id].append(f"あなた: {prompt}")
    conversation_log[conversation_id].append(f"モデル: {response}")
    
    save_conversation_log(conversation_log)
    
    return jsonify({"conversation_id": conversation_id, "response": response})
```

### ログ取得エンドポイント

```python
@app.get("/log", tags=[log_tag])
def get_log(query: LogRequest):
    conversation_id = query.conversation_id
    
    if not conversation_id:
        return jsonify({"error": "会話IDが必要です"}), 400
    
    conversation_log = load_conversation_log()
    
    if conversation_id not in conversation_log:
        return jsonify({"error": "会話が見つかりません"}), 400
    
    return jsonify({"conversation_id": conversation_id, "log": conversation_log[conversation_id]})
```

### アプリケーションの実行

```python
if __name__ == "__main__":
    app.run(debug=True)
```
