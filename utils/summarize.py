# 安定版: chat.completions + JSONモード、ニュース見出しを秒速で要約して JSON で返す” 用のミニモジュール
import os, json
from dotenv import load_dotenv
from openai import OpenAI

# 事前設定（.env／モデル／クライアント）
load_dotenv()
MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini") # .env に OPENAI_API_KEY が入っている前提。OPENAI_MODEL は未設定なら "gpt-4.1-mini"。

_client = None
def get_client(): # get_client() はシングルトン：初回だけ OpenAI() を作って _client にキャッシュ。以降は再利用。（毎回再接続しないので速くて安定）
    global _client
    if _client is None:
        _client = OpenAI()  # OPENAI_API_KEY を .env から読む
    return _client

# システムプロンプト設計
SYSTEM_PROMPT = ( # 最大文字数・文数・出力JSONのキーをシステムで強制。ユーザープロンプト側より強く効くので、フォーマット崩れを抑えられます。
    "あなたは新聞見出しの要約アシスタントです。"
    "以下を厳守：1) 要約は1〜2文で最大{max_chars}文字、誇張禁止。"
    "2) 固有情報を優先。3) 見出しだけでも成立。"
    "出力は必ず JSON で、keys=['summary','keywords','quality']。"
    "keywords は配列、quality は 'ok'|'shortened'|'fallback' のいずれか。"
) # max_chars は後述の hard_limit を差し込むので、記事ごとに制限を変えられる。

def generate_summary(title: str, source: str, max_chars: int = 60, body: str = "") -> dict: # 入力：見出し title、媒体名 source、上限文字数 max_chars（デフォ60）、任意の本文 body。
    # 文字数上限の安全化
    hard_limit = max(30, min(120, max_chars)) # 30〜120 文字の範囲にクランプ。極端な値でも壊れないようにするガード。
    system = SYSTEM_PROMPT.format(max_chars=hard_limit)
    # ユーザーメッセージを組み立て
    if body:
        # 本文があれば最初の4000文字に切る（トークン節約）。本文がある場合は「見出しに無い固有事実を優先」と指示。
        snippet = body[:4000]
        user = (
            f"ソース: {source}\n[見出し]\n{title}\n\n"
            "以下は記事本文の抜粋です。見出しに無い“事実情報”（数値・人名・地名・時刻・因果）を優先して要約。\n"
            "[本文]\n" + snippet + "\n\n必ずJSONで。"
        )
    else:
        user = f"ソース: {source}\n[見出し]\n{title}\n\n必ずJSONで。" # どちらでも最後に「必ずJSONで」を重ねておくのが地味に効く。

    # API 呼び出し（JSON モード）
    resp = get_client().chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        response_format={"type": "json_object"},  # response_format={"type":"json_object"} でJSONモード。フォーマット崩れが激減します。
        temperature=0.2, # temperature=0.2 はブレ抑制（再現性・一貫性重視の要約に向く）。
    )
    text = resp.choices[0].message.content

    # JSON を堅牢にパース
    try:
        data = json.loads(text)
    except Exception:
        # まれにプレーンテキストが混ざる場合があるので保険
        data = {"summary": text.strip(), "keywords": [], "quality": "fallback"}

    # 最低限の整形
    summary = (data.get("summary") or "").strip()
    kws = data.get("keywords") or []
    if isinstance(kws, str): # keywords が文字列で返ることがあるため、配列化を丁寧にハンドリング。
        try:
            kws = json.loads(kws) # ほぼ JSON で返りますが、万一の保険でテキスト直返しも受け止めて fallback 扱い。
        except Exception:
            kws = [k.strip() for k in kws.split(",") if k.strip()]
    if len(summary) > hard_limit: # 要約は最終的にも切り詰め（モデルの出し過ぎ対策／二重ガード）。
        summary = summary[:hard_limit]

    return {
        "summary": summary,
        "keywords": kws[:6],
        "quality": data.get("quality", "ok"),
    } # 返却は keywords を最大6件にスライス、quality はあればそのまま、無ければ "ok"。

if __name__ == "__main__": # 直接実行すると、キーが見えているかとサンプル要約を表示。セットアップ確認に便利。
    print("MODEL=", MODEL, " KEY(set?)=", bool(os.getenv("OPENAI_API_KEY")))
    print(generate_summary("日銀が政策金利を据え置き、景気判断を下方修正", "テスト"))
