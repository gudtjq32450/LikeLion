import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUTPUT_FILE = ROOT / "프로젝트.txt"

# 제외할 폴더나 파일 확장자 (빌드 파일, 가상환경, 찌꺼기 파일 등)
EXCLUDE_DIRS = {".git", ".venv", "node_modules", "dist", "build", "__pycache__"}
EXCLUDE_EXTENSIONS = {".pyc", ".png", ".jpg", ".gif", ".ico", ".db", ".lock"}
EXCLUDE_FILES = {"프로젝트.txt", "최신화.py"}

def generate_smart_txt():
    content_list = []
    print("[*] 프로젝트 폴더 전체 스캔 중...")
    
    # 루트 폴더부터 하위 폴더까지 재귀적으로 탐색
    for file_path in sorted(ROOT.rglob("*")):
        if file_path.is_file():
            # 제외할 폴더 내부에 있는지 확인
            if any(part in EXCLUDE_DIRS for part in file_path.parts):
                continue
            # 제외할 파일 이름이거나 확장자인지 확인
            if file_path.name in EXCLUDE_FILES or file_path.suffix.lower() in EXCLUDE_EXTENSIONS:
                continue
                
            # 프로젝트 루트 기준 상대 경로 추출
            rel_path = file_path.relative_to(ROOT).as_posix()
            print(f"[포함] {rel_path}")
            
            try:
                code_text = file_path.read_text(encoding="utf-8")
            except Exception:
                try:
                    code_text = file_path.read_text(encoding="cp949", errors="ignore")
                except Exception:
                    continue
                    
            content_list.append(f"{rel_path}\n`````\n{code_text}\n`````\n")

    # 프로젝트.txt로 병합 저장
    OUTPUT_FILE.write_text("\n".join(content_list), encoding="utf-8")
    print(f"\n[성공] 새 파일이나 코드 추가 여부와 관계없이 '{OUTPUT_FILE.name}'이(가) 완벽히 최신화되었습니다!")

if __name__ == "__main__":
    generate_smart_txt()