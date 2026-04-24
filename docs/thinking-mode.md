# Qwen3 Thinking モード

Qwen3 モデルは推論時に「思考プロセス」を出力する Thinking モードを備えている。

## 概要

- **デフォルト**: 有効（Thinking モード）
- **出力形式**: レスポンスに `<think>...</think>` タグで思考プロセスが含まれる（vLLM の `--reasoning-parser qwen3` により `reasoning_content` フィールドに自動分離）
- **対応バックエンド**: vLLM（Qwen3 系モデル）

## Thinking モード（有効）

デフォルトの動作。モデルは回答前に思考プロセスを出力する。

### リクエスト例

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen3.6-35B-A3B-FP8",
    "messages": [{"role": "user", "content": "What is 2+2?"}],
    "max_tokens": 256
  }'
```

### レスポンス例

```
<think>
The user is asking for a simple arithmetic calculation.
2 + 2 = 4
</think>

The answer is 4.
```

## Non-thinking モード（無効化）

システムプロンプトに `/no_think` を追加すると、思考プロセスを出力せずに回答のみを返す。

### リクエスト例

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen3.6-35B-A3B-FP8",
    "messages": [
      {"role": "system", "content": "/no_think"},
      {"role": "user", "content": "What is 2+2?"}
    ],
    "max_tokens": 128
  }'
```

### レスポンス例

```
The answer is 4.
```

## クライアント側での処理

本リポジトリの qwen36 profile は起動時に `--reasoning-parser qwen3` を指定しているため、思考プロセスは自動的に **`reasoning_content` フィールド** に分離されて返る。通常のクライアントは `content` をそのまま使えばよく、`<think>...</think>` タグを手動で除去する必要はない。

### レスポンス構造

```json
{
  "choices": [{
    "message": {
      "content": "The answer is 4.",
      "reasoning_content": "The user is asking for a simple arithmetic calculation. 2 + 2 = 4"
    }
  }]
}
```

### `<think>` タグの手動除去が必要になるケース

以下のいずれかの場合のみ、クライアント側で生レスポンスからタグを除去する実装が必要。

- vLLM を `--reasoning-parser qwen3` **なし** で起動したとき
- 将来別モデルで reasoning parser が未対応だったとき

<details>
<summary>手動除去の参考実装</summary>

```python
import re

def remove_thinking(response: str) -> str:
    """Remove <think>...</think> tags from response."""
    return re.sub(r'<think>.*?</think>\s*', '', response, flags=re.DOTALL)
```

```javascript
function removeThinking(response) {
  return response.replace(/<think>[\s\S]*?<\/think>\s*/g, '');
}
```

</details>
