from pathlib import Path
from openai import OpenAI
import json
from config.config import GUIJI_API_KEY, GUIJI_BASE_URL

def analyze_html_for_testing(html_file_path='page_content.html', ele_loc_file='eleLoc.json'):
    client = OpenAI(
        api_key=GUIJI_API_KEY,
        base_url=GUIJI_BASE_URL,
    )

    try:
        # 修正 purpose 参数为硅基流动要求的合法值
        file_object = client.files.create(
            file=Path(html_file_path),
            purpose="auto-test"  # 硅基流动支持的参数值
        )
        file_content = client.files.content(file_id=file_object.id).text

        messages = [
            {
                "role": "system",
                "content": """你是一个资深自动化测试工程师，请根据网页内容生成规范的 JSON 数据：
                        1. 分析页面核心功能模块
                        2. 识别所有用户交互元素（如按钮、输入框、链接等）及其用途，注意必须仅包含真实存在的交互元素
                        3. 为每个交互元素推荐最优定位方式（按优先级排列），定位方式要保证唯一且稳定
                        4. 说明推荐理由

                        输出要求：
                        - 使用规范的 JSON 格式
                        - 包含元素描述、定位策略、优先级和理由
                        - 按模块进行分类组织

                        注意：仅输出 JSON 数据，无需任何其他解释或文字"""
            },
            {
                "role": "system",
                "content": file_content,
            },
            {"role": "user", "content": "根据我提供的 html 文件来分析我进行自动化测试需要的元素及其最优定位方式"},
        ]


        completion = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1",
            messages=messages,
            temperature=0.7,          # 调低temperature参数
        )

        response_content = completion.choices[0].message.content

        try:
            # 解析 JSON 数据
            data = json.loads(response_content)
            # 将数据保存到指定文件名的文件
            with open(ele_loc_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"数据已成功保存到 {ele_loc_file} 文件。")
            return data
        except json.JSONDecodeError as e:
            print(f"提取到的 content 内容：\n{response_content}")
            print(f"JSON 解析错误: {e}")
            return None
    except FileNotFoundError:
        print(f"未找到文件: {html_file_path}")
        return None


if __name__ == "__main__":
    # 可以在这里修改需要分析的 HTML 文件和保存文件名
    analyze_html_for_testing(html_file_path='shouye.html', ele_loc_file='shouye.json')