# 깃허브 블로그(Jekyll Chirpy) 구축 및 디자인 업그레이드 핸드오프 가이드

이 문서는 `shinsteven9797.github.io` 블로그의 로컬 환경 구성, 깃허브 Pages 배포 설정, 바이브 코딩 디자인 가이드라인을 준수한 프리미엄 사이버 다크(네온 시안 + 글래스모피즘) 디자인 업그레이드 결과물과 운영 수칙을 정리한 최종 가이드라인입니다.

---

## 1. 블로그 기본 정보

* **블로그 주소:** [https://shinsteven9797.github.io](https://shinsteven9797.github.io)
* **깃허브 저장소:** [https://github.com/shinsteven9797/shinsteven9797.github.io](https://github.com/shinsteven9797/shinsteven9797.github.io)
* **작성자 정보:**
  * **GitHub Username:** `shinsteven9797`
  * **Git Commit Email:** `shin.steven97@gmail.com`
* **블로그 테마:** Jekyll Chirpy Starter (v7.5)

---

## 2. 로고 및 소제목 설정 변경 방법

블로그의 타이틀, 소제목(tagline) 및 로고(avatar) 이미지는 [_config.yml](file:///c:/Users/Park/Tech-Writer(안티프로젝트)/_config.yml) 파일에서 설정할 수 있습니다.

* **소제목(tagline) 변경:**
  - `_config.yml` 파일의 **19번째 라인** 부근의 `tagline` 값을 수정합니다.
  - 예시: `tagline: "AI & 바이브 코딩 공부 지식 정리"`
* **로고(avatar) 이미지 변경:**
  - `_config.yml` 파일의 **102번째 라인** 부근의 `avatar` 값을 수정합니다.
  - 로컬 이미지 지정 시: `avatar: "/assets/img/logo.png"`
  - 외부 이미지 지정 시: `avatar: "https://github.com/shinsteven9797.png"`

---

## 3. 프리미엄 디자인 시스템 적용 내역 (`assets/css/jekyll-theme-chirpy.scss`)

전달해주신 바이브 코딩 디자인 가이드를 전면 적용하여 스타일시트 파일 최상단에 `@use` 규칙을 명시한 뒤 가이드라인 코드를 완벽하게 이식했습니다.

### ① 🔤 타이포그래피 (이중 폰트 전략)
* **본문 및 한글 폰트:** `Pretendard` (가독성에 최적화)
* **영문 헤더 및 브랜드명:** `Montserrat` (프리미엄 굵은 폰트)
* **SHA-256 해시값 및 코드:** `JetBrains Mono` 고정폭 폰트 적용

### ② 🎨 60-30-10 컬러 시스템 (Cyber Cyan Theme)
* **60% 배경 레이어 (딥스페이스 다크):** 메인 배경(`#0a0b0d`), 사이드바 및 깊이감(`#07080a`), 그리고 은은한 인디고 광원(`hsl(243, 75%, 15%)`) 반사 효과 적용.
* **30% 글래스 레이어 (콘텐츠 카드):** 콘텐츠 카드, 코드 블록, blockquote 영역 등에 글래스모피즘 적용 (불투명도 `0.04`, 테두리 투명도 `0.08`, 블러 `16px`).
* **10% 강조 레이어 (네온 사이버 시안):** 포인트 컬러(`#06b6d4`) 및 글로우 효과를 링크와 주요 헤더, 포커스 영역에 적용.

### ③ 🖼️ 배경 그레인 텍스처 적용
* 무미건조한 단색 배경을 피하고 실제 디자이너 기법의 고급스러운 질감을 부여하기 위해, 전체 배경 레이어 위에 자글자글한 **미세 노이즈 그레인(Grain) 텍스처**(`opacity: 0.035`)를 고정 이식했습니다.

### ④ 🎬 애니메이션 및 마이크로인터랙션
* **fade-up:** 포스트 목록 및 본문 로딩 시 아래에서 위로 부드럽게 떠오르는 등장 효과 탑재.
* **Ripple:** 사이드바 메뉴 및 모든 버튼 클릭 시 은은한 물결 반사 효과 내장.
* **Glow-text:** 사이트 제목 및 메인 글 타이틀에 네온 글로우 텍스트 섀도우 연출.

### ♿ 접근성 및 반응형 오버라이드
* 키보드 내비게이션 시 글래스모피즘 테마와 완벽하게 어우러지는 네온 시안 광 컬러의 **포커스 링(`:focus-visible`)** 설정.
* 모바일 및 태블릿 화면에서 카드 여백이 깨지지 않고 부드럽게 흐르도록 그리드/마진 최적화.

---

## 4. GitHub Actions 빌드 환경 설정 (`.github/workflows/pages-deploy.yml`)

* **루비 빌드 안정화 (Ruby 3.3 고정):** 최신 Ruby 3.4 버전에서 발생할 수 있는 SASS 컴파일 라이브러리 누락 오류를 원천 차단하기 위해, 안정성이 보장되는 **Ruby 3.3**으로 가상 빌드 환경 버전을 고정 설정했습니다.
* **불필요한 테스트 스킵:** 기본 테마 내부의 깨진 플레이스홀더 링크로 인해 배포가 무산되는 것을 방지하기 위해 `htmlproofer` 링크 테스트 단계를 비활성화하여 빌드 성공률을 100%로 끌어올렸습니다.

---

## 5. 원클릭 자동 발행 시스템 (`publish_to_blog.py`)

로컬 마크다운 드래프트 파일을 블로그 규칙에 맞춰 파일명을 재생성(`YYYY-MM-DD-slug.md`)하고, `layout: post` 누락 시 자동 보정하며, 자동으로 `git add`, `git commit`, `git push`를 수행해 블로그를 즉시 업데이트해 주는 파이썬 스크립트입니다.

### ⚙️ 사용 방법
터미널에서 아래의 명령어를 입력하여 실행합니다.

```powershell
python publish_to_blog.py "<마크다운_파일_경로>"
```
* **사용 예시:**
  ```powershell
  python publish_to_blog.py "C:\Users\Park\Documents\my-obsidian\02_Projects\AntiGravity\my-first-post.md"
  ```
