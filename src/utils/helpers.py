def clean_title(title: str) -> str:
    from bs4 import BeautifulSoup
    """清理标题中的 HTML 标签和多余字符"""
    if not title:
        return ""
    soup = BeautifulSoup(title, 'html.parser')
    return soup.get_text().strip()

def normalize_title(title: str) -> str:
    import re
    """标准化标题，移除干扰字符"""
    if not title:
        return ""
    return re.sub(r'[^\w]', '', title).lower()  # 只保留字母、数字和下划线


    
