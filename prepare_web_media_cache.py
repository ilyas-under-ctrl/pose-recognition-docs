from web_annotator_server import WEB_MEDIA_DIR, ensure_web_media
from annotation_tool import VIDEO_HEADERS, VIDEOS_CSV, ensure_video_index, read_csv


def main():
    ensure_video_index()
    videos = read_csv(VIDEOS_CSV, VIDEO_HEADERS)
    WEB_MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Preparing {len(videos)} browser-playable videos in {WEB_MEDIA_DIR}")
    for index, video in enumerate(videos, start=1):
        path = video["path"]
        print(f"[{index}/{len(videos)}] {path}")
        ensure_web_media(path)
    print("Done.")


if __name__ == "__main__":
    main()
