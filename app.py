import base64
import json
import random
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


st.set_page_config(page_title="托福单词默写", page_icon="📝", layout="wide")

st.markdown(
    """
    <style>
    :root {
      --bg-deep-1: #070b16;
      --bg-deep-2: #110f24;
      --bg-deep-3: #06060b;
      --card-bg: rgba(15, 18, 34, 0.68);
      --card-border: rgba(181, 108, 255, 0.26);
      --text-main: #e9edff;
      --text-soft: #a8b2d8;
      --line-soft: rgba(0, 245, 255, 0.2);
      --neon-cyan: #00f5ff;
      --neon-purple: #b56cff;
      --ok-color: #7af7c7;
      --bad-color: #c78995;
    }

    html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
      font-family: Inter, Arial, sans-serif;
      color: var(--text-main);
      background:
        radial-gradient(1400px 700px at 12% -10%, rgba(0, 245, 255, 0.1), transparent 45%),
        radial-gradient(1200px 650px at 92% 0%, rgba(181, 108, 255, 0.1), transparent 50%),
        linear-gradient(145deg, var(--bg-deep-1) 0%, var(--bg-deep-2) 48%, var(--bg-deep-3) 100%);
    }

    .block-container {
      padding-top: 2rem;
      padding-bottom: 2rem;
      max-width: 1000px;
    }

    .title {
      font-size: 2rem;
      font-weight: 700;
      margin-bottom: 0.3rem;
      color: #f2f5ff;
      letter-spacing: 0.3px;
      text-shadow: 0 0 10px rgba(0, 245, 255, 0.18);
    }

    .subtitle {
      color: var(--text-soft);
      margin-bottom: 1rem;
    }

    .panel-card {
      padding: 1rem 1.1rem 1.2rem 1.1rem;
      margin-bottom: 1rem;
      border-radius: 14px;
      border: 1px solid rgba(181, 108, 255, 0.18);
      background: var(--card-bg);
      box-shadow:
        0 0 8px rgba(0, 245, 255, 0.04),
        0 0 10px rgba(181, 108, 255, 0.045),
        inset 0 0 0 1px rgba(255, 255, 255, 0.02);
      backdrop-filter: blur(3px);
    }

    .ok {
      color: var(--ok-color);
      font-weight: 600;
      text-shadow: 0 0 8px rgba(122, 247, 199, 0.25);
    }

    .bad {
      color: var(--bad-color);
      font-weight: 600;
      text-shadow: 0 0 3px rgba(199, 137, 149, 0.12);
    }

    .word-box {
      padding: 8px 0;
      border-bottom: 1px solid rgba(140, 165, 255, 0.16);
      color: #dfe6ff;
    }

    h2, h3, .stMarkdown p, .stCaption, label {
      color: var(--text-main) !important;
    }

    .stTextInput > div > div > input {
      color: #eef3ff;
      background: rgba(10, 14, 30, 0.32);
      border: 1px solid rgba(120, 140, 190, 0.2);
      border-radius: 10px;
      box-shadow: 0 0 3px rgba(0, 245, 255, 0.05);
    }

    .stTextInput > div > div > input:focus {
      border-color: rgba(181, 108, 255, 0.3);
      box-shadow: 0 0 6px rgba(181, 108, 255, 0.1);
    }

    .stButton > button {
      border-radius: 10px;
      border: 1px solid rgba(181, 108, 255, 0.28);
      color: #edf1ff;
      background: rgba(18, 24, 48, 0.62);
      transition: all 0.2s ease;
      box-shadow: 0 0 4px rgba(181, 108, 255, 0.07);
    }

    .stButton > button:hover {
      border-color: rgba(0, 245, 255, 0.32);
      box-shadow:
        0 0 6px rgba(0, 245, 255, 0.09),
        0 0 7px rgba(181, 108, 255, 0.08);
      background: rgba(24, 32, 62, 0.64);
      color: #f5f8ff;
    }

    .stAlert {
      background: rgba(14, 24, 44, 0.55);
      border: 1px solid rgba(0, 245, 255, 0.22);
      color: var(--text-main);
    }

    hr {
      border-color: rgba(148, 163, 220, 0.22);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def get_word_file() -> Path:
    target = Path("6托福-乱序.txt")
    if target.exists():
        return target

    txt_files = sorted(Path(".").glob("*.txt"))
    if not txt_files:
        raise FileNotFoundError("当前目录未找到任何 .txt 词库文件。")
    return txt_files[0]


def load_word_pairs() -> list[tuple[str, str]]:
    file_path = get_word_file()
    content = file_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    pairs: list[tuple[str, str]] = []

    for line in content:
        line = line.strip()
        if not line:
            continue
        if "\t" in line:
            en, zh = line.split("\t", 1)
        else:
            parts = line.split(maxsplit=1)
            if len(parts) < 2:
                continue
            en, zh = parts[0], parts[1]
        pairs.append((en.strip(), zh.strip()))

    if len(pairs) < 10:
        raise ValueError("词库单词数量不足 10 个，无法抽题。")
    return pairs


def _b64_encode_text(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def _b64_decode_text(encoded: str) -> str:
    return base64.b64decode(encoded.encode("ascii")).decode("utf-8")


def load_wrong_words_from_query(valid_words: dict[str, str]) -> list[tuple[str, str]]:
    encoded = st.query_params.get("wrong_words_data", "")
    if not encoded:
        return []

    try:
        decoded = _b64_decode_text(encoded)
        payload = json.loads(decoded)
    except Exception:
        return []

    if not isinstance(payload, list):
        return []

    wrong_words: list[tuple[str, str]] = []
    seen: set[str] = set()

    for item in payload:
        if not isinstance(item, dict):
            continue
        en = str(item.get("en", "")).strip()
        zh = str(item.get("zh", "")).strip()
        if not en or en in seen:
            continue

        # 优先使用词库里的标准翻译，避免本地缓存被手动篡改。
        if en in valid_words:
            wrong_words.append((en, valid_words[en]))
        elif zh:
            wrong_words.append((en, zh))
        seen.add(en)

    return wrong_words


def sync_wrong_words_to_localstorage(wrong_words: list[tuple[str, str]]) -> None:
    payload = json.dumps([{"en": en, "zh": zh} for en, zh in wrong_words], ensure_ascii=False)
    encoded = _b64_encode_text(payload)

    components.html(
        f"""
        <script>
        (function () {{
          const KEY = "toefl_wrong_words";
          const EMPTY = "W10=";
          const pyData = {json.dumps(encoded)};
          const parentWin = window.parent;
          const url = new URL(parentWin.location.href);
          const qp = url.searchParams.get("wrong_words_data");

          if (pyData && pyData !== qp) {{
            try {{ localStorage.setItem(KEY, pyData); }} catch (e) {{}}
            url.searchParams.set("wrong_words_data", pyData);
            parentWin.location.replace(url.toString());
            return;
          }}

          const localData = localStorage.getItem(KEY) || EMPTY;
          if (localData !== qp) {{
            url.searchParams.set("wrong_words_data", localData);
            parentWin.location.replace(url.toString());
          }}
        }})();
        </script>
        """,
        height=0,
    )


def add_wrong_words(candidates: list[tuple[str, str]]) -> None:
    exist = {en for en, _ in st.session_state.wrong_words}
    for en, zh in candidates:
        if en not in exist:
            st.session_state.wrong_words.append((en, zh))
            exist.add(en)


def remove_wrong_words(correct_words: list[str]) -> None:
    remove_set = set(correct_words)
    st.session_state.wrong_words = [
        (en, zh) for en, zh in st.session_state.wrong_words if en not in remove_set
    ]


def reset_quiz() -> None:
    words = load_word_pairs()
    st.session_state.questions = random.sample(words, 10)
    st.session_state.started = False
    st.session_state.checked = False
    st.session_state.results = [None] * 10
    for i in range(10):
        st.session_state[f"answer_{i}"] = ""


def reset_wrong_quiz() -> None:
    if not st.session_state.wrong_words:
        st.session_state.wrong_questions = []
        st.session_state.wrong_started = False
        st.session_state.wrong_checked = False
        st.session_state.wrong_results = []
        return

    sample_size = min(10, len(st.session_state.wrong_words))
    st.session_state.wrong_questions = random.sample(st.session_state.wrong_words, sample_size)
    st.session_state.wrong_started = False
    st.session_state.wrong_checked = False
    st.session_state.wrong_results = [None] * sample_size
    for i in range(sample_size):
        st.session_state[f"wrong_answer_{i}"] = ""


if "questions" not in st.session_state:
    reset_quiz()

if "all_words" not in st.session_state:
    words = load_word_pairs()
    st.session_state.all_words = {en: zh for en, zh in words}

if "wrong_words" not in st.session_state:
    st.session_state.wrong_words = load_wrong_words_from_query(st.session_state.all_words)

if "wrong_questions" not in st.session_state:
    st.session_state.wrong_questions = []
if "wrong_started" not in st.session_state:
    st.session_state.wrong_started = False
if "wrong_checked" not in st.session_state:
    st.session_state.wrong_checked = False
if "wrong_results" not in st.session_state:
    st.session_state.wrong_results = []

sync_wrong_words_to_localstorage(st.session_state.wrong_words)


st.markdown('<div class="panel-card">', unsafe_allow_html=True)
st.markdown('<div class="title">托福单词默写</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">随机抽取 10 个单词，点击“开始默写”后进行听写。</div>', unsafe_allow_html=True)

btn_col1, btn_col2, _ = st.columns([1, 1, 6])
with btn_col1:
    if st.button("开始默写", use_container_width=True):
        st.session_state.started = True
        st.session_state.checked = False
        st.session_state.results = [None] * 10
with btn_col2:
    if st.button("换一组题", use_container_width=True):
        reset_quiz()
        st.rerun()

if st.session_state.started:
    if st.button("检查答案", type="primary", use_container_width=True):
        results = []
        new_wrong_words = []
        for i, (en, _zh) in enumerate(st.session_state.questions):
            user_answer = st.session_state.get(f"answer_{i}", "").strip().lower()
            correct = en.strip().lower()
            is_correct = user_answer == correct
            results.append(is_correct)
            if not is_correct:
                new_wrong_words.append(st.session_state.questions[i])
        st.session_state.results = results
        st.session_state.checked = True
        add_wrong_words(new_wrong_words)


col_en, col_zh, col_input = st.columns([2, 3, 3])
with col_en:
    st.markdown("### 英文单词")
with col_zh:
    st.markdown("### 中文翻译")
with col_input:
    st.markdown("### 你的答案")

for i, (en, zh) in enumerate(st.session_state.questions):
    col_en, col_zh, col_input = st.columns([2, 3, 3])

    with col_en:
        if not st.session_state.started:
            st.markdown(f'<div class="word-box">{en}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="word-box"> </div>', unsafe_allow_html=True)

    with col_zh:
        st.markdown(f'<div class="word-box">{zh}</div>', unsafe_allow_html=True)

    with col_input:
        st.text_input(
            label=f"word_{i+1}",
            key=f"answer_{i}",
            label_visibility="collapsed",
            placeholder="请输入英文单词",
        )

        if st.session_state.checked:
            if st.session_state.results[i]:
                st.markdown('<div class="ok">正确</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="bad">错误（正确答案：{en}）</div>', unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
st.markdown("---")
st.markdown('<div class="panel-card">', unsafe_allow_html=True)
st.markdown("## 错题本")
st.caption("这里会显示历史答错的单词，可单独重新练习。")

if not st.session_state.wrong_words:
    st.info("暂无错题，继续加油！")
else:
    for en, zh in st.session_state.wrong_words:
        st.markdown(f"- `{en}`：{zh}")

wrong_btn_col1, wrong_btn_col2, _ = st.columns([1, 1, 6])
with wrong_btn_col1:
    if st.button("错题本重新练习", use_container_width=True):
        reset_wrong_quiz()
        st.session_state.wrong_started = True
        st.session_state.wrong_checked = False

with wrong_btn_col2:
    if st.button("清空错题本", use_container_width=True):
        st.session_state.wrong_words = []
        reset_wrong_quiz()
        st.rerun()

if st.session_state.wrong_started and st.session_state.wrong_questions:
    if st.button("检查错题答案", type="primary", use_container_width=True):
        results = []
        now_correct_words = []
        for i, (en, _zh) in enumerate(st.session_state.wrong_questions):
            user_answer = st.session_state.get(f"wrong_answer_{i}", "").strip().lower()
            correct = en.strip().lower()
            is_correct = user_answer == correct
            results.append(is_correct)
            if is_correct:
                now_correct_words.append(en)

        st.session_state.wrong_results = results
        st.session_state.wrong_checked = True
        remove_wrong_words(now_correct_words)

    col_en, col_zh, col_input = st.columns([2, 3, 3])
    with col_en:
        st.markdown("### 英文单词")
    with col_zh:
        st.markdown("### 中文翻译")
    with col_input:
        st.markdown("### 你的答案")

    for i, (en, zh) in enumerate(st.session_state.wrong_questions):
        col_en, col_zh, col_input = st.columns([2, 3, 3])
        with col_en:
            st.markdown('<div class="word-box"> </div>', unsafe_allow_html=True)
        with col_zh:
            st.markdown(f'<div class="word-box">{zh}</div>', unsafe_allow_html=True)
        with col_input:
            st.text_input(
                label=f"wrong_word_{i+1}",
                key=f"wrong_answer_{i}",
                label_visibility="collapsed",
                placeholder="请输入英文单词",
            )
            if st.session_state.wrong_checked:
                if st.session_state.wrong_results[i]:
                    st.markdown('<div class="ok">正确（已从错题本移除）</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="bad">错误（正确答案：{en}）</div>', unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
