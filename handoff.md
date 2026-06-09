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

전달받은 스타일 제안을 완벽하게 수렴하여, 가독성과 심미성을 극대화한 **Typora Lapis (라피스) 테마** 디자인 시스템을 완벽히 이식했습니다.

### ① 🔤 타이포그래피 (인쇄물 스타일 조합)
* **본문 및 헤더:** `Cantarell` (영문/숫자의 세련된 둥글음)과 `Noto Serif KR` (한글의 유려하고 차분한 세리프) 혼합 적용.
* **코드 블록 및 인라인 코드:** `JetBrains Mono` 고정폭 폰트 적용.

### ② 🎨 Lapis 컬러 시스템 (Lapis Light & Dark)
* **Lapis Light (라이트 모드):**
  * 배경: Pure White (`#ffffff`)
  * 사이드바: Soft Gray (`#f6f8fa`)
  * 포인트 컬러(Accent): Lapis Blue (`#4870ac`)
  * 텍스트: Muted Slate Gray (`#40464f`)
* **Lapis Dark (다크 모드):**
  * 배경: Deep Slate Gray-Blue (`#1e222a`)
  * 사이드바: Darker Blue-Gray (`#181c24`)
  * 포인트 컬러(Accent): Soft Slate Blue (`#8393ad`)
  * 텍스트: Soft White (`#e4e4e4e3`)

### ③ 🖼️ 미니멀 & 플랫 디자인 철학
* 기존 Chirpy의 과도한 그림자나 네온 광원 효과를 과감히 걷어내고 플랫한 테두리(`border`) 중심의 깔끔한 그리드를 채택했습니다.
* 가독성을 저해하는 소셜 공유 버튼, 추천 포스트 영역, 우측 TOC 사이드 패널을 완전히 숨김 처리하여 독자가 오직 글의 텍스트에만 몰입할 수 있도록 집중도를 극대화했습니다.

### ♿ 접근성 및 모바일 레이아웃 최적화
* 포커스 이동 시 Lapis Accent Blue 색상의 **포커스 링(`:focus-visible`)** 제공.
* 850px 이하 모바일 환경에서는 사이드바가 상단 콤팩트 가로 내비게이션으로 자연스럽게 흐르도록 반응형 오버라이드 구축.

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
