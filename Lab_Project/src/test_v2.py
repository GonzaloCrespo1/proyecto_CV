"""
Capture chessboard images for camera calibration.

Every `interval` seconds a photo is taken from the live camera and saved as JPG
in `datos_damero/` (damero_01.jpg ... damero_20.jpg). By default a photo is only
saved when the chessboard is detected, so every saved image is usable by the
calibration script.

Keys:
    SPACE   take a photo now (still checks for the chessboard if required)
    p       pause / resume the automatic timer
    q, ESC  quit

Examples:
    python test_v2.py
    python test_v2.py --camera 0 --interval 3 --count 20 --pattern 9x6
    python test_v2.py --no-require-board      # save every frame, board or not
"""
import argparse
import time
from pathlib import Path

import cv2

DEFAULT_OUTPUT = Path(__file__).resolve().parent / "datos_damero"
FILE_PREFIX = "damero_"


def parse_args():
    parser = argparse.ArgumentParser(description="Capture chessboard images for camera calibration.")
    parser.add_argument("--camera", type=int, default=1, help="Camera index (default: 1)")
    parser.add_argument("--width", type=int, default=1280, help="Requested frame width")
    parser.add_argument("--height", type=int, default=720, help="Requested frame height")
    parser.add_argument("--interval", type=float, default=2.0, help="Seconds between photos (default: 2)")
    parser.add_argument("--count", type=int, default=20, help="Number of images to save (default: 20)")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output folder (default: src/datos_damero)")
    parser.add_argument("--pattern", type=str, default="9x6",
                        help="Chessboard INNER corners as COLSxROWS (default: 9x6)")
    parser.add_argument("--no-require-board", dest="require_board", action="store_false",
                        help="Save photos even if the chessboard is not detected")
    parser.add_argument("--min-sharpness", type=float, default=0.0,
                        help="Minimum Laplacian variance to accept a photo (0 = disabled)")
    parser.add_argument("--no-mirror", dest="mirror", action="store_false",
                        help="Do not mirror the preview window")
    parser.add_argument("--keep", action="store_true",
                        help="Keep existing damero_*.jpg files instead of deleting them at start")
    return parser.parse_args()


def parse_pattern(text):
    try:
        cols, rows = (int(v) for v in text.lower().split("x"))
    except ValueError:
        raise SystemExit(f"Invalid --pattern '{text}'. Use COLSxROWS, e.g. 9x6.")
    if cols < 2 or rows < 2:
        raise SystemExit("--pattern needs at least 2x2 inner corners.")
    return cols, rows


def prepare_output(folder, keep):
    folder.mkdir(parents=True, exist_ok=True)
    old = sorted(folder.glob(f"{FILE_PREFIX}*.jpg"))
    if old and not keep:
        for f in old:
            f.unlink()
        print(f"Removed {len(old)} old image(s) from {folder}")
    return folder


def next_free_index(folder):
    # Used with --keep so existing images are not overwritten
    i = 1
    while (folder / f"{FILE_PREFIX}{i:02d}.jpg").exists():
        i += 1
    return i


def open_camera(index, width, height):
    cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)  # Use CAP_DSHOW for Windows to avoid warning messages
    if not cap.isOpened():
        return None
    # MJPG lets most USB webcams deliver 720p at full frame rate
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    # Discard first frames while auto-exposure / white balance settle
    for _ in range(10):
        cap.read()
    return cap


def detect_board(gray, pattern, scale=1.0):
    """Return (found, corners) on a possibly downscaled image. Corners are in full-res coordinates."""
    img = gray if scale == 1.0 else cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    flags = cv2.CALIB_CB_ADAPTIVE_THRESH | cv2.CALIB_CB_NORMALIZE_IMAGE | cv2.CALIB_CB_FAST_CHECK
    found, corners = cv2.findChessboardCorners(img, pattern, flags)
    if found and scale != 1.0:
        corners = corners / scale
    return found, corners


def sharpness(gray):
    return cv2.Laplacian(gray, cv2.CV_64F).var()


def draw_text(img, text, org, scale=0.8, color=(255, 255, 255), thickness=2):
    cv2.putText(img, text, org, cv2.FONT_HERSHEY_SIMPLEX, scale, (0, 0, 0), thickness + 3, cv2.LINE_AA)
    cv2.putText(img, text, org, cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness, cv2.LINE_AA)


