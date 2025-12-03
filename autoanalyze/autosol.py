import subprocess
import glob
import os
import sys
import re

def extract_solidity_version(sol_file_path):#solのバージョンチェック
    pattern = r"pragma\s+solidity\s+([^;]+);"

    with open(sol_file_path, "r", encoding="utf-8") as f:
        for line in f:
            m = re.search(pattern, line)
            if m:
                return m.group(1).strip()
    return None
def normalize_version(version_str):
    if not version_str:
        return None
    # 最初に出現した x.x.x を抽出
    m = re.search(r"(\d+\.\d+\.\d+)", version_str)
    if m:
        return m.group(1)
    return None
def version_to_tuple(v):
    try:
        return tuple(map(int, v.split(".")))
    except:
        return None
def main():
    # コマンドライン引数チェック
    if len(sys.argv) < 2:
        print("Usage: python mythril_batch.py <dataset_directory>")
        return
    
    dataset_dir = sys.argv[1]

    # dataset_dir の存在確認
    if not os.path.isdir(dataset_dir):
        print(f"ERROR: Directory not found: {dataset_dir}")
        return

    # 出力フォルダ
    results_dir = "results"
    os.makedirs(results_dir, exist_ok=True)

    # .sol ファイルを再帰的に集める
    sol_files = glob.glob(os.path.join(dataset_dir, "**/*.sol"), recursive=True)

    if not sol_files:
        print("ERROR: 指定したディレクトリに .sol ファイルがありません")
        return

    for sol_path in sol_files:
        file_name = os.path.basename(sol_path)
        output_path = os.path.join(results_dir, file_name.replace(".sol", ".txt"))

        print(f"=== Analyzing {sol_path} ===")
        #solのバージョン抽出
        raw_version = extract_solidity_version(sol_path)
        version = normalize_version(raw_version)
        version_tuple = version_to_tuple(version) if version else None
        print(f"  pragma: {raw_version}, 抽出バージョン: {version}")
        
        #0.4.15はスキップ
        if version_tuple and version_tuple <= (0, 4, 15):
            print(f"  [SKIP] {sol_path} は Solidity {version} (<= 0.4.15) のため Mythril を実行しません")

            skip_path = os.path.join(results_dir, file_name.replace(".sol", "_skip.txt"))
            with open(skip_path, "w", encoding="utf-8") as f:
                f.write(f"Skipped {sol_path}\nReason: Solidity version is <= 0.4.15 ({version})\n")

            continue  # mythril 実行しない
        
        cmd = [
            "myth",
            "analyze",
            sol_path,
            "-t", "3",
            "--execution-timeout", "180"
        ]

        # Mythril 実行
        result = subprocess.run(cmd, capture_output=True, text=True)

        # 通常出力 → txt
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result.stdout)

        # エラー出力 → error.txt
        if result.stderr.strip():
            error_path = output_path.replace(".txt", "_error.txt")
            with open(error_path, "w", encoding="utf-8") as f:
                f.write(result.stderr)

        print(f"Saved: {output_path}")

if __name__ == "__main__":
    main()