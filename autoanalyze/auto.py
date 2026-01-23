#solファイルをコンパイルしてバイトコードを生成するスクリプト
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
    #0.4.22の時、なんか動かんから0.5.0に変更にする
    if raw_version.startswith(">="):
        m_ge = re.search(r"(\d+\.\d+\.\d+)", raw_version)
        if m_ge and m_ge.group(0) == "0.4.22" and m_ge.group(0):
            m_lt = re.search(r"<\s*(\d+\.\d+\.\d+)", raw_version)
            if m_lt.group(1).split(".")[1] == "5" or m_lt.group(1).split(".")[1] == "6":
                return "0.5.0"
            return "0.4.22"

    m2 = re.search(r"(\d+\.\d+\.\d+)", raw_version)
    if m2:
        return ( m2.group(1))
    return ( None)

def change_version(version):
    #0.4.5以下と0.4.15は動かんから0.4.19に変更
    major, minor, patch = map(int, version.split('.'))
    v = (major, minor, patch)
    if v == (0,4,15) or v <= (0,4,5):
        return "0.4.19"
    return version

def change_version(version):
    #0.4.5以下と0.4.15は動かんから0.4.19に変更
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
            current_contract = None
            buffer = []
            
            #base_name = os.path.splittext(os.path.basename(sol_file_path))[0]
            i = 0
            while i < len(lines):
                line = lines[i]
                
                if line.startswith("=") and ":" in line and line.endswith("="):
                    if current_contract and buffer:
                        bin_out_path = os.path.join(compiled_dir,f"{file_name}_{current_contract}.bin")
                        with open(bin_out_path, "w", encoding="utf-8") as f:
                            f.write("\n".join(buffer))
                            print(f"書き込み成功:{bin_out_path}")
                    
                    buffer =[]
                    if i + 1 <len(lines) and lines[i+1].startswith("Binary:"):
                        match= re.search(r":([^:\s]+)\s*=",line)
                        if match:
                            current_contract = match.group(1)
                        else:
                            current_contract = "Unknown"
                        i += 2
                        continue
                if current_contract:
                    buffer.append(line)
                i += 1
                
            if current_contract and buffer:
                bin_out_path = os.path.join(compiled_dir,f"{file_name}_{current_contract}.bin")
                with open(bin_out_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(buffer))
                    print(f"書き込み成功:{bin_out_path}")
            return bin_output_path
        except Exception as e:
            print(f"  [ERROR] solc 実行中に例外発生: {e}")
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
    results_dir = "results"
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
#compiled_dirにあるファイルすべてをコンパイル

    compiled_files = glob.glob(os.path.join(compiled_dir, "**/*.bin"), recursive=True)
    for bin_path in compiled_files:
        file_name = os.path.basename(bin_path)#/前やbinを除いた名前
        output_path = os.path.join(results_dir, file_name.replace(".bin", ".txt"))
        
        cmd = [
            "myth",
            "analyze",
            "-f",
            bin_path,
            "-t", "8",
            "--execution-timeout", "180"
        ]

        # Mythril 実行
        print(f"  Running Mythril...:{bin_path}")
        print(" ".join(cmd))
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
