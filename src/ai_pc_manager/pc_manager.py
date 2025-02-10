import json
import logging
from typing import List, Dict
import aiohttp

from .display import show_waiting_spinner
from .command import execute_command
from .prompts import SYSTEM_PROMPT
try:
    from ._persional_info import PersonalInfo
except ImportError:
    class PersonalInfoStub:
        @classmethod
        def get_all_info(cls):
            return ""
    PersonalInfo = PersonalInfoStub

logger = logging.getLogger(__name__)

class PCManager:
    """PC管理员智能体核心类"""

    FILED_RETRY_TIMES = 3

    def __init__(self):
        self.bash_url = "http://localhost:8000/api/v1/chat/completions" # 基于ai-request-service的AI请求服务
        self.conversation_history: List[Dict] = []
        self._system_message = {
            "role": "system",
            "content": f"{SYSTEM_PROMPT}\n{PersonalInfo.get_all_info()}"  # 添加个人信息
        }

    def _clear_history(self):
        """清空对话历史"""
        self.conversation_history.clear()

    def _handle_compression(self, ai_response: str) -> bool:
        """处理对话压缩，返回是否进行了压缩"""
        if "COMPRESS_START:" in ai_response and "COMPRESS_END:" in ai_response:
            start_idx = ai_response.find("COMPRESS_START:") + len("COMPRESS_START:")
            end_idx = ai_response.find("COMPRESS_END:")
            compressed_content = ai_response[start_idx:end_idx].strip()

            # 保留用户原始需求
            user_input = self.conversation_history[0]
            # 清空历史并添加压缩后的内容
            self._clear_history()
            if compressed_content:
                print("压缩后的内容：")
                print(compressed_content)
                self.conversation_history.append(user_input)
                self.conversation_history.append({
                    "role": "assistant",
                    "content": "以下是精简的对话历史：\n" + compressed_content
                })
            return True
        return False

    async def get_ai_response(self, messages: List[Dict]) -> str:
        """从AI服务获取响应"""
        try:
            with show_waiting_spinner() as spinner:
                async with aiohttp.ClientSession() as session:
                    payload = {
                        "messages": messages,
                        "temperature": 0.5,
                        "stream": False,
                        "providers": ["siliconflow-deepseek-r1-pro", "siliconflow-deepseek-v3"]
                    }

                    async with session.post(self.bash_url, json=payload) as response:
                        result = await response.json()
                        if 'error' in result:
                            raise Exception(f"API错误: {result['error']}")
                        # 获取提供者信息并传递给spinner
                        provider = result.get("provider", None)
                        if spinner:
                            spinner.set_provider(provider)
                        return result['choices'][0]['message']['content']
        except Exception as e:
            logger.error(f"AI请求失败: {str(e)}")
            raise

    async def process_request(self, user_input: str) -> str:
        try:
            """处理用户请求"""
            self.conversation_history.append({
                "role": "user",
                "content": user_input
            })

            failed_times = 0

            while True:
                messages = [self._system_message] + self.conversation_history

                ai_response = await self.get_ai_response(messages)

                # 处理对话压缩
                if self._handle_compression(ai_response):
                    continue

                self.conversation_history.append({
                    "role": "assistant",
                    "content": ai_response
                })
                # 处理命令执行
                if "COMMAND:" in ai_response:
                    command_start = ai_response.find("COMMAND:") + 8
                    # 查找下一个换行符的位置
                    def _find_enter_position(start_index):
                        return ai_response.find("\n", start_index) if "\n" in ai_response[start_index:] else len(ai_response)
                    command_end = _find_enter_position(command_start)
                    while ai_response[command_end - 1] == "\\":
                        command_end = _find_enter_position(command_end + 1)
                    command = ai_response[command_start:command_end].strip()

                    output, return_code = execute_command(command)
                    self.conversation_history.append({
                        "role": "user",
                        "content": f"一轮对话仅执行一条命令：\n{command}\n" + \
                            f"命令执行结果（返回码={return_code}）：\n{output}\n" + \
                            ("\n提醒：请确保每个单独的命令结果符合期待再进行后续的操作，而不要盲目的使用管道连接多个命令！" if return_code != 0 else "")
                    })
                    continue

                def _handle_complete():
                    response = "\n=============================\n".join([message["content"] for message in self.conversation_history])
                    self._clear_history()  # 任务结束后清空历史
                    return response

                # 处理任务完成或失败
                if "COMPLETE:" in ai_response:
                    return _handle_complete()
                elif "FAILED:" in ai_response:
                    failed_times += 1
                    if failed_times >= self.FILED_RETRY_TIMES:
                        return _handle_complete()
                    else:
                        self.conversation_history.append({
                            "role": "user",
                            "content": f"请不要轻易放弃，请检查命令的返回是否符合期待，请检查请求的url是否正确等等。或再尝试其他方法。"
                        })
                        continue
                else:
                    self.conversation_history.append({
                        "role": "user",
                        "content": f"AI响应格式错误，请严格遵循system提示词的响应格式规则并重试"
                    })
                    continue
        except Exception as e:
            logger.error(f"处理请求失败: {str(e)}")
            raise e
        finally:
            self._clear_history()

    async def __test(self):
        """测试"""
        self.conversation_history.append({
            "role": "user",
            "content": "你好"
        })

        messages = [{"role": "system", "content": "这是一个关于api对于多轮对话中的角色识别的测试。"},
                    {"role": "user", "content": "1"},
                    {"role": "assistant", "content": "2"},
                    {"role": "user", "content": "3"},
                    {"role": "assistant", "content": "4"},
                    {"role": "user", "content": "5"},
                    {"role": "assistant", "content": "6"},
                    {"role": "user", "content": "请识别出对话中的角色，并返回角色的名称和对话内容。"},
                    ]

        ai_response = await self.get_ai_response(messages)
        print(ai_response)
