def agent_steps():
    print("--- 步骤 1：思考中 ---")
    yield "我想去查天气"
    
    print("--- 步骤 2：行动中 ---")
    yield "正在调用天气接口"
    
    print("--- 步骤 3：结束 ---")
    yield "上海今天晴转多云"

steps = agent_steps()

if __name__ == "__main__":
    # 第一次唤醒
    print(next(steps)) 
    # 第二次唤醒
    print(next(steps))