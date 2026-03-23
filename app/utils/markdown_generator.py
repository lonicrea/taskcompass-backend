def generate_markdown(session_data, filepath):
    """生成Markdown格式的需求文档"""
    def format_answer_text(answer):
        if isinstance(answer, dict) and answer.get('auto_infer'):
            return '已使用預設推測，由 AI 依上下文補足'
        return answer.get('answer', '') if isinstance(answer, dict) else str(answer)

    with open(filepath, 'w', encoding='utf-8') as f:
        # 写入标题
        f.write("# 任務需求簡報\n\n")
        
        # 写入原始想法
        f.write("## 1. 初始想法\n\n")
        idea_text = session_data.get('idea', '未提供初始想法')
        f.write(f"{idea_text}\n\n")
        
        # 写入问答内容（只有在有数据时才添加）
        if session_data.get('questions') and session_data.get('answers'):
            f.write("## 2. 需求澄清問答\n\n")
            
            # 确保问题和答案数量匹配
            min_len = min(len(session_data['questions']), len(session_data['answers']))
            for i in range(min_len):
                q = session_data['questions'][i]
                a = session_data['answers'][i]
                
                question_text = q.get('text', '') if isinstance(q, dict) else str(q)
                answer_text = format_answer_text(a)
                
                f.write(f"**Q{i+1}: {question_text}**\n")
                f.write(f"A{i+1}: {answer_text}\n\n")
        
        # 写入分析报告
        if session_data.get('reports'):
            f.write("## 3. 階段分析報告\n\n")
            
            for i, report in enumerate(session_data['reports'], 1):
                f.write(f"### 第 {i} 次分析\n")
                f.write(f"{report}\n\n")
        
        # 如果没有任何内容，添加默认内容
        if not session_data.get('idea') and not session_data.get('questions') and not session_data.get('reports'):
            f.write("目前沒有內容\n")
