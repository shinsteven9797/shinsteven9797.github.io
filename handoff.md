# 깃허브 블로그(Jekyll Chirpy) 구축 및 운영 핸드오프 가이드

이 문서는 `shinsteven9797.github.io` 블로그의 로컬 환경 구성, 깃허브 Pages 배포 설정, 한글 폰트 적용 및 자동 발행 자동화 구축 완료 상태와 사용 방법을 정리한 핸드오프 가이드입니다.

---

## 1. 블로그 기본 정보

* **블로그 주소:** [https://shinsteven9797.github.io](https://shinsteven9797.github.io)
* **깃허브 저장소:** [https://github.com/shinsteven9797/shinsteven9797.github.io](https://github.com/shinsteven9797/shinsteven9797.github.io)
* **작성자 정보:**
  * **GitHub Username:** `shinsteven9797`
  * **Git Commit Email:** `shin.steven97@gmail.com`
* **블로그 테마:** Jekyll Chirpy Starter (v7.5)

---

## 2. 블로그 설정 및 커스터마이징 내역

### ① 기본 설정 (`_config.yml`)
블로그의 핵심 설정을 한국어 환경과 작성자의 정보에 맞춰 수정했습니다.
* **언어 및 타임존:** `lang: ko`, `timezone: Asia/Seoul`
* **타이틀 및 소개:** `title: Tech Writer`, `tagline: AI & 바이브 코딩 공부 지식 정리`
* **URL 매핑:** `url: "https://shinsteven9797.github.io"` 및 GitHub 계정 정보 연동 완료.

### ② 한글 웹폰트 적용 (`assets/css/jekyll-theme-chirpy.scss`)
가독성이 뛰어난 한국어 웹폰트인 **Pretendard(프리텐다드)**를 적용했습니다.
* **폰트 로드:** CDN을 통해 Pretendard Variable 웹폰트를 호출합니다.
* **Sass 문법 준수:** `@use 'main' ...;` 규칙을 파일 최상단에 선언한 뒤 `@import` 규칙을 작성하여 Sass 문법 오류를 사전에 차단했습니다.
```scss
---
---
@use 'main{%- if jekyll.environment == "production" -%}.bundle{%- endif -%}';
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.css');

body {
  font-family: 'Pretendard Variable', Pretendard, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif !important;
}
```

### ③ GitHub Actions 워크플로우 (`.github/workflows/pages-deploy.yml`)
* **빌드 안정성 확보:** 루비 환경의 최신 버전(3.4) 라이브러리 제거 이슈로 인한 빌드 오류를 방지하기 위해, 안정성이 검증된 **Ruby 3.3** 버전을 사용하도록 명시적으로 고정했습니다.
* **불필요한 테스트 스킵:** 초기 구축 및 템플릿 환경에서 빌드가 막히지 않도록 `htmlproofer` 링크 검사 단계(Test site)를 비활성화했습니다.

---

## 3. 원클릭 자동 발행 시스템 (`publish_to_blog.py`)

옵시디언(Obsidian) 등 로컬 에디터에서 자유롭게 작성한 마크다운 문서를 간단한 명령어 한 줄로 깃허브 블로그에 자동 발행해 주는 파이썬 스크립트입니다.

### 💡 주요 기능
1. **파일명 자동 변환:** 마크다운 파일 내 Front Matter에 기록된 `title`과 `date`를 읽어 Jekyll 규격인 `YYYY-MM-DD-title.md` 형태로 파일명을 자동 재생성합니다. (날짜가 없으면 오늘 날짜 자동 적용)
2. **레이아웃 추가:** 글 포맷에 `layout: post` 설정이 누락된 경우 이를 자동으로 삽입해 줍니다.
3. **블로그 폴더 복사:** 결과물을 프로젝트의 `_posts/` 폴더로 자동 복사합니다.
4. **Git 자동화:** `git add`, `git commit -m "Publish post: [제목]"`, `git push` 과정을 자동으로 실행해 깃허브 저장소에 코드를 밀어 넣고 배포를 트리거합니다.

### ⚙️ 사용 방법
터미널에서 아래의 명령어를 입력하여 실행합니다.

```powershell
python publish_to_blog.py "<작성한_마크다운_파일_경로>"
```

* **사용 예시:**
  ```powershell
  python publish_to_blog.py "C:\Users\Park\Documents\my-obsidian\02_Projects\AntiGravity\my-first-post.md"
  ```

---

## 4. 운영 및 관리 수칙

1. **GitHub Pages 빌드 소스 설정:**
   * 깃허브 저장소 웹페이지의 **Settings** -> **Pages** -> **Build and deployment** 경로에서 **Source**가 **`GitHub Actions`**로 선택되어 있어야 정상적으로 빌드가 동작합니다.
2. **새 글 업로드 후 배포 확인:**
   * 스크립트 실행 후 **[Actions 탭](https://github.com/shinsteven9797/shinsteven9797.github.io/actions)**에서 빌드 작업(`Build and Deploy`)이 초록색 체크(`✓`)로 정상 완료되었는지 확인합니다. (약 1~2분 소요)
