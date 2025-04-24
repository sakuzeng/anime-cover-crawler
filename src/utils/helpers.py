# helpers.py

def format_anime_title(title: str) -> str:
    """格式化动漫标题，去除多余空格并转换为小写"""
    return title.strip().lower()

def extract_image_url(html_content: str) -> str:
    """从HTML内容中提取图片URL"""
    # 这里可以使用BeautifulSoup等库来解析HTML并提取图片URL
    pass

def save_image(image_url: str, save_path: str) -> None:
    """保存图片到指定路径"""
    import requests
    response = requests.get(image_url)
    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            f.write(response.content)
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