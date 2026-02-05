# NIM on DGX Spark

NVIDIA NIM を DGX Spark 上で実行するための Docker Compose 設定。

## 必要条件

- DGX Spark (GB10)
- Docker / Docker Compose
- NVIDIA Container Toolkit
- NGC API キー

## セットアップ

### 1. NGC API キーの取得

https://org.ngc.nvidia.com/setup/api-key から Personal API キーを取得。

### 2. 環境変数の設定

```bash
export NGC_API_KEY="<YOUR_NGC_API_KEY>"
```

### 3. NGC レジストリへのログイン

```bash
echo "$NGC_API_KEY" | docker login nvcr.io --username '$oauthtoken' --password-stdin
```

### 4. キャッシュディレクトリの準備

```bash
mkdir -p ~/.cache/nim
chmod -R 700 ~/.cache/nim
```

## 起動

```bash
docker compose up
```

初回起動時はモデルのダウンロードに時間がかかります。

## 動作確認

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "Qwen/Qwen3-32B", "messages": [{"role": "user", "content": "Hello"}]}'
```

## モデルの変更

`compose.yml` の `image` を変更することで別のモデルを使用可能。

DGX Spark 対応 NIM:
- `nvcr.io/nim/qwen/qwen3-32b-dgx-spark:1.1.0-variant`
- `nvcr.io/nim/meta/llama-3.1-8b-instruct-dgx-spark:latest`
- `nvcr.io/nim/nvidia/nvidia-nemotron-nano-9b-v2-dgx-spark:1.0.0-variant`
