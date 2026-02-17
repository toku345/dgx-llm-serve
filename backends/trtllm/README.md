# TRT-LLM Backend

TensorRT-LLM (`1.3.0rc3`) を使用した LLM サービング環境。

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
| `qwen.yaml` | Qwen (standalone のみ) | AutoDeploy 設定、`compile_backend: torch-cudagraph` |
| `qwen_multi.yaml` | Qwen (multi のみ) | KV キャッシュメモリ制限、`compile_backend: torch-cudagraph` |
| `nginx.conf` | Proxy (multi のみ) | モデル名ベースのリクエストルーティング |

### トラブルシューティング

- **503 unhealthy**: 両バックエンドの起動完了を待ってください（初回は数分かかります）
- **404 unknown model**: `model` フィールドに "qwen" または "nemotron" を含む正しいモデル名を指定してください
- **Nemotron 起動失敗**: `nano_v3.yaml` の `free_gpu_memory_fraction` を調整してください
- **multi で OOM**: `qwen_multi.yaml` の `free_gpu_memory_fraction` を下げてください

### 既知の問題: SM120 `cudaErrorIllegalInstruction`

DGX Spark (SM120 / Blackwell) の multi プロファイルで、Qwen3-FP4 のサンプリング処理中に `cudaErrorIllegalInstruction` が散発します。

- **原因**: TRT-LLM 1.3.0rc3 の cutlass MoE カーネルが SM120 で不正命令を実行する
- **ワークアラウンド**: `--backend _autodeploy` + `compile_backend: torch-cudagraph` で軽減（設定済み）。ただし完全には回避できず、特定の推論パターンでサンプラー内のカーネルが失敗する場合がある
- **影響**: エラー発生後、エグゼキューターのイベントループがクラッシュし以降のリクエストは処理不可能になる。**ただし `/health` は 200 を返し続ける**ため、オーケストレーションシステムが障害を検出できない。コンテナの手動再起動が必要
- **監視の推奨**: `/health` だけでは障害を検知できないため、定期的に実際の推論リクエストを送信するライブネスチェックの実装を推奨する（例: 軽量な chat/completions リクエストのタイムアウト監視）
- **対策**: `free_gpu_memory_fraction` を低めに維持してメモリ圧迫を軽減する（Qwen: 0.30、Nemotron: 0.50）。根本解決は TRT-LLM の SM120 カーネル修正またはドライバ 590+ へのアップデート待ち
- **vLLM での代替不可**: Qwen3-FP4 (NVFP4) は vLLM 26.01 の NVIDIA コンテナで単体動作を確認済みだが、ドライバ 580 の Forward Compat 制約により 26.01 コンテナは同時 1 つまでのため、multi 構成では Nemotron (同じく 26.01 必須) と共存できない

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
