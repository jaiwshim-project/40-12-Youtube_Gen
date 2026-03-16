"""클립보드 복사 헬퍼"""

def copy_to_clipboard(text: str) -> bool:
    try:
        import pyperclip
        pyperclip.copy(text)
        return True
    except ImportError:
        try:
            import subprocess
            subprocess.run(['clip'], input=text.encode('utf-8'), check=True)
            return True
        except Exception:
            return False

def get_first_prompt(prompts_text: str) -> str:
    parts = [p.strip() for p in prompts_text.split("---") if p.strip()]
    return parts[0] if parts else ""
