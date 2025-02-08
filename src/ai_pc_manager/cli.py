import asyncio
from .pc_manager import PCManager

def main():
    """命令行入口点"""
    asyncio.run(async_main())

async def async_main():
    pc_manager = PCManager()

    print("欢迎使用PC管理员智能体！输入 'exit' 退出。")
    while True:
        try:
            user_input = input("\n请输入您的需求: ")
            if user_input.lower() == 'exit':
                break

            response = await pc_manager.process_request(user_input)
            print("\nAI响应:", response)
        except KeyboardInterrupt:
            print("\n程序已终止")
            break
        except Exception as e:
            print(f"\n发生错误: {str(e)}")

if __name__ == "__main__":
    main()