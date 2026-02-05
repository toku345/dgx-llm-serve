# Qwen3 Thinking モード

Qwen3 モデルは推論時に「思考プロセス」を出力する Thinking モードを備えている。

## 概要

- **デフォルト**: 有効（Thinking モード）
- **出力形式**: レスポンスに `<think>...</think>` タグで思考プロセスが含まれる
- **対応バックエンド**: TensorRT-LLM, vLLM（Qwen3 系モデル）

## Thinking モード（有効）

デフォルトの動作。モデルは回答前に思考プロセスを出力する。

### リクエスト例

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nvidia/Qwen3-30B-A3B-FP4",
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
    "model": "nvidia/Qwen3-30B-A3B-FP4",
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

Thinking モード使用時は、クライアント側でレスポンスから `<think>...</think>` タグを除去する必要がある。

### Python での除去例

```python
import re

def remove_thinking(response: str) -> str:
    """Remove <think>...</think> tags from response."""
    return re.sub(r'<think>.*?</think>\s*', '', response, flags=re.DOTALL)
```

### JavaScript での除去例

```javascript
function removeThinking(response) {
  return response.replace(/<think>[\s\S]*?<\/think>\s*/g, '');
}
```

## 備考

- trtllm-serve は現時点で `--reasoning_parser` オプション未対応
- Thinking タグの自動除去はクライアント側で実装が必要
