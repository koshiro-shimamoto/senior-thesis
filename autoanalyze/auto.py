import subprocess
import glob
import os
import sys
import re

def extract_and_normalize_solidity_version(sol_file_path):
   #solidityファイルからバージョンを抜き出す
    pattern = r"pragma\s+solidity\s+([^;]+);"

    raw_version = None
    with open(sol_file_path, "r", encoding="utf-8") as f:
        for line in f:
            m = re.search(pattern, line)
            if m:
                raw_version = m.group(1).strip()
                break

    if not raw_version:
        return (None)

    m2 = re.search(r"(\d+\.\d+\.\d+)", raw_version)
    if m2:
        return ( m2.group(1))
    return ( None)

def change_version(version):
    #0.4.5以下と0.4.15は動かんから0.4.15に変更
    major, minor, patch = map(int, version.split('.'))
    v = (major, minor, patch)
    if v == (0,4,15) or v <= (0,4,5):
        return "0.4.19"
    return version

def switch_solc_version(version):
    #solc-select を使ってコンパイラバージョンを変更
    try:
        #print(f"  solc-select use {version} 実行中...")
        result = subprocess.run(
            ["solc-select", "use", version],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print("  [ERROR] solc-select use に失敗")
            print("  stderr:", result.stderr)
            return False
        
        print(f"  ✔ solc バージョン切替成功: {version}")
        return True

    except Exception as e:
        print(f"  [ERROR] solc-select 実行中に例外発生: {e}")
        return False

def compile_solidity(sol_file_path, compiled_dir):
        """
        sol ファイルを `solc --bin` でコンパイルして、出力を
        `compiled_dir/<file_name>.bin` に書き込む。成功時に True、失敗時に False を返す。
        """
        file_name = os.path.basename(sol_file_path).replace(".sol", "")
        bin_output_path = os.path.join(compiled_dir, f"{file_name}.bin")

        solc_cmd = [
            "solc",
            "--bin",
            sol_file_path,
            #"-o", compiled_dir
        ]

        try:
            result = subprocess.run(solc_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"  [ERROR] solc 実行に失敗: {sol_file_path}")
                print("  stderr:", result.stderr)
                return False

            lines = result.stdout.splitlines()
            if len(lines)< 2:#この箇所を===があれば2行分削除に変更した方がいいかも
                print("[WARN] 出力行数が少なく、削除できません")
                stripped = result.stdout
            else:#先頭の2行を削除
                stripped = "\n".join(lines[3:])
            # 出力をそのままファイルに保存（必要ならパースして個別ファイル化する）
            with open(bin_output_path, "w", encoding="utf-8") as f:
                f.write(stripped)

            print(f"  ✔ コンパイル成功: {bin_output_path}")
            return bin_output_path

        except Exception as e:
            print(f"  [ERROR] コンパイル中に例外発生: {e}")
            return False


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
    results_dir = "byte_results"
    os.makedirs(results_dir, exist_ok=True)
    compiled_dir = "compiled"
    #solファイルを集める
    sol_files = glob.glob(os.path.join(dataset_dir, "**/*.sol"), recursive=True)
    if not sol_files:
        print("ERROR: 指定したディレクトリに .sol ファイルがありません")
        return
    """
    Compile a .sol file using `solc --bin` and save the raw output to
    `compiled_dir/<basename>.bin`.

    Returns:
      - True on successful compilation
      - False on failure
    """
    
    for sol_path in sol_files:
        file_name = os.path.basename(sol_path)
        output_path = os.path.join(results_dir, file_name.replace(".sol", "_byte.txt"))

        print(f"=== Analyzing {sol_path} ===")
        # sol のバージョン抽出（raw と正規化された x.y.z を取得）
        version = extract_and_normalize_solidity_version(sol_path)
        version = change_version(version)
        print(version)
        #version_tuple = version_to_tuple(version) if version else None
                # ③ solc-select でバージョン切替
        if version:
            success = switch_solc_version(version)
            if not success:
                print("  [ERROR] solc バージョン切替に失敗したためスキップ")
                continue
        else:
            print("  [WARN] Solidity バージョンを取得できなかったためデフォルトの solc を使用")
        
        bin_path =compile_solidity(sol_path,compiled_dir)
        if not bin_path:
            print("  [ERROR] コンパイルに失敗したためスキップ")
            continue

        cmd = [
            "myth",
            "analyze",
            "-f",
            bin_path,
            "-t", "3",
            "--execution-timeout", "180"
        ]

        # Mythril 実行
        print(f"  Running Mythril...:{bin_path}")
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
