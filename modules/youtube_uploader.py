"""YouTube Data API v3 자동 업로드 모듈"""
from pathlib import Path

_CONFIG = Path(__file__).parent.parent / "config"
TOKEN_PATH   = _CONFIG / "youtube_token.json"
SECRETS_PATH = _CONFIG / "youtube_client_secrets.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def get_credentials():
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
    except ImportError:
        raise ImportError(
            "pip install google-api-python-client google-auth-oauthlib"
        )

    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not SECRETS_PATH.exists():
                raise FileNotFoundError(
                    f"YouTube OAuth 파일 없음: {SECRETS_PATH}\n\n"
                    "설정 방법:\n"
                    "1. https://console.cloud.google.com → 새 프로젝트 생성\n"
                    "2. API 및 서비스 → YouTube Data API v3 활성화\n"
                    "3. 사용자 인증 정보 → OAuth 2.0 클라이언트 ID → 데스크톱 앱\n"
                    f"4. JSON 다운로드 → {SECRETS_PATH} 로 저장\n"
                    "5. 다시 업로드 실행 (브라우저 인증 팝업이 한 번 뜸)"
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(SECRETS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")

    return creds


def upload_video(video_path: str, title: str, description: str,
                 tags: str, privacy: str = "private", progress_cb=None) -> str:
    """YouTube에 영상 업로드. 업로드된 영상 URL 반환."""
    try:
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
    except ImportError:
        raise ImportError(
            "pip install google-api-python-client google-auth-oauthlib"
        )

    if not Path(video_path).exists():
        raise FileNotFoundError(f"영상 파일 없음: {video_path}\nStep 6 영상 빌드를 먼저 실행하세요.")

    if progress_cb:
        progress_cb("  YouTube OAuth 인증 중...")
    creds = get_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    tag_list = [t.strip() for t in tags.replace("\n", ",").split(",") if t.strip()][:500]

    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tag_list,
            "categoryId": "22",          # People & Blogs
            "defaultLanguage": "ko",
        },
        "status": {
            "privacyStatus": privacy,    # private / unlisted / public
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(
        video_path, chunksize=256 * 1024, resumable=True, mimetype="video/mp4"
    )

    if progress_cb:
        progress_cb(f"  업로드 시작 ({Path(video_path).stat().st_size // 1024 // 1024} MB)...")

    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status and progress_cb:
            progress_cb(f"  업로드 진행: {int(status.progress() * 100)}%")

    url = f"https://youtu.be/{response['id']}"
    if progress_cb:
        progress_cb(f"  ✅ 업로드 완료 ({privacy}): {url}")
    return url
