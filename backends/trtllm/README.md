# TRT-LLM Backend

TensorRT-LLM (`1.3.0rc2`) を使用した LLM サービング環境。

## 対応モデル

| プロファイル | モデル | 量子化 | 推定メモリ |
|-------------|--------|--------|-----------|
| qwen | Qwen3-30B-A3B-FP4 | FP4 | ~8 GiB |
| nemotron | NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4 | NVFP4 | ~16 GiB |
| multi | 上記2モデル同時起動 | — | ~25 GiB |

## 起動

```bash
# Qwen3-FP4
docker compose --profile qwen up

# Nemotron-NVFP4
docker compose --profile nemotron up

# マルチモデル (単一ポートで同時起動)
docker compose --profile multi up
```

## マルチモデル起動

`multi` プロファイルは OpenResty プロキシ経由で2モデルをポート 8000 に統合します。
リクエストボディの `model` フィールドで自動ルーティングされます。

起動順序: Qwen → healthy → Nemotron → healthy → Proxy

| モデル | ルーティング条件 |
|--------|-----------------|
| Qwen3-30B-A3B-FP4 | `model` に "qwen" を含む |
| Nemotron-30B-A3B-NVFP4 | `model` に "nemotron" を含む |

```bash
# 利用可能なモデル一覧
curl http://localhost:8000/v1/models

# Qwen3
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "nvidia/Qwen3-30B-A3B-FP4", "messages": [{"role": "user", "content": "Hello"}]}'

# Nemotron
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4", "messages": [{"role": "user", "content": "Hello"}]}'
```

### 設定ファイル

| ファイル | 対象 | 用途 |
|----------|------|------|
| `nano_v3.yaml` | Nemotron (全プロファイル) | AutoDeploy 設定、`compile_backend: torch-cudagraph` |
| `qwen_multi.yaml` | Qwen (multi のみ) | KV キャッシュメモリ制限 (`free_gpu_memory_fraction: 0.30`) |
| `nginx.conf` | Proxy (multi のみ) | モデル名ベースのリクエストルーティング |

### トラブルシューティング

- **503 unhealthy**: 両バックエンドの起動完了を待ってください（初回は数分かかります）
- **404 unknown model**: `model` フィールドに "qwen" または "nemotron" を含む正しいモデル名を指定してください
- **Nemotron 起動失敗**: `nano_v3.yaml` の `free_gpu_memory_fraction` を調整してください
- **multi で OOM**: `qwen_multi.yaml` の `free_gpu_memory_fraction` を下げてください

## Thinking モード

Qwen3 はデフォルトで **thinking モード（有効）** で動作します。レスポンスに `<think>` タグで思考プロセスが含まれます。

### Non-thinking モードへの切り替え

システムプロンプトに `/no_think` を追加すると、思考プロセスを出力せずに回答のみを返します。

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nvidia/Qwen3-30B-A3B-FP4",
    "messages": [
      {"role": "system", "content": "/no_think"},
      {"role": "user", "content": "Hello"}
    ],
    "max_tokens": 128
  }'
```

thinking モード使用時は、クライアント側でレスポンスから `<think>...</think>` タグを除去する必要があります。

### Nemotron Reasoning Parser

Nemotron は `--reasoning_parser deepseek-r1` により、思考過程をサーバー側で分離します。
レスポンスの `reasoning_content` フィールドに思考過程、`content` フィールドに最終回答が返されます。

## 環境要件

- NVIDIA GPU + nvidia-container-toolkit
- モデルウェイト: `~/model_weights/` に配置
