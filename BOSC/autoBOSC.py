import subprocess
from pathlib import Path
import os

BOSC_DIR = Path(r"C:\Users\koshiro\senior-thesis\BOSC")
output_dir = BOSC_DIR / "output"
def main():
    bin_files = sorted(Path(r"C:\Users\koshiro\senior-thesis\BOSC").glob("*.bin"))
    if not bin_files :
        print("対象ファイルが見つかりません")
        return
    
    print(f"{len(bin_files)} files found Start analysis..\n")
    
    for i ,file_path in enumerate(bin_files,1):
        print(f"[{i}/{len(bin_files)}] Analyzing: {file_path.name}")
        rel_path = os.path.relpath(file_path, BOSC_DIR )
        print("DEBUG bin_path:", str(rel_path),str(output_dir))

        result = subprocess.run(
            [
                "java",
                "-jar",
                "BOSC.jar",
                str(rel_path),
                str(output_dir)
            ],
            
            cwd=BOSC_DIR
        )
        
        if result.returncode != 0:
            print(f"Error analyzing {file_path.name}: {result.stderr}")
        else:
            print(f"Analysis complete for {file_path.name}")
    print("\nAll analyses complete.")
if __name__ == "__main__":
    main()