import os
import sys
import glob
import subprocess
def main():
    if len(sys.argv) < 2:
        print("Usage:python mythrill_batch.py <dataset_directory>")
        return
    dataset_dir = sys.argv[1]
    
    if not os.path.isdir(dataset_dir):
        print(f"Error: The directory {dataset_dir} does not exist.")
        return
    
    results_dir = "byte_results"
    evm_files = glob.glob(os.path.join(dataset_dir,"**/*.obf"),recursive=True)
    if not evm_files:
        print("ERROR: 指定したディレクトリに .sol ファイルがありません")
        return
    
    for evm_path in evm_files:
        file_name = os.path.basename(evm_path)
        output_path = os.path.join(results_dir,file_name.replace(".obf",".txt"))
        
        print(f"=== Analyzing {evm_path} ===")
        cmd = [
            "myth",
            "analyze",
            "-f",
            evm_path,
            "-t", "3",
            "--execution-timeout", "180"
        ]
        print(" ".join(cmd))
        result =subprocess.run(cmd,capture_output = True,text=True)
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