# ScoreQuery — 성적 조회 시스템

교수자 성적 공시와 학생 본인 성적 조회를 지원하는 GitHub Pages 기반 웹 애플리케이션

## 🌐 웹 조회

GitHub Pages로 배포: **https://[your-username].github.io/ScoreQuery/**

- 학번 + 전화번호 뒷자리 4자리로 본인 성적 조회
- 과목 선택 후 공시 기간 내 성적 조회
- 평가항목별 점수 / 총점 카드 표시
- 분반 평균 및 최고점수 비교 Radar 차트
- 교수자 모드에서 과목, 평가기준, Excel 업로드, 공시 기간 관리

## 🔒 개인정보 보호

- 인증 키: `SHA-256(학번|전화번호뒷4자리)` — 원본 역추적 불가
- 전화번호, 이메일: JSON에 미포함
- 이름: 마스킹 처리 (첫 글자만 표시)
- 학번: 앞 4자리만 표시
- 성적/설정 파일: `AES-256-GCM + PBKDF2-HMAC-SHA256`으로 암호화 저장
- Excel 원본, `config.json`, `data.json`, 암호화된 민감 파일은 GitHub에 올리지 않음
- 정적 Pages 구조는 서버 비밀키를 숨길 수 없으므로 고위험 운영에서는 서버/API 검증 전환 권장

## 📁 프로젝트 구조

```
ScoreQuery/
├── docs/                    ← GitHub Pages 배포 폴더
│   ├── index.html
│   ├── data.enc.json        ← 암호화 성적 데이터(로컬 전용, Git 제외)
│   ├── admin-guide.md       ← 운영 가이드
│   └── static/
│       ├── style.css
│       ├── app.js
│       └── admin.js
├── app.py                   ← 로컬 Flask 서버 (개발용)
├── build_data.py            ← Excel → 암호화 JSON 변환 스크립트
├── scorequery_crypto.py     ← AES-256-GCM 암호화 모듈
├── secure_files.py          ← 민감 파일 암호화/복호화 CLI
├── config.example.json      ← 로컬 설정 예시
├── templates/index.html     ← Flask 템플릿
├── static/                  ← Flask 정적 파일
├── requirements.txt
└── .gitignore               ← 민감 파일 제외
```

## 🛠 데이터 업데이트

Excel 파일 변경 시:

```powershell
$env:SCOREQUERY_DATA_PASSPHRASE = "긴-임의-비밀번호"
python build_data.py    # docs/data.enc.json 생성
python secure_files.py scan
```

`docs/data.enc.json`도 민감 파일이므로 공개 GitHub 저장소에는 커밋하지 않습니다.

교수자 모드에서 Excel 업로드를 사용하는 경우:

1. 과목과 평가기준을 설정합니다.
2. Excel 파일을 업로드하고 검증 보고서를 확인합니다.
3. 성적데이터를 확정합니다.
4. 공시 시작/종료 일시를 설정하고 최종 확인 후 공시합니다.

## ⚙ GitHub Pages 설정

1. GitHub에서 Settings → Pages
2. Source: **Deploy from a branch**
3. Branch: **main**, Folder: **/docs**
4. Save → 배포 완료

추가 운영 메모는 [docs/admin-guide.md](docs/admin-guide.md)를 참고하세요.
