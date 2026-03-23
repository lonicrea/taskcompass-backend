import json as json_lib
import os
import re

from dotenv import load_dotenv
from openai import OpenAI

from app.utils.traditional_chinese import to_traditional_data, to_traditional_text

load_dotenv()

DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"
DEFAULT_OPENAI_QUESTION_MODEL = "gpt-4o-mini"
DEFAULT_OPENAI_REPORT_MODEL = "gpt-4o-mini"


def get_default_api_key():
    """優先使用 OpenAI API Key，保留舊的 QWEN_API_KEY 作為相容退路。"""
    return os.getenv("OPENAI_API_KEY") or os.getenv("QWEN_API_KEY")


def get_default_base_url():
    """優先使用 OpenAI 官方端點，保留舊的 QWEN_BASE_URL 作為相容退路。"""
    return (
        os.getenv("OPENAI_BASE_URL")
        or os.getenv("QWEN_BASE_URL")
        or DEFAULT_OPENAI_BASE_URL
    )


def get_default_model(purpose="question"):
    """優先讀取 OPENAI_MODEL，若未設定則退回舊的 QWEN_MODEL。"""
    configured_model = os.getenv("OPENAI_MODEL") or os.getenv("QWEN_MODEL")
    if configured_model:
        return configured_model

    if purpose == "report":
        return DEFAULT_OPENAI_REPORT_MODEL
    return DEFAULT_OPENAI_QUESTION_MODEL


def create_client(api_key=None, base_url=None):
    return OpenAI(
        api_key=api_key or get_default_api_key(),
        base_url=base_url or get_default_base_url(),
    )


default_client = create_client()


def get_client(custom_api_key=None, custom_base_url=None):
    """取得 API 客戶端，支援自訂 OpenAI 相容端點。"""
    if custom_api_key or custom_base_url:
        return create_client(custom_api_key, custom_base_url)
    return default_client