def main():
    args = parse_args()
    pattern = parse_pattern(args.pattern)
    out_dir = prepare_output(args.output, args.keep)
    index = next_free_index(out_dir) if args.keep else 1

    cap = open_camera(args.camera, args.width, args.height)
    if cap is None:
        # Requested camera not available: fall back to the first one that works
        for alt in (i for i in range(5) if i != args.camera):
            cap = open_camera(alt, args.width, args.height)
            if cap is not None:
                print(f"Camera {args.camera} not available, using camera {alt} instead.")
                args.camera = alt
                break
    if cap is None:
        print("Could not open any camera (tried indices 0-4). Is it connected / used by another app?")
        return

    real_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    real_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Camera {args.camera} opened at {real_w}x{real_h}")
    print(f"Saving {args.count} images every {args.interval:g}s to {out_dir}")
    print(f"Chessboard inner corners: {pattern[0]}x{pattern[1]} "
          f"({'required' if args.require_board else 'not required'})")

    window_name = "Calibration capture - SPACE: photo | p: pause | q: quit"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)  # resizable window

    # Live detection runs on a downscaled frame to keep the preview fluid
    preview_scale = min(1.0, 640 / max(real_w, 1))
    saved = 0
    paused = False
    next_shot = time.monotonic() + args.interval
    flash_until = 0.0
    status = ""
    status_until = 0.0

    try:
        while saved < args.count:
            ret, frame = cap.read()
            if not ret:
                print("No frame received (the camera may have been disconnected).")
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            found, corners = detect_board(gray, pattern, preview_scale)
            sharp = sharpness(gray)
            now = time.monotonic()

            key = cv2.waitKey(1) & 0xFF
            if key in (ord('q'), 27):
                break
            if key == ord('p'):
                paused = not paused
                next_shot = now + args.interval  # restart countdown on resume
            manual = key == ord(' ')

            # Take a photo when the timer expires (or on SPACE). If the board is
            # required and not visible, keep trying on every frame until it is.
            if manual or (not paused and now >= next_shot):
                reason = None
                if args.require_board and not found:
                    reason = "Chessboard not detected"
                elif args.min_sharpness > 0 and sharp < args.min_sharpness:
                    reason = f"Too blurry ({sharp:.0f} < {args.min_sharpness:g})"

                if reason is None:
                    # Save the RAW frame: no mirror, no overlays, otherwise calibration is wrong
                    path = out_dir / f"{FILE_PREFIX}{index:02d}.jpg"
                    if cv2.imwrite(str(path), frame, [cv2.IMWRITE_JPEG_QUALITY, 95]):
                        saved += 1
                        print(f"[{saved}/{args.count}] Saved {path.name}")
                        index += 1
                        status, status_until = f"Saved {path.name}", now + 1.0
                        flash_until = now + 0.15
                    else:
                        print(f"ERROR: could not write {path}")
                        status, status_until = "Write error!", now + 1.5
                    next_shot = now + args.interval
                else:
                    status, status_until = reason, now + 0.3

            # ---------- Preview (overlays only, never saved) ----------
            view = frame.copy()
            if found:
                cv2.drawChessboardCorners(view, pattern, corners, found)
            if args.mirror:
                view = cv2.flip(view, 1)
            if now < flash_until:
                view[:] = 255

            h = view.shape[0]
            draw_text(view, f"Images: {saved}/{args.count}", (15, 35))
            if paused:
                draw_text(view, "PAUSED (p to resume)", (15, 70), color=(0, 200, 255))
            else:
                remaining = max(0.0, next_shot - now)
                draw_text(view, f"Next photo in: {remaining:.1f}s", (15, 70))
            board_txt, board_col = ("Board: OK", (0, 255, 0)) if found else ("Board: NOT FOUND", (0, 0, 255))
            draw_text(view, board_txt, (15, 105), color=board_col)
            draw_text(view, f"Sharpness: {sharp:.0f}", (15, 140), scale=0.6)
            if now < status_until:
                draw_text(view, status, (15, h - 20), color=(0, 255, 255))

            # Progress bar
            bar_w = int(view.shape[1] * saved / args.count)
            cv2.rectangle(view, (0, h - 6), (bar_w, h), (0, 255, 0), -1)

            cv2.imshow(window_name, view)
    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
        cv2.destroyAllWindows()

    print(f"\nDone: {saved} image(s) saved in {out_dir}")
    if saved < args.count:
        print(f"Warning: only {saved}/{args.count} images captured.")


if __name__ == "__main__":
    main()
