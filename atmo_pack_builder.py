# atmo_pack_builder.py
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
    if resp.status_code == 403 and "rate limit" in resp.text:
        print("⚠️ GitHub API 限速，请稍后再试或在本地运行。")
        sys.exit(1)
    resp.raise_for_status()
    data = resp.json()
    for asset in data["assets"]:
        if asset["name"].endswith(suffix_filter):
            return asset["browser_download_url"], asset["name"]
    raise Exception(f"No asset found with suffix {suffix_filter} in {owner}/{repo}")

def download_file(url, save_path):
    print(f"正在下载 {save_path.name} ...")
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(save_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

def extract_zip_to(zip_path, target_dir):
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(target_dir)

def main():
    output_dir = Path("Atmo_Integration_Pack")
    temp_dir = Path("temp")
    
    if output_dir.exists():
        shutil.rmtree(output_dir)
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir()

    try:
        print("=== 构建 Switch Atmosphère 整合包（含 sigpatches）===")

        # 1. 下载 sigpatches
        print("\n[1/5] 下载 sigpatches...")
        sig_url, sig_name = get_latest_release_asset("ITotalJustice", "patches", ".zip")
        sig_zip = temp_dir / sig_name
        download_and_extract(sig_url, sig_zip, output_dir)

        # 2. 下载官方 Atmosphère（fusee.bin）
        print("\n[2/5] 下载 fusee.bin...")
        atmo_url, _ = get_latest_release_asset("Atmosphere-NX", "Atmosphere", ".zip")
        atmo_resp = requests.get(atmo_url, stream=True)
        atmo_zip = temp_dir / "atmo.zip"
        with open(atmo_zip, 'wb') as f:
            for chunk in atmo_resp.iter_content(8192):
                f.write(chunk)
        atmo_temp = temp_dir / "atmo"
        atmo_temp.mkdir()
        extract_zip_to(atmo_zip, atmo_temp)
        shutil.copy(atmo_temp / "fusee.bin", output_dir / "fusee.bin")

        # 3. 创建目录
        tesla_app_dir = output_dir / "tesla" / "apps"
        emuiibo_data_dir = output_dir / "emuiibo"
        daybreak_dir = output_dir / "switch" / "Daybreak"
        config_dir = output_dir / "atmosphere" / "config"

        tesla_app_dir.mkdir(parents=True, exist_ok=True)
        emuiibo_data_dir.mkdir(parents=True, exist_ok=True)
        daybreak_dir.mkdir(parents=True, exist_ok=True)
        config_dir.mkdir(parents=True, exist_ok=True)

        # 4. 下载 Tesla
        print("\n[3/5] 下载 Tesla Menu...")
        tesla_url, tesla_name = get_latest_release_asset("WerWolv", "Tesla-Menu", ".nro")
        download_file(tesla_url, tesla_app_dir / tesla_name)

        # 5. 下载 emuiibo
        print("\n[4/5] 下载 emuiibo...")
        emuiibo_url, emuiibo_name = get_latest_release_asset("XorTroll", "emuiibo", ".nro")
        download_file(emuiibo_url, tesla_app_dir / emuiibo_name)

        # 6. 下载 DBI
        print("\n[5/5] 下载 DBI (Daybreak)...")
        dbi_url, dbi_name = get_latest_release_asset("mison20000", "daybreak", ".nro")
        download_file(dbi_url, daybreak_dir / dbi_name)

        # 启用 Tesla
        (config_dir / "system_settings.ini").write_text('[tesla]\nenabled = u8"1"\n')

        # 打包为 ZIP（方便下载）
        zip_name = "Atmo_Integration_Pack.zip"
        print(f"\n📦 正在打包为 {zip_name}...")
        shutil.make_archive("Atmo_Integration_Pack", 'zip', output_dir)

        print(f"\n✅ 构建成功！整合包已生成。")
        print("GitHub Actions 将自动上传 .exe 和整合包 ZIP。")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        sys.exit(1)
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        if output_dir.exists():
            shutil.rmtree(output_dir)

if __name__ == "__main__":
    main()