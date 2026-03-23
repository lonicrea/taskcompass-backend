from flask import jsonify, request

from app.models.session import SessionManager
from app.routes import bp
from app.utils.openai_api import generate_questions, process_answers_to_doc
from app.utils.token_limit import check_token_limit
from app.utils.traditional_chinese import to_traditional_data


@bp.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'})


@bp.route('/api/generate-questions', methods=['POST'])
@check_token_limit
def api_generate_questions():
    """根據使用者輸入的想法生成問題。"""
    try:
        data = request.get_json()
        idea = data.get('idea', '')

        # 取得自訂 API 配置
        custom_config = data.get('custom_api') or {}
        custom_api_key = custom_config.get('api_key')
        custom_base_url = custom_config.get('base_url')
        custom_model = custom_config.get('model')

        if not idea:
            return jsonify({'error': '想法不能為空'}), 400

        # 生成唯一工作階段 ID
        session_id = SessionManager.create_session(idea)

        # 呼叫 OpenAI API 生成問題
        questions = generate_questions(
            idea,
            custom_api_key=custom_api_key,
            custom_base_url=custom_base_url,
            custom_model=custom_model,
        )

        # 儲存問題到工作階段
        SessionManager.save_questions(session_id, questions)

        return jsonify({
            'session_id': session_id,
            'questions': to_traditional_data(questions)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/api/submit-answers', methods=['POST'])
@check_token_limit
def api_submit_answers():
    """提交問題答案並生成階段性報告。"""
    try:
        data = request.get_json()
        session_id = data.get('session_id', '')
        answers = data.get('answers', [])

        # 取得自訂 API 配置
        custom_config = data.get('custom_api') or {}
        custom_api_key = custom_config.get('api_key')
        custom_base_url = custom_config.get('base_url')
        custom_model = custom_config.get('model')

        if not session_id or not answers:
            return jsonify({'error': '工作階段 ID 與答案不能為空'}), 400

        # 取得工作階段資訊
        session_data = SessionManager.get_session(session_id)
        if not session_data:
            return jsonify({'error': '無效的工作階段 ID'}), 400

        # 使用所有歷史問題和答案（包含之前輪次）
        all_questions = session_data['questions']
        all_answers = session_data['answers'] + answers

        # 基於所有歷史問答生成階段性報告
        report = process_answers_to_doc(
            session_data['idea'],
            all_questions,
            all_answers,
            custom_api_key=custom_api_key,
            custom_base_url=custom_base_url,
            custom_model=custom_model,
        )

        # 更新工作階段資料
        SessionManager.update_session_with_answers(session_id, answers, report)

        return jsonify({
            'session_id': session_id,
            'report': to_traditional_data(report)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/api/generate-pdf', methods=['POST'])
def api_generate_pdf():
    """生成最終 PDF 文件。"""
    try:
        data = request.get_json()
        session_id = data.get('session_id', '')

        if not session_id:
            return jsonify({'error': '工作階段 ID 不能為空'}), 400

        # 取得工作階段資訊
        session_data = SessionManager.get_session(session_id)
        if not session_data:
            return jsonify({'error': '無效的工作階段 ID'}), 400

        # 生成 PDF 文件
        pdf_path = SessionManager.generate_pdf_report(session_id)

        return jsonify({
            'session_id': session_id,
            'pdf_url': f'/api/download-pdf/{session_id}'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/api/session/<session_id>', methods=['GET'])
def api_get_session_data(session_id):
    """取得工作階段資料（包含問題）。"""
    try:
        # 取得工作階段資訊
        session_data = SessionManager.get_session(session_id)
        if not session_data:
            return jsonify({'error': '無效的工作階段 ID'}), 400

        return jsonify({
            'session_id': session_id,
            'idea': to_traditional_data(session_data['idea']),
            'questions': to_traditional_data(session_data['questions']),
            'answers': session_data['answers'],
            'reports': to_traditional_data(session_data['reports'])
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/api/session/<session_id>/rounds', methods=['GET'])
def api_get_session_rounds(session_id):
    """取得工作階段輪次資料（保持問答對應關係）。"""
    try:
        # 取得工作階段資訊
        session_data = SessionManager.get_session(session_id)
        if not session_data:
            return jsonify({'error': '無效的工作階段 ID'}), 404

        # 取得輪次資料
        rounds = SessionManager.get_rounds(session_id)

        return jsonify({
            'session_id': session_id,
            'rounds': to_traditional_data(rounds)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/api/continue-with-feedback', methods=['POST'])
@check_token_limit
def api_continue_with_feedback():
    """使用者提供回饋後繼續生成新問題。"""
    try:
        data = request.get_json()
        session_id = data.get('session_id', '')
        feedback = data.get('feedback', '')

        # 取得自訂 API 配置
        custom_config = data.get('custom_api') or {}
        custom_api_key = custom_config.get('api_key')
        custom_base_url = custom_config.get('base_url')
        custom_model = custom_config.get('model')

        if not session_id or not feedback:
            return jsonify({'error': '工作階段 ID 與回饋不能為空'}), 400

        # 取得工作階段資訊
        session_data = SessionManager.get_session(session_id)
        if not session_data:
            return jsonify({'error': '無效的工作階段 ID'}), 400

        # 基於原始想法、既有問答與使用者回饋生成新問題
        new_questions = generate_questions(
            session_data['idea'],
            session_data['questions'],
            session_data['answers'],
            feedback,
            custom_api_key=custom_api_key,
            custom_base_url=custom_base_url,
            custom_model=custom_model,
        )

        # 取代工作階段中的問題（而不是追加）
        SessionManager.replace_questions(session_id, new_questions)

        return jsonify({
            'session_id': session_id,
            'questions': to_traditional_data(new_questions)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/api/download-pdf/<session_id>', methods=['GET'])
def api_download_pdf(session_id):
    """下載報告（目前為 Markdown 格式）。"""
    try:
        # 取得工作階段資訊
        session_data = SessionManager.get_session(session_id)
        if not session_data:
            return "找不到工作階段", 404

        # 如果沒有文件，生成一份
        if not session_data.get('final_doc'):
            from flask import send_file
            import os
            # 建立輸出目錄
            output_dir = SessionManager.OUTPUT_DIR
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # 生成 Markdown 文件
            filename = f"requirement_document_{session_id[:8]}.md"
            filepath = os.path.join(output_dir, filename)

            from app.utils.markdown_generator import generate_markdown
            generate_markdown(session_data, filepath)

            # 在資料庫中記錄文件路徑
            import sqlite3
            conn = sqlite3.connect(SessionManager.DB_PATH)
            cursor = conn.cursor()

            from datetime import datetime
            updated_at = datetime.now().isoformat()
            cursor.execute("""
                UPDATE sessions
                SET final_doc_path = ?, updated_at = ?
                WHERE id = ?
            """, (filepath, updated_at, session_id))

            conn.commit()
            conn.close()
        else:
            filepath = session_data['final_doc']

        from flask import send_file
        import os
        if not os.path.exists(filepath):
            return "檔案不存在", 404

        # 确定正确的文件扩展名
        file_ext = os.path.splitext(filepath)[1]
        download_name = f"requirement_document_{session_id[:8]}{file_ext}"

        return send_file(filepath, as_attachment=True, download_name=download_name)
    except Exception as e:
        return str(e), 500


@bp.route('/api/session/<session_id>', methods=['DELETE'])
def api_delete_session(session_id):
    """
    删除会话
    """
    try:
        # 获取会话信息
        session_data = SessionManager.get_session(session_id)
        if not session_data:
            return jsonify({'error': '無效的工作階段 ID'}), 404

        # 删除会话
        SessionManager.delete_session(session_id)

        return jsonify({
            'message': '刪除成功'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
