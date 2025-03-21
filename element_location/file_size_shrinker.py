from bs4 import BeautifulSoup

def remove_svg_tags(html_content):
    """
    移除 HTML 内容中的所有 <svg> 标签
    返回清理后的 HTML 字符串
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 移除所有 svg 标签及其内容
    for svg_tag in soup.find_all('svg'):
        svg_tag.decompose()
    
    return str(soup)

if __name__ == "__main__":
    import os
    import sys
    
    def process_html_file(file_path):
        """处理指定HTML文件并保存清理结果"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            cleaned = remove_svg_tags(content)
            
            # 保存清理后的文件
            new_path = os.path.splitext(file_path)[0] + "_cleaned.html"
            with open(new_path, 'w', encoding='utf-8') as f:
                f.write(cleaned)
            
            print(f"成功处理文件: {os.path.basename(file_path)}")
            print(f"清理后文件已保存至: {new_path}")
            print(f"原始大小: {len(content)} bytes → 清理后大小: {len(cleaned)} bytes")
            
        except Exception as e:
            print(f"处理文件时出错: {str(e)}")

    # 直接处理 shouye.html（需要文件存在）
    if os.path.exists("shouye.html"):
        process_html_file("shouye.html")
    else:
        print("未找到 shouye.html，请确保文件存在于当前目录")