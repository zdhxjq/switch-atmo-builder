# build_pack.py
import os
import sys
import shutil
import zipfile
import requests
from pathlib import Path

GITHUB_API_HEADERS = {"Accept": "application/vnd.github.v3+json"}

def get_latest_release_asset(owner, repo, suffix_filter):
    url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    resp = requests.get(url, headers=GITHUB_API_HEADERS)
    resp.raise_for_status()
    data = resp.json()
    for asset in data["assets"]:
        if asset["name"].endswith(suffix_filter):
            return asset["browser_download_url"], asset["name"]
    raise Exception(f"未找到 {owner}/{repo} 中以 {suffix_filter} 结尾的文件")

def download_file(url, save_path):
    print(f"📥 下载: {save_path.name}")
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(save_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

def extract_zip(zip_path, extract_to):
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(extract_to)

def main():
    output_dir = Path("SD_ROOT")
    temp_dir = Path("temp")
    
    # 清理
    if output_dir.exists():
        shutil.rmtree(output_dir)
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir()

    try:
        print("🚀 开始构建 Switch 大气层整合包（含 sigpatches）...")

        # 1. 下载 ITotalJustice 的 sigpatches（包含 atmosphere + bootloader + patches）
        print("\n[1/5] 获取 sigpatches...")
        sig_url, sig_name = get_latest_release_asset("ITotalJustice", "patches", ".zip")
        sig_zip = temp_dir / sig_name
        download_file(sig_url, sig_zip)
        extract_zip(sig_zip, output_dir)

        # 2. 更新 fusee.bin 为官方最新版
        print("\n[2/5] 获取最新 fusee.bin...")
        atmo_url, _ = get_latest_release_asset("Atmosphere-NX", "Atmosphere", ".zip")
        atmo_resp = requests.get(atmo_url, stream=True)
        atmo_zip = temp_dir / "atmo.zip"
        with open(atmo_zip, 'wb') as f:
            for chunk in atmo_resp.iter_content(8192):
                f.write(chunk)
        atmo_temp = temp_dir / "atmo"
        atmo_temp.mkdir()
        extract_zip(atmo_zip, atmo_temp)
        shutil.copy(atmo_temp / "fusee.bin", output_dir / "fusee.bin")

        # 3. 创建插件目录
        tesla_app_dir = output_dir / "tesla" / "apps"
        emuiibo_data_dir = output_dir / "emuiibo"
        daybreak_dir = output_dir / "switch" / "Daybreak"
        config_dir = output_dir / "atmosphere" / "config"

        tesla_app_dir.mkdir(parents=True, exist_ok=True)
        emuiibo_data_dir.mkdir(parents=True, exist_ok=True)
        daybreak_dir.mkdir(parents=True, exist_ok=True)
        config_dir.mkdir(parents=True, exist_ok=True)

        # 4. 下载 Tesla Menu
        print("\n[3/5] 下载 Tesla Menu...")
        tesla_url, tesla_name = get_latest_release_asset("WerWolv", "Tesla-Menu", ".nro")
        download_file(tesla_url, tesla_app_dir / tesla_name)

        # 5. 下载 emuiibo
        print("\n[4/5] 下载 emuiibo...")
        emuiibo_url, emuiibo_name = get_latest_release_asset("XorTroll", "emuiibo", ".nro")
        download_file(emuiibo_url, tesla_app_dir / emuiibo_name)

        # 6. 下载 DBI (Daybreak)
        print("\n[5/5] 下载 DBI (Daybreak)...")
        dbi_url, dbi_name = get_latest_release_asset("mison20000", "daybreak", ".nro")
        download_file(dbi_url, daybreak_dir / dbi_name)

        # 7. 启用 Tesla Overlay
        (config_dir / "system_settings.ini").write_text('[tesla]\nenabled = u8"1"\n', encoding="utf-8")

        # 8. 打包为 ZIP（保留 SD 卡根目录结构）
        zip_filename = "Switch_Atmo_Integration_Pack.zip"
        print(f"\n📦 正在打包整合包 → {zip_filename}")
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(output_dir):
                for file in files:
                    full_path = Path(root) / file
                    arc_path = full_path.relative_to(output_dir.parent)
                    zipf.write(full_path, arc_path)

        print(f"\n✅ 整合包构建成功！文件: {zip_filename}")

    except Exception as e:
        print(f"\n❌ 构建失败: {e}")
        sys.exit(1)
    finally:
        # 清理临时文件
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        if output_dir.exists():
            shutil.rmtree(output_dir)

if __name__ == "__main__":
    main()
