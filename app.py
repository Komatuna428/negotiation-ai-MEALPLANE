import streamlit as st
from google import genai
import os

st.set_page_config(
    page_title="対話型値引き交渉AI",
    page_icon="🛍️",
    layout="centered"
)

st.title("🛍️ 対話型値引き交渉 AI")
st.caption("AIの店員とチャットでリアルな値引き交渉を体験しよう！")

@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key="GEMINI_API_KEY")

try:
    client = get_gemini_client()
except Exception as e:
    st.error(f"APIクライアントの初期化に失敗しました: {e}")
    st.stop()

# 難易度を「ちょいムズ（粘れば折れる）」レベルに調整
scenarios = {
    "メイク用品": {
        "item": "美容液",
        "price": 12000,
        "target": 10500,
        "image": "nail.png",
        "instruction": (
            "あなたはECサイトのカスタマーサポートAIです。"
            "定価12,000円の高級美容液を販売しています。"
            "最初のアバウトな「安くして」には断ってください。"
            "ただし、ユーザーが「定期購入（サブスク）にする」「まとめ買いする」などの提案をしてきたら、"
            "最初は「通常はお断りしているのですが…」と迷いつつも、1〜2回粘られたら苦渋の決断として10,500円付近まで値下げに応じてください。"
        )
    },
    "ワイヤレスイヤホン": {
        "item": "ワイヤレスイヤホン",
        "price": 15000,
        "target": 13500,
        "image": "earphones.png",
        "instruction": (
            "あなたは家電ECサイトの店員です。定価15,000円のイヤホンを販売しています。"
            "「他店の方が安い」「予算オーバー」だけでは一旦断りますが、"
            "「レビューを書く」「メルマガ登録する」「即決する」などの提案で1〜2回粘られたら、"
            "「特別に…」と13,500円への値下げ、またはおまけの追加を承諾してください。"
        )
    },
    "腕時計": {
        "item": "ブランド腕時計",
        "price": 50000,
        "target": 45000,
        "image": "watch.png",
        "instruction": (
            "あなたはフリマアプリの出品者です。定価50,000円の美品腕時計を出品しています。"
            "いきなり4万円などの大幅値引きは突っぱねますが、"
            "丁寧に挨拶され「〇〇円なら即決できる」「大切に使う」と熱意を示して粘られたら、"
            "段階的に歩み寄って最終的に45,000円まで下げてあげてください。"
        )
    }
}

if "selected_scenario" not in st.session_state:
    st.session_state.selected_scenario = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat" not in st.session_state:
    st.session_state.chat = None

if st.session_state.selected_scenario is None:
    st.markdown("### 📍 交渉するシチュエーションを選んでね（※難易度ノーマル〜やや難）")
    st.write("")

    cols = st.columns(3)
    
    for i, (name, data) in enumerate(scenarios.items()):
        with cols[i]:
            if os.path.exists(data["image"]):
                st.image(data["image"], width=80)
            else:
                st.info("画像なし")
            
            st.markdown(f"**{name.split('（')[0]}**")
            st.caption(f"定価: {data['price']:,}円")
            
            if st.button("この店員と交渉する", key=f"btn_{i}", use_container_width=True):
                st.session_state.selected_scenario = name
                
                system_instruction = (
                    f"{data['instruction']}\n\n"
                    f"【会話ルール】\n"
                    f"- 目標値引き価格は {data['target']:,} 円程度です。\n"
                    f"- 一度断っても、条件提示（定期購入やレビュー等）や粘り強い交渉があったら柔軟に折れてあげてください。\n"
                    f"- **返答は必ず1〜2文（最大2行）以内**で、チャットらしく短くテンポよく返信してください。"
                )
                
                st.session_state.chat = client.chats.create(
                    model="gemini-3.5-flash",
                    config={"system_instruction": system_instruction}
                )
                
                initial_msg = f"いらっしゃいませ！{data['item']}（定価{data['price']:,}円）はいかがですか？何かご質問はございますか？"
                st.session_state.messages = [{"role": "model", "content": initial_msg}]
                st.rerun()

else:
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(f"**現在のシチュエーション:** {st.session_state.selected_scenario}")
    with col2:
        if st.button("🔄 選び直す"):
            st.session_state.selected_scenario = None
            st.session_state.messages = []
            st.session_state.chat = None
            st.rerun()
            
    st.divider()

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if user_input := st.chat_input("値引き交渉のセリフを入力..."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("model"):
            with st.spinner("店員が考えています..."):
                try:
                    response = st.session_state.chat.send_message(user_input)
                    ai_reply = response.text
                    st.markdown(ai_reply)
                    st.session_state.messages.append({"role": "model", "content": ai_reply})
                except Exception as e:
                    st.error(f"エラーが発生しました: {e}")
