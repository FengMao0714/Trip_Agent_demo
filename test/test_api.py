import os
from dotenv import load_dotenv
from openai import OpenAI

# 1. 加载你的 .env 保险箱
load_dotenv()

# 2. 初始化客户端 (它会自动读取 .env 里的 KEY 和 BASE_URL)
client = OpenAI()

print("正在连接超算互联网 API，请稍候...")

try:
    # 3. 发送测试消息
    response = client.chat.completions.create(
        model="MiniMax-M2.5",  # <--- 注意这里！修改成对应的模型名
        messages=[
            {"role": "user", "content": "你好，请问你是哪个大模型？请用一句话回答。"}
        ],
        temperature=0.7
    )
    
    # 4. 打印回复
    print("\n✅ 连接成功！模型的回复是：")
    print(response.choices[0].message.content)

except Exception as e:
    print(f"\n❌ 连接失败，报错信息：{e}")