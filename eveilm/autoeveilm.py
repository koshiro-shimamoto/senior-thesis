import subprocess
from pathlib import Path

# ===== 設定 =====
EVEILM_DIR = Path(r"C:\Users\koshiro\senior-thesis\eveilm")
EVEILM_SCRIPT = EVEILM_DIR / "eveilm.py"
TARGET_DIR = EVEILM_DIR / "resources" / "original"

# =================


def main():
    bin_files = sorted(TARGET_DIR.glob("*.bin"))

    if not bin_files:
        print("対象ファイルが見つかりません")
        return

    print(f"{len(bin_files)} files found. Start analysis...\n")

    for i, file_path in enumerate(bin_files, 1):
        print(f"[{i}/{len(bin_files)}] Analyzing: {file_path.name}")

        result = subprocess.run(
            [
                "python",
                str(EVEILM_SCRIPT),
                "--file",
                str(file_path),
            ],
            cwd=EVEILM_DIR
        )

        if result.returncode != 0:
            print("  ❌ Error occurred")
            print(result.stderr)
        else:
            print("  ✅ Done")

    print("\nAll files processed.")


if __name__ == "__main__":
    main()
