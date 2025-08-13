# 見出し＋（あれば）本文から、次の5点をJSONで同時生成します：
# summary：1〜2文の要約（最大文字数ガード付き）
# keywords：具体語 3〜6 個（配列）
# comment：編集メモ風のひと言
# comment_type：insight | caution | impact
# quality：ok | shortened | fallback
# さらに、軽いリトライ・JSONモード強制・文字数クランプ・旧API互換ラッパー・バッチ処理まで揃った“実運用寄り”の拡張版
import os, json, time
from typing import List, Dict, Optional
from dotenv import load_dotenv
from openai import OpenAI

# 事前設定（.env／モデル／クライアント）
load_dotenv()
MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")  # .env から OPENAI_API_KEY を読み込み。OPENAI_MODEL 未設定時は "gpt-4.1-mini" にフォールバック。

_client = None
def get_client():
    """OpenAI() をシングルトンで保持（再接続コスト削減）"""
    global _client
    if _client is None:
        _client = OpenAI()
    return _client

# —— プロンプト設計（拡張版） ——
SYSTEM_PROMPT_PLUS = (
    "あなたは新聞見出しの要約アシスタントです。\n"
    "出力は必ず JSON で、keys="
    "['summary','keywords','comment','comment_type','quality']。\n"
    "厳守事項：\n"
    "1) summary: 1〜2文、最大{max_chars}文字。誇張・推測禁止。固有名詞・数値・時期を優先。\n"
    "2) keywords: 具体語3〜6個の配列（一般語や重複は不可）。\n"
    "3) comment: 編集メモ風に短く最大{comment_max}文字。事実ベースの示唆/注意/影響のいずれかに絞る。\n"
    "4) comment_type: 'insight'|'caution'|'impact' のいずれか。\n"
    "5) quality: 'ok'|'shortened'|'fallback'。上限超過や情報不足なら 'shortened'。\n"
    "6) 本文(text)があれば優先（見出しに無い固有情報を抽出）。URLや媒体名は書かない。\n"
)

# 旧APIとの整合を取りつつ chat.completions の JSONモードを利用
def _response_format():
    return {"type": "json_object"} # Chat Completions の JSONモードを使用（崩れ対策の第一手）。

def _coerce_json(text: str) -> Dict:
    """モデル出力を安全にJSON化"""
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    # フォールバック
    return {
        "summary": text.strip()[:120],
        "keywords": [],
        "comment": "",
        "comment_type": "insight",
        "quality": "fallback",
    }

def _call(payload: Dict, max_retries: int = 2) -> str: # 最大2回の再試行＋短い待機。瞬間的なエラー（レート制限・ネットワーク）を吸収。
    """軽いリトライ付き呼び出し"""
    last_err = None
    cli = get_client()
    for _ in range(max_retries + 1):
        try:
            resp = cli.chat.completions.create(**payload)
            content = resp.choices[0].message.content
            if not content:
                raise RuntimeError("Empty response content")
            return content
        except Exception as e:
            last_err = e
            time.sleep(0.5)
    raise last_err

# —— 新: 複合モードのメイン関数 ——
def generate_summary_plus(
    title: str,
    source: str = "",
    max_chars: int = 90,
    body: str = "",
    comment_max: int = 70,
    temperature: float = 0.2,
) -> Dict:
    """
    要約 + 独自コメントを同時生成する拡張版。
    戻り値: dict(summary, keywords[], comment, comment_type, quality, model)
    """
    # 上限の安全化
    hard_limit = max(30, min(160, max_chars))
    comment_limit = max(40, min(100, comment_max))

    system = SYSTEM_PROMPT_PLUS.format(max_chars=hard_limit, comment_max=comment_limit)

    if body:
        snippet = body[:4000]  # トークン節約
        user = {
            "title": title,
            "text": snippet
        }
    else:
        user = {
            "title": title,
            "text": ""
        }
    # APIペイロード
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(user, ensure_ascii=False)},
        ],
        "response_format": _response_format(),
        "temperature": temperature,
    }
    # 呼び出し → パース
    raw = _call(payload)
    data = _coerce_json(raw)

    # 整形＆ガード
    summary = (data.get("summary") or "").strip()
    comment = (data.get("comment") or "").strip()
    kws = data.get("keywords") or []
    if isinstance(kws, str):
        try:
            kws = json.loads(kws)
        except Exception:
            kws = [k.strip() for k in kws.split(",") if k.strip()]
    if len(summary) > hard_limit:
        summary = summary[:hard_limit]
        data["quality"] = "shortened"
    if len(comment) > comment_limit:
        comment = comment[:comment_limit]
        data["quality"] = "shortened"

    return {
        "summary": summary,
        "keywords": kws[:6],
        "comment": comment,
        "comment_type": data.get("comment_type", "insight"),
        "quality": data.get("quality", "ok"),
        "model": MODEL,
    } # keywords は最大6件に制限。comment_type が欠けたら insight にフォールバック。

# —— 既存互換（旧インターフェース） ——
def generate_summary(title: str, source: str, max_chars: int = 60, body: str = "") -> dict:
    """
    既存呼び出し箇所のために残す薄いラッパー。
    戻り値は従来どおり: summary/keywords/quality
    """
    res = generate_summary_plus(
        title=title,
        source=source,
        max_chars=max_chars,
        body=body,
        # 旧版は極力コンパクトにするためコメント短め
        comment_max=60,
    )
    return {
        "summary": res["summary"],
        "keywords": res["keywords"],
        "quality": res["quality"],
    }

# —— まとめ実行（複数件） ——
def batch_summarize_plus(items: List[Dict], **kwargs) -> List[Dict]:
    """
    items: [{ 'title': str, 'body': Optional[str], 'source': Optional[str] }, ...]
    それぞれに generate_summary_plus を適用。
    """
    out: List[Dict] = []
    for it in items: # 1件ずつ順次処理し、個別エラーはその要素だけ fallback。全体停止を避けます。
        try:
            out.append(generate_summary_plus(
                title=it.get("title", ""),
                source=it.get("source", ""),
                body=it.get("body", "") or it.get("text", ""),
                **kwargs
            ))
        except Exception as e:
            out.append({
                "summary": (it.get("title") or "")[:90],
                "keywords": [],
                "comment": "",
                "comment_type": "insight",
                "quality": "fallback",
                "model": MODEL,
                "error": str(e),
            })
    return out

# —— 動作確認（直接実行） ——（サンプル）
if __name__ == "__main__":
    print("MODEL=", MODEL, " KEY(set?)=", bool(os.getenv("OPENAI_API_KEY")))
    sample = generate_summary_plus(
        title="日銀が追加利上げを検討、為替の変動に警戒し市場対話を強化",
        body="日銀は次回会合で追加利上げの是非を議論する見通し。物価と賃上げの持続性を点検し、"
             "長短金利操作の調整も選択肢。円安進行に伴う物価上振れリスクを注視。",
        max_chars=90,
        comment_max=60,
    )
    print(json.dumps(sample, ensure_ascii=False, indent=2))