def generate_questions(
    idea,
    questions_list=None,
    answers_list=None,
    feedback=None,
    custom_api_key=None,
    custom_base_url=None,
    custom_model=None,
):
    """根據使用者想法、歷史問答與回饋生成下一輪問題。"""
    client = get_client(custom_api_key, custom_base_url)
    model = custom_model or get_default_model("question")
    is_custom_api = bool(custom_api_key or custom_base_url or custom_model)

    has_qa_history = questions_list and len(questions_list) > 0 and feedback

    if has_qa_history:
        qa_pairs = []
        if answers_list and len(answers_list) > 0:
            min_len = min(len(questions_list), len(answers_list))
            for i in range(min_len):
                question_item = questions_list[i]
                answer_item = answers_list[i]
                question_text = (
                    question_item.get("text", "")
                    if isinstance(question_item, dict)
                    else str(question_item)
                )
                answer_text = (
                    answer_item.get("answer", "")
                    if isinstance(answer_item, dict)
                    else str(answer_item)
                )
                qa_pairs.append(f"問題：{question_text} | 回答：{answer_text}")

        qa_context = "\n".join(qa_pairs) if qa_pairs else "目前沒有已回答的問題"

        prompt = f"""
        # Role
        你是一位智慧任務對齊專家（Task Alignment Specialist）。你的目標是透過高品質提問，幫助使用者釐清模糊想法，明確最後要產出的交付物類型（如 PPT、程式、文章、企劃等）與核心要求。
        你的風格親切、專業，善於透過提問引導使用者思考，而不是像審問。
        # Goals
        1. **意圖識別**：透過提問確認使用者最終想要的交付物形式。
        2. **關鍵資訊補全**：針對該交付物需要的核心資訊（如受眾、風格、長度、技術棧等）持續追問。
        3. **動態題數**：依資訊缺失程度，生成 3-7 個高品質問題，不要為了湊數而提問。
        # Context
        使用者正在描述一個想法，你們正在進行多輪需求對齊對話。
        - 初始想法："{idea}"
        - 歷史問答紀錄："{qa_context}"
        - 使用者最新回饋："{feedback}"

        請基於以上所有資訊，提出 5-10 個有針對性的新問題，進一步明確需求。
        注意：不要重複已經問過的問題，應依據使用者回饋與既有答案提出更深入的新問題。
        所有問題內容請使用繁體中文輸出。
        問題類型可以包含選擇題、填空題與敘述題。
        其中最後一題必須為敘述題，讓使用者自由補充想法。
        請以 JSON 格式回傳問題列表，每個問題包含以下欄位：
        - id: 問題唯一識別
        - text: 問題內容
        - type: 問題類型 (choice, fill_blank, narrative)
        - options: 選項列表（僅選擇題需要）
        """
    elif feedback:
        prompt = f"""
        # Role
        你是一位智慧任務對齊專家（Task Alignment Specialist）。你的目標是透過高品質提問，幫助使用者釐清模糊想法，明確最後要產出的交付物類型（如 PPT、程式、文章、企劃等）與核心要求。
        你的風格親切、專業，善於透過提問引導使用者思考，而不是像審問。
        # Goals
        1. **意圖識別**：透過提問確認使用者最終想要的交付物形式。
        2. **關鍵資訊補全**：針對該交付物需要的核心資訊（如受眾、風格、長度、技術棧等）持續追問。
        3. **動態題數**：依資訊缺失程度，生成 3-7 個高品質問題，不要為了湊數而提問。
        # Context
        使用者正在描述一個想法，你們正在進行多輪需求對齊對話。
        - 初始想法："{idea}"
        - 使用者最新回饋："{feedback}"

        請基於以上資訊，提出 5-10 個有針對性的問題，進一步明確需求。
        所有問題內容請使用繁體中文輸出。
        問題類型可以包含選擇題、填空題與敘述題。
        其中最後一題必須為敘述題，讓使用者自由補充想法。
        請以 JSON 格式回傳問題列表，每個問題包含以下欄位：
        - id: 問題唯一識別
        - text: 問題內容
        - type: 問題類型 (choice, fill_blank, narrative)
        - options: 選項列表（僅選擇題需要）
        """
    else:
        prompt = f"""
        # Role
        你是一位智慧任務對齊專家（Task Alignment Specialist）。你的目標是透過高品質提問，幫助使用者釐清模糊想法，明確最後要產出的交付物類型（如 PPT、程式、文章、企劃等）與核心要求。
        你的風格親切、專業，善於透過提問引導使用者思考，而不是像審問。
        # Goals
        1. **意圖識別**：透過提問確認使用者最終想要的交付物形式。
        2. **關鍵資訊補全**：針對該交付物需要的核心資訊（如受眾、風格、長度、技術棧等）持續追問。
        3. **動態題數**：依資訊缺失程度，生成 3-7 個高品質問題，不要為了湊數而提問。
        # Context
        使用者正在描述一個想法，你們正在進行多輪需求對齊對話。
        - 初始想法："{idea}"

        請提出 5-10 個有針對性的問題來明確需求。
        所有問題內容請使用繁體中文輸出。
        問題類型可以包含選擇題、填空題與敘述題。
        其中最後一題必須為敘述題，讓使用者自由補充想法。
        請以 JSON 格式回傳問題列表，每個問題包含以下欄位：
        - id: 問題唯一識別
        - text: 問題內容
        - type: 問題類型 (choice, fill_blank, narrative)
        - options: 選項列表（僅選擇題需要）
        """

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=4000,
        )

        content = response.choices[0].message.content.strip()

        if not is_custom_api and hasattr(response, "usage") and response.usage:
            from app.models.session import SessionManager

            SessionManager.add_token_usage(response.usage.total_tokens)

        json_match = re.search(r"\[.*\]", content, re.DOTALL)
        if json_match:
            parsed_questions = json_lib.loads(json_match.group())
            return to_traditional_data(parsed_questions)

        return [
            {
                "id": "fallback-1",
                "text": "(AI 回傳失敗，預設問題)請詳細描述您的任務目標與預期功能。",
                "type": "narrative",
            },
            {
                "id": "fallback-2",
                "text": "(AI 回傳失敗，預設問題)您的目標使用者族群是誰？",
                "type": "narrative",
            },
        ]

    except Exception as exc:
        print(f"Error calling OpenAI API: {str(exc)}")
        return [
            {
                "id": "error-1",
                "text": "(AI 回傳失敗，預設問題)請詳細描述您的想法與期待成果。",
                "type": "narrative",
            }
        ]


