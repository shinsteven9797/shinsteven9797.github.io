import os
import sys
import re
import shutil
import subprocess
import io
from datetime import datetime

# Windows 콘솔 UTF-8 강제 (한국어·특수문자 출력 깨짐 방지)
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def print_korean(msg, status="INFO"):
    colors = {
        "INFO": "\033[94m[정보]\033[0m",
        "SUCCESS": "\033[92m[성공]\033[0m",
        "ERROR": "\033[91m[오류]\033[0m"
    }
    prefix = colors.get(status, f"[{status}]")
    print(f"{prefix} {msg}", flush=True)

def make_slug(title):
    # 영문, 숫자, 한글, 하이픈만 허용하고 공백은 하이픈으로 변경
    slug = re.sub(r'[^a-zA-Z0-9가-힣\s-]', '', title).strip().lower()
    slug = re.sub(r'[\s]+', '-', slug)
    return slug

def parse_front_matter(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # YAML Front Matter 파싱
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    title = None
    date_str = None
    
    if match:
        front_matter = match.group(1)
        for line in front_matter.split('\n'):
            if line.startswith('title:'):
                title = line.split('title:', 1)[1].strip().strip('"').strip("'")
            elif line.startswith('date:'):
                date_str = line.split('date:', 1)[1].strip()
                # 날짜에 붙어있는 따옴표 등 제거
                date_str = date_str.strip('"').strip("'")
                # YYYY-MM-DD 형식만 추출
                date_match = re.match(r'^(\d{4}-\d{2}-\d{2})', date_str)
                if date_match:
                    date_str = date_match.group(1)
    
    return title, date_str, content

def run_command(cmd, cwd=None):
    # text=True 대신 bytes로 받아 utf-8 디코딩 (cp949 깨짐 방지)
    result = subprocess.run(cmd, shell=True, capture_output=True, cwd=cwd)
    stdout = result.stdout.decode('utf-8', errors='replace')
    stderr = result.stderr.decode('utf-8', errors='replace')
    return result.returncode, stdout, stderr

def main():
    if len(sys.argv) < 2:
        print_korean("사용법: python publish_to_blog.py <마크다운_파일_경로> [--slug <영문_슬러그>]", "ERROR")
        sys.exit(1)
        
    # 커맨드라인 인수 파싱
    src_path_raw = sys.argv[1]
    passed_slug = None
    
    if "--slug" in sys.argv:
        try:
            slug_idx = sys.argv.index("--slug")
            passed_slug = sys.argv[slug_idx + 1]
        except IndexError:
            print_korean("--slug 뒤에 슬러그 값을 지정해야 합니다.", "ERROR")
            sys.exit(1)
        
    src_path = os.path.abspath(src_path_raw)
    if not os.path.exists(src_path):
        print_korean(f"파일을 찾을 수 없습니다: {src_path}", "ERROR")
        sys.exit(1)
        
    print_korean(f"블로그 발행 프로세스를 시작합니다. 대상 파일: {os.path.basename(src_path)}")
    
    # 1. 파일 분석
    title, date_str, original_content = parse_front_matter(src_path)
    
    if not title:
        # Front matter에 title이 없는 경우 파일명 사용
        base_name = os.path.splitext(os.path.basename(src_path))[0]
        title = base_name
        print_korean(f"Front matter에서 제목(title)을 찾지 못해 파일명을 제목으로 설정합니다: {title}")
    
    if not date_str:
        # 오늘 날짜 사용
        date_str = datetime.today().strftime('%Y-%m-%d')
        print_korean(f"Front matter에서 날짜(date)를 찾지 못해 오늘 날짜로 설정합니다: {date_str}")
        
    # 2. 저장용 파일명 결정 (YYYY-MM-DD-slug.md)
    if passed_slug:
        slug = passed_slug.strip().lower()
        print_korean(f"전달받은 영문 슬러그를 사용합니다: {slug}")
    else:
        slug = make_slug(title)
        
    # 폴백 안전장치: 슬러그에 한글이나 허용되지 않은 문자가 있다면 깨짐 방지를 위해 clean한 영문/숫자 슬러그로 강제 대체
    if re.search(r'[^a-z0-9-]', slug):
        clean_slug = re.sub(r'[^a-z0-9-]', '', slug.encode('ascii', 'ignore').decode('ascii'))
        clean_slug = re.sub(r'-+', '-', clean_slug).strip('-')
        if not clean_slug:
            clean_slug = f"post-{date_str}"
        print_korean(f"경고: 슬러그에 비영문 문자({slug})가 포함되어 있어 깨짐 방지를 위해 안전한 슬러그({clean_slug})로 자동 전환합니다.", "INFO")
        slug = clean_slug

    new_filename = f"{date_str}-{slug}.md"
    
    # 블로그 루트 경로 확인 (_posts 폴더 위치)
    blog_root = os.path.dirname(os.path.abspath(__file__))
    posts_dir = os.path.join(blog_root, "_posts")
    
    if not os.path.exists(posts_dir):
        os.makedirs(posts_dir)
        
    dest_path = os.path.join(posts_dir, new_filename)
    
    # 3. 파일 복사 및 Front Matter 보강
    # layout: post 가 명시되어 있는지 확인하고 없으면 삽입
    has_layout = False
    lines = original_content.split('\n')
    
    # Front matter 확인
    if original_content.startswith('---'):
        in_front_matter = False
        front_matter_end_idx = -1
        for idx, line in enumerate(lines):
            if line.startswith('---'):
                if not in_front_matter:
                    in_front_matter = True
                else:
                    in_front_matter = False
                    front_matter_end_idx = idx
                    break
            if in_front_matter and line.startswith('layout:'):
                has_layout = True
                
        if not has_layout and front_matter_end_idx != -1:
            # layout: post 추가
            lines.insert(1, "layout: post")
            print_korean("Front matter에 'layout: post'를 추가하였습니다.")
            
    # 파일 쓰기
    with open(dest_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
        
    print_korean(f"글이 복사되었습니다: {dest_path}", "SUCCESS")
    
    # 4. Git 자동화
    print_korean("Git 스테이징 및 커밋을 진행합니다...")
    
    # 4.1 Git Add
    code, stdout, stderr = run_command("git add .", cwd=blog_root)
    if code != 0:
        print_korean(f"Git Add 실패: {stderr}", "ERROR")
        sys.exit(1)
        
    # 4.2 Git Commit
    commit_msg = f"Publish post: {title}"
    code, stdout, stderr = run_command(f'git commit -m "{commit_msg}"', cwd=blog_root)
    if code != 0:
        # 이미 최신 상태인 경우 커밋 실패할 수 있음
        if "nothing to commit" in stdout or "nothing to commit" in stderr:
            print_korean("Git 변경사항이 없어 커밋을 건너뜁니다.")
        else:
            print_korean(f"Git Commit 실패: {stderr}", "ERROR")
            sys.exit(1)
    else:
        print_korean(f"Git 커밋 성공: '{commit_msg}'", "SUCCESS")
        
    # 4.3 Git Push (origin main)
    print_korean("원격 저장소(GitHub)로 업로드 중... 잠시만 기다려주세요.")
    # 기본 브랜치 이름을 main 또는 master 확인
    code, stdout, stderr = run_command("git branch --show-current", cwd=blog_root)
    branch_name = stdout.strip() if code == 0 else "main"
    
    code, stdout, stderr = run_command(f"git push origin {branch_name}", cwd=blog_root)
    if code != 0:
        print_korean(f"Git Push 실패 (원격 연결 설정을 확인해주세요): {stderr}", "ERROR")
        print_korean("로컬 커밋까지만 완료되었습니다. 깃허브 원격 저장소가 등록된 후 'git push origin main'을 직접 실행하거나 다시 스크립트를 시도해 주세요.")
    else:
        print_korean("원격 저장소(GitHub) 업로드 성공! 배포가 시작되었습니다.", "SUCCESS")
        print_korean(f"블로그 주소: https://shinsteven9797.github.io/posts/{slug}/", "SUCCESS")

if __name__ == "__main__":
    main()
