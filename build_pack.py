# build_pack.py - 稳定版（支持 ZIP 内提取 .nro）
import os
import sys
import shutil
import zipfile
import requests
from pathlib import Path

# 如果提供了 GITHUB_TOKEN，用于提升 API 限额
token = os.getenv("GITHUB_TOKEN")
GITHUB_API_HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    **({"Authorization": f"token {token}"} if token else {})
}

def get_latest_release_asset(owner, repo, suffix_filter):
    url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    resp = requests.get(url, headers=GITHUB_API_HEADERS)
    if resp.status_code == 403 and "rate limit" in resp.text:
        print("❌ GitHub API 限速！请稍后再试。")
        sys.exit(1)
    resp.raise_for_status()
    data = resp.json()
    for asset in data["assets"]:
        if asset["name"].endswith(suffix_filter):
            return asset["browser_download_url"], asset["name"]
    raise Exception(f"在 {owner}/{repo} 中未找到以 {suffix_filter} 结尾的文件")

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

def find_nro_in_dir(root: Path, target_name: str = None):
    """递归查找 .nro 文件"""
    for f in root.rglob("*.nro"):
        if target_name is None or target_name in f.name:
            return f
    raise FileNotFoundError(f".nro 文件未在 {root} 中找到")

def main():
    output_dir = Path("SD_ROOT")
    temp_dir = Path("temp")
    
    if output_dir.exists():
        shutil.rmtree(output_dir)
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir()

    try:
        print("🚀 构建 Switch 大气层整合包（含 sigpatches）...")

        # 1. sigpatches
        print("\n[1/5] 获取 sigpatches...")
        sig_url, _ = get_latest_release_asset("ITotalJustice", "patches", ".zip")
        sig_zip = temp_dir / "sigpatches.zip"
        download_file(sig_url, sig_zip)
        extract_zip(sig_zip, output_dir)

        # 2. fusee.bin
        print("\n[2/5] 获取 fusee.bin...")
        atmo_url, _ = get_latest_release_asset("Atmosphere-NX", "Atmosphere", ".zip")
        atmo_zip = temp_dir / "atmo.zip"
        download_file(atmo_url, atmo_zip)
        atmo_temp = temp_dir / "atmo"
        atmo_temp.mkdir()
        extract_zip(atmo_zip, atmo_temp)
        shutil.copy(atmo_temp / "fusee.bin", output_dir / "fusee.bin")

        # 3. 目录
        tesla_app_dir = output_dir / "tesla" / "apps"
        emuiibo_data_dir = output_dir / "emuiibo"
        daybreak_dir = output_dir / "switch" / "Daybreak"
        config_dir = output_dir / "atmosphere" / "config"

        for d in [tesla_app_dir, emuiibo_data_dir, daybreak_dir, config_dir]:
            d.mkdir(parents=True, exist_ok=True)

        # 4. Tesla (从 ZIP 提取)
        print("\n[3/5] 下载 Tesla Menu...")
        tesla_url, _ = get_latest_release_asset("WerWolv", "Tesla-Menu", ".zip")
        tesla_zip = temp_dir / "tesla.zip"
        download_file(tesla_url, tesla_zip)
        tesla_temp = temp_dir / "tesla"
        tesla_temp.mkdir()
        extract_zip(tesla_zip, tesla_temp)
        tesla_nro = find_nro_in_dir(tesla_temp, "menu")
        shutil.copy(tesla_nro, tesla_app_dir / "tesla_menu.nro")

        # 5. emuiibo (从 ZIP 提取)
        print("\n[4/5] 下载 emuiibo...")
        emuiibo_url, _ = get_latest_release_asset("XorTroll", "emuiibo", ".zip")
        emuiibo_zip = temp_dir / "emuiibo.zip"
        download_file(emuiibo_url, emuiibo_zip)
        emuiibo_temp = temp_dir / "emuiibo"
        emuiibo_temp.mkdir()
        extract_zip(emuiibo_zip, emuiibo_temp)
        emuiibo_nro = find_nro_in_dir(emuiibo_temp)
        shutil.copy(emuiibo_nro, tesla_app_dir / "emuiibo.nro")

        # 6. DBI (通常提供 .nro)
        print("\n[5/5] 下载 DBI (Daybreak)...")
        try:
            dbi_url, _ = get_latest_release_asset("mison20000", "daybreak", ".nro")
            download_file(dbi_url, daybreak_dir / "Daybreak.nro")
        except:
            # 回退到 ZIP
            print("⚠️ 尝试从 ZIP 下载 DBI...")
            dbi_url, _ = get_latest_release_asset("mison20000", "daybreak", ".zip")
            dbi_zip = temp_dir / "dbi.zip"
            download_file(dbi_url, dbi_zip)
            dbi_temp = temp_dir / "dbi"
            dbi_temp.mkdir()
            extract_zip(dbi_zip, dbi_temp)
            dbi_nro = find_nro_in_dir(dbi_temp)
            shutil.copy(dbi_nro, daybreak_dir / "Daybreak.nro")

        # 7. 启用 Tesla
        (config_dir / "system_settings.ini").write_text('[tesla]\nenabled = u8"1"\n', encoding="utf-8")

        # 8. 打包
        zip_name = "Switch_Atmo_Integration_Pack.zip"
        print(f"\n📦 打包整合包 → {zip_name}")
        shutil.make_archive("Switch_Atmo_Integration_Pack", 'zip', output_dir)

        print("\n✅ 成功！整合包已生成。")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        if output_dir.exists():
            shutil.rmtree(output_dir)

if __name__ == "__main__":
    main()
