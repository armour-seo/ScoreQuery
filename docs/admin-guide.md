# ScoreQuery 운영 가이드

## 설정 파일

- `config.json`은 로컬 전용 파일입니다. 실제 GAS Web App URL처럼 배포 환경마다 달라지는 값은 이 파일에 둡니다.
- GitHub에는 `config.json`을 올리지 않습니다. 대신 `config.example.json`을 참고해 로컬에서만 생성합니다.
- `config.json`을 보관해야 하면 `python secure_files.py encrypt config.json --delete-plain`으로 `config.enc.json`을 만들고 평문을 제거합니다.

## 배포 데이터

- GitHub Pages 배포본은 `docs/` 폴더입니다.
- 현재 기본 배포 흐름은 `main` 브랜치의 `/docs` 폴더를 Pages source로 사용하는 방식입니다.
- `deploy.bat`는 `gh-pages` 브랜치 루트 배포가 필요할 때만 사용합니다. 둘 중 하나의 방식만 운영 기준으로 정해 사용하세요.
- 교수/학생 정보가 들어 있는 성적 데이터는 평문 `data.json`으로 배포하지 않습니다.
- 로컬 저장이 필요한 경우 `SCOREQUERY_DATA_PASSPHRASE` 환경변수를 설정한 뒤 암호화된 `docs/data.enc.json`만 생성합니다.

## 성적 공시 전 확인

1. 교수자 모드에서 과목을 선택합니다.
2. 평가 기준 합계가 100%인지 확인합니다.
3. Excel 업로드 후 파일 검증 보고서를 확인합니다.
4. 총점 불일치, 점수 결측, 인증정보 누락 항목을 확인합니다.
5. 공시 기간을 설정하고 최종 확인 창에서 학생 수와 검증 경고를 확인한 뒤 공시합니다.

## 개인정보 주의

- Excel 원본은 학번, 전화번호 등 개인정보를 포함하므로 GitHub에 올리지 않습니다.
- 성적 데이터 파일은 AES-256-GCM + PBKDF2-HMAC-SHA256 방식으로 암호화합니다.
- 암호화 파일도 공개 GitHub 저장소에는 올리지 않습니다. 암호화는 로컬 PC, 백업, 이동식 저장장치 유출에 대비한 추가 보호장치입니다.
- 정적 GitHub Pages 구조에서는 클라이언트 검증 한계가 있으므로, 고위험 운영에서는 서버/API 기반 조회 검증으로 전환하는 것을 권장합니다.

## 암호화 절차

PowerShell 예시:

```powershell
$env:SCOREQUERY_DATA_PASSPHRASE = "긴-임의-비밀번호를-여기에-입력"
python build_data.py
python secure_files.py scan
```

민감 파일을 직접 암호화할 때:

```powershell
python secure_files.py encrypt config.json docs/data.json "*.xlsx" --delete-plain
```

복호화가 필요한 경우:

```powershell
python secure_files.py decrypt docs/data.enc.json --output-dir restored
```
