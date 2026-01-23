# byte(obfファイル)をmythrilで解析し、
# dataset_dir のフォルダ構造を維持したまま
# 指定された出力ディレクトリに結果を保存するスクリプト

import os
import sys
import glob
import subprocess


def main():
    if len(sys.argv) < 3:
        print("Usage: python mythril_batch.py <dataset_directory> <output_directory>")
        return

    dataset_dir = sys.argv[1]
    results_dir = sys.argv[2]

    if not os.path.isdir(dataset_dir):
        print(f"Error: The directory {dataset_dir} does not exist.")
        return

    # 出力ディレクトリがなければ作成
    os.makedirs(results_dir, exist_ok=True)

    # 再帰的に .obf ファイルを取得
    evm_files = glob.glob(os.path.join(dataset_dir, "**", "*.obf"), recursive=True)
    if not evm_files:
        print("ERROR: 指定したディレクトリに .obf ファイルがありません")
        return

    for evm_path in evm_files:
        # dataset_dir からの相対パス
        rel_path = os.path.relpath(evm_path, dataset_dir)

        # 拡張子を .txt に変更
        rel_txt_path = os.path.splitext(rel_path)[0] + ".txt"

        # 出力先パス（フォルダ構造を維持）
        output_path = os.path.join(results_dir, rel_txt_path)

        # 出力先ディレクトリを作成
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        print(f"=== Analyzing {evm_path} ===")

        cmd = [
            "myth",
            "analyze",
            "-f", evm_path,
            "-t", "16",
            "--execution-timeout", "300"
        ]
        print(" ".join(cmd))

        result = subprocess.run(cmd, capture_output=True, text=True)

        # 通常出力 → txt
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result.stdout)

        # エラー出力 → _error.txt
        if result.stderr.strip():
            error_path = output_path.replace(".txt", "_error.txt")
            with open(error_path, "w", encoding="utf-8") as f:
                f.write(result.stderr)

        print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