def process_answers_to_doc(
    idea,
    questions,
    answers,
    custom_api_key=None,
    custom_base_url=None,
    custom_model=None,
):
    """處理使用者答案並生成階段性報告。"""
    client = get_client(custom_api_key, custom_base_url)
    model = custom_model or get_default_model("report")
    is_custom_api = bool(custom_api_key or custom_base_url or custom_model)

    qa_pairs = []
    for i, answer in enumerate(answers):
        if i < len(questions):
            auto_infer = bool(answer.get("auto_infer")) if isinstance(answer, dict) else False
            qa_pairs.append(
                {
                    "question": questions[i]["text"],
                    "answer": answer.get("answer", ""),
                    "question_type": questions[i].get("type", "narrative"),
                    "auto_infer": auto_infer,
                }
            )

    qa_input_text = chr(10).join(
        [
            (
                f"問題：{pair['question']} | 回答狀態：使用系統預設推測，請根據上下文與常見需求保守補足"
                if pair["auto_infer"]
                else f"問題：{pair['question']} | 回答：{pair['answer']}"
            )
            for pair in qa_pairs
        ]
    )

    prompt = f"""
    # Role
    你是一位全能型首席助理（Chief of Staff）。你的任務是把使用者模糊的初始想法與多輪問答記錄，整合成一份《任務執行簡報》。
    這份簡報將傳遞給下游 AI（可能是 PPT 生成器、寫作助手、程式引擎或設計工具），因此必須清晰、無歧義，且要適配最終交付物類型。
    # Input Data
    - 原始想法：{idea}
    - 問答對：
    {qa_input_text}

    # Goals
    你的核心目標是準確判斷使用者最終想要的交付物類型，例如 PPT、文章、程式、企劃或表格，並將所有問答資訊收斂成一份可直接交付下游 AI 使用的任務執行簡報。若對話內容存在前後差異，請以最新的問答答案為準。你需要依據交付物類型動態調整報告重點，例如面對 PPT 時更重視大綱與視覺風格，面對程式開發時更重視功能邏輯與技術棧，面對文章時更重視語氣、結構與敘事方式。同時，對於尚未被明確確認、但又會影響執行結果的重要資訊，你必須清楚標示那是基於上下文推得的合理假設，方便下游 AI 後續使用或再確認。
    若某些問題被標記為「使用系統預設推測」，代表使用者選擇不手動填寫，授權你根據原始想法、其他已回答內容與同類任務的常見需求，做出保守、合理且自洽的推測來補足觀點。這些推測可以進入最終簡報內容，但你必須在「約束與假設」章節清楚說明哪些內容屬於系統代為推測，而非使用者明確表述。

    # Constraints
    請全程使用繁體中文撰寫，語氣保持專業、清晰、自然且具有執行指令感。輸出格式仍使用標準 Markdown，但不要使用條列式、編號清單或表格作為主要表達方式，而是改用完整的人類語言自然段落來呈現內容。每一段都要有充分資訊量，不能因為改成自然段就變得空泛或簡略。你也必須依任務類型調整敘述方式，不要把軟體開發術語硬套到不相干的任務上，例如文章寫作任務就不應出現資料庫設計之類的內容。所有未確認資訊都必須如實標註，不得臆測或捏造。

    # Workflow
    你需要先從對話中判斷最終交付物的類型，再提取任務的核心目標、目標受眾、內容重點、邏輯結構、風格要求、格式規範、限制條件與可能缺漏。接著請依照下方定義的輸出結構，把這些資訊重組為一份易讀、連貫、可直接拿去執行的任務執行簡報，並在最後補上對下游 AI 的具體工作建議。

    # Output Structure (必須嚴格遵守)
    請保留五個章節標題，依序輸出「## 1. 任務概覽 (Task Overview)」、「## 2. 內容與邏輯 (Content & Logic)」、「## 3. 風格與規範 (Style & Guidelines)」、「## 4. 約束與假設 (Constraints & Assumptions)」以及「## 5. 給下游 AI 的指令 (Instructions for Downstream AI)」。但在每個章節之下，內容必須以自然段落方式展開，不要再拆成條列項目。

    在「任務概覽」中，請用一到兩段自然文字清楚說明任務類型、核心目標與目標受眾，讓讀者一開始就能理解這份交付物到底要解決什麼問題、會給誰看、以及最終成果應該長成什麼樣子。

    在「內容與邏輯」中，請用完整段落說明這份交付物應包含哪些核心模組、大綱或段落，哪些資訊點是不可缺少的，以及整體內容應如何鋪陳與推進。這一節要具體到足以讓執行者直接照著規劃內容，而不是只有抽象概念。

    在「風格與規範」中，請以自然敘述整合語氣風格、視覺或格式要求，以及長度與規模等期待，例如是否偏商務、偏敘事、偏技術，是否需要 Markdown、簡報頁數、文章字數、程式語言版本或其他明確規格。

    在「約束與假設」中，請寫成連貫段落，先交代使用者已明確提出的限制、禁忌或硬性要求，再補充那些尚未明確確認、但為了讓任務可以繼續推進而暫時採用的合理假設，並明白指出這些假設需要下游 AI 留意。

    在「給下游 AI 的指令」中，請以一到兩段自然語言，直接對後續執行的 AI 說明應採取的工作方式、優先順序、執行重點與品質標準。這部分要具體、可操作，而且要根據任務類型量身調整，例如若是 PPT 就描述頁面安排與表達重點，若是程式就描述實作原則、註解、錯誤處理與結構要求。

    # Initialization
    請基於輸入資料，生成符合上述要求的《任務執行簡報》。整份內容必須詳細、自然、完整，並以繁體中文輸出。
    """

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=4000,
        )

        report = to_traditional_text(response.choices[0].message.content.strip())

        if not is_custom_api and hasattr(response, "usage") and response.usage:
            from app.models.session import SessionManager

            SessionManager.add_token_usage(response.usage.total_tokens)

        return report

    except Exception as exc:
        print(f"Error processing answers to doc: {str(exc)}")
        return to_traditional_text(f"處理答案時發生錯誤：{str(exc)}")
