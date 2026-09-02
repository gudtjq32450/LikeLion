import os
from pathlib import Path

# 프로젝트 루트 디렉토리
ROOT = Path(__file__).resolve().parent
OUTPUT_FILE = ROOT / "프로젝트.txt"

# 취합할 파일들의 상대 경로 목록 (최신 모듈화 구조 반영)
TARGET_FILES = [
    # 1. Frontend Config & HTML
    "frontend/vite.config.js",
    "frontend/package.json",
    "frontend/index.html",
    "frontend/src/App.css",
    
    # 2. Frontend Components (분할된 최신 구조)
    "frontend/src/utils/icons.jsx",
    "frontend/src/components/Header.jsx",
    "frontend/src/components/AuthModal.jsx",
    "frontend/src/components/ChildPage.jsx",
    "frontend/src/components/ParentPage.jsx",
    "frontend/src/components/LibraryPage.jsx",
    "frontend/src/App.jsx",
    
    # 3. Backend Core & Database
    "backend/database.py",
    "backend/models.py",
    "backend/auth.py",
    "backend/main.py",
    "backend/.env",
    
    # 4. Backend Schemas
    "backend/schemas/auth.py",
    "backend/schemas/family.py",
    "backend/schemas/question.py",
    "backend/schemas/answer.py",
    
    # 5. Backend Data & Services
    "backend/data/question_bank.py",
    "backend/services/openai_client.py",
    "backend/services/question_service.py",
    "backend/services/answer_service.py",
    
    # 6. Backend Routers
    "backend/routers/system.py",
    "backend/routers/auth.py",
    "backend/routers/families.py",
    "backend/routers/questions.py",
    "backend/routers/answers.py",
    
    # 7. Runner Scripts
    "START.bat",
]

def generate_project_txt():
    content_list = []
    
    for file_path_str in TARGET_FILES:
        file_path = ROOT / file_path_str
        if file_path.exists():
            print(f"[포함] {file_path_str}")
            try:
                code_text = file_path.read_text(encoding="utf-8")
            except Exception as e:
                print(f"[경고] 인코딩 오류 발생 ({file_path_str}): {e}")
                code_text = file_path.read_text(encoding="cp949", errors="ignore")
                
            content_list.append(f"{file_path_str}\n`````\n{code_text}\n`````\n")
        else:
            print(f"[누락/없음] {file_path_str} (건너뜁니다)")

    # 프로젝트.txt로 병합 저장
    OUTPUT_FILE.write_text("\n".join(content_list), encoding="utf-8")
    print(f"\n[성공] 모든 최신 코드가 '{OUTPUT_FILE.name}' 파일에 성공적으로 취합되었습니다!")

if __name__ == "__main__":
    generate_project_txt()