import logging
import subprocess
from typing import Tuple

from .display import print_command_execution

logger = logging.getLogger(__name__)

def truncate_output(output: str, max_chars: int = 1024) -> str:
    """
    截断过长的输出，只保留开头部分。
    - 保留至少max_chars个字符
    - 保持行的完整性，除非单行长度超过2倍max_chars
    - 在截断处显示省略的字符数
    """
    if len(output) <= max_chars:
        return output

    lines = output.splitlines()
    head_lines = []
    head_length = 0

    # 处理头部
    for line in lines:
        if len(line) > max_chars * 2:
            # 如果单行过长，直接截断
            head_lines.append(f"{line[:max_chars]}...")
            head_length += max_chars + 3
            break
        else:
            new_length = head_length + len(line) + 1  # +1 是换行符
            if new_length > max_chars and head_length > 0:
                break
            head_lines.append(line)
            head_length = new_length

    # 计算省略的字符数
    total_length = len(output)
    shown_length = sum(len(line) for line in head_lines)
    omitted_chars = total_length - shown_length

    # 生成提示信息
    if omitted_chars > 0:
        prompt_too_long = f"\n... (后续还有{omitted_chars}个字符未显示，如有必要请使用适当的命令分段查看) ..."
        return "\n".join(head_lines) + prompt_too_long

    return "\n".join(head_lines)


def execute_command(command: str) -> Tuple[str, int]:
    """
    执行bash命令
    返回: (输出内容, 返回码)
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True
        )
        output = result.stdout if result.stdout else result.stderr
        truncated_output = truncate_output(output)

        # 打印命令执行过程
        print_command_execution(command, truncated_output, result.returncode)

        return truncated_output, result.returncode
    except Exception as e:
        error_msg = f"执行命令时出错: {str(e)}"
        logger.error(error_msg)

        # 打印错误信息
        print_command_execution(command, error_msg, 1)

        return error_msg, 1