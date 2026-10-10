"""Put the Cirri game test's frames together into a film (it isn't committed: it shows Minecraft's own world).

  gradlew runClientGameTest -PskyTests=Cirri -PskyFilm -PtestHeap=2g
  python tools/film.py [out.mp4] [frames folder: sky-frames (the Cirri test) or sky-tour (the world test)]

The test films the game slowed down and notes the game tick of every frame
(build/run/clientGameTest/sky-frames/frames.txt); each frame is shown for as long as the game time it covers, so
the film runs at the game's real pace. Needs ffmpeg (on the PATH or WinGet's Gyan.FFmpeg).
"""
import glob
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRAMES = os.path.join(ROOT, "build", "run", "clientGameTest", "sky-frames")
TICK = 0.05


def ffmpeg():
    found = shutil.which("ffmpeg")
    if found:
        return found
    pattern = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "WinGet", "Packages", "Gyan.FFmpeg*", "**", "ffmpeg.exe")
    hits = glob.glob(pattern, recursive=True)
    if not hits:
        sys.exit("ffmpeg not found")
    return hits[0]


def main(argv):
    global FRAMES
    if len(argv) > 1:
        FRAMES = os.path.join(ROOT, "build", "run", "clientGameTest", argv[1])
    out = os.path.abspath(argv[0] if argv else os.path.join(ROOT, "build", "film", "cirri-flight.mp4"))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    rows = [line.split() for line in open(os.path.join(FRAMES, "frames.txt"), encoding="utf-8") if line.strip()]
    entries = []
    for i, (frame, stage, tick) in enumerate(rows):
        nxt = int(rows[i + 1][2]) if i + 1 < len(rows) else int(tick) + 1
        # a frame covers the game time until the next one (at most a few ticks: between scenes the game jumps ahead)
        entries.append((f"frame-{int(frame):04d}.png", min(3, max(1, nxt - int(tick))) * TICK))
    with open(os.path.join(FRAMES, "list.txt"), "w", encoding="utf-8") as f:
        for name, seconds in entries:
            f.write(f"file '{name}'\nduration {seconds:.3f}\n")
        f.write(f"file '{entries[-1][0]}'\n")
    subprocess.run([ffmpeg(), "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", "list.txt",
                    "-vf", "minterpolate=fps=30:mi_mode=blend,format=yuv420p", "-c:v", "libx264", "-crf", "20",
                    "-movflags", "+faststart", out], cwd=FRAMES, check=True)
    print(f"{out}: {len(entries)} frames, {sum(s for _, s in entries):.1f} s")


if __name__ == "__main__":
    main(sys.argv[1:])
