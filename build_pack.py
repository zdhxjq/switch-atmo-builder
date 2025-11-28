# build_pack.py - 修复 DMCA 问题，使用 sigmapatches.info
import os
import sys
import shutil
import zipfile
import requests
from pathlib import Path

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
    for f in root.rglob("*.nro"):
        if target_name is None or target_name in f.name.lower():
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

        # ✅ 使用 sigmapatches.info 官方 CDN（无 DMCA 风险）
        print("\n[1/5] 从 sigmapatches.info 获取 sigpatches...")
        sig_url = "https://download.sigmapatches.info/sigpatches.zip"
        sig_zip = temp_dir / "sigpatches.zip"
        download_file(sig_url, sig_zip)
        extract_zip(sig_zip, output_dir)

        # 2. 获取最新 fusee.bin（Atmosphère 官方）
        print("\n[2/5] 获取最新 fusee.bin...")
        atmo_api = "https://api.github.com/repos/Atmosphere-NX/Atmosphere/releases/latest"
        resp = requests.get(atmo_api)
        resp.raise_for_status()
        data = resp.json()
        for asset in data["assets"]:
            if asset["name"].endswith(".zip"):
                atmo_url = asset["browser_download_url"]
                break
        else:
            raise Exception("未找到 Atmosphère ZIP")
        
        atmo_zip = temp_dir / "atmo.zip"
        download_file(atmo_url, atmo_zip)
        atmo_temp = temp_dir / "atmo"
        atmo_temp.mkdir()
        extract_zip(atmo_zip, atmo_temp)
        shutil.copy(atmo_temp / "fusee.bin", output_dir / "fusee.bin")

        # 3. 创建目录
        tesla_app_dir = output_dir / "tesla" / "apps"
        emuiibo_data_dir = output_dir / "emuiibo"
        daybreak_dir = output_dir / "switch" / "Daybreak"
        config_dir = output_dir / "atmosphere" / "config"

        for d in [tesla_app_dir, emuiibo_data_dir, daybreak_dir, config_dir]:
            d.mkdir(parents=True, exist_ok=True)

        # 4. Tesla Menu
        print("\n[3/5] 下载 Tesla Menu...")
        tesla_api = "https://api.github.com/repos/WerWolv/Tesla-Menu/releases/latest"
        resp = requests.get(tesla_api)
        resp.raise_for_status()
        data = resp.json()
        for asset in data["assets"]:
            if asset["name"].endswith(".zip"):
                tesla_url = asset["browser_download_url"]
                break
        else:
            raise Exception("未找到 Tesla ZIP")
        tesla_zip = temp_dir / "tesla.zip"
        download_file(tesla_url, tesla_zip)
        tesla_temp = temp_dir / "tesla"
        tesla_temp.mkdir()
        extract_zip(tesla_zip, tesla_temp)
        tesla_nro = find_nro_in_dir(tesla_temp, "menu")
        shutil.copy(tesla_nro, tesla_app_dir / "tesla_menu.nro")

        # 5. emuiibo
        print("\n[4/5] 下载 emuiibo...")
        emuiibo_api = "https://api.github.com/repos/XorTroll/emuiibo/releases/latest"
        resp = requests.get(emuiibo_api)
        resp.raise_for_status()
        data = resp.json()
        for asset in data["assets"]:
            if asset["name"].endswith(".zip"):
                emuiibo_url = asset["browser_download_url"]
                break
        else:
            raise Exception("未找到 emuiibo ZIP")
        emuiibo_zip = temp_dir / "emuiibo.zip"
        download_file(emuiibo_url, emuiibo_zip)
        emuiibo_temp = temp_dir / "emuiibo"
        emuiibo_temp.mkdir()
        extract_zip(emuiibo_zip, emuiibo_temp)
        emuiibo_nro = find_nro_in_dir(emuiibo_temp)
        shutil.copy(emuiibo_nro, tesla_app_dir / "emuiibo.nro")

        # 6. DBI (Daybreak)
        print("\n[5/5] 下载 DBI (Daybreak)...")
        dbi_api = "https://api.github.com/repos/mison20000/daybreak/releases/latest"
        resp = requests.get(dbi_api)
        resp.raise_for_status()
        data = resp.json()
        for asset in data["assets"]:
            if asset["name"].endswith(".nro") or asset["name"].endswith(".zip"):
                dbi_url = asset["browser_download_url"]
                dbi_name = asset["name"]
                break
        else:
            raise Exception("未找到 DBI 文件")
        
        dbi_path = temp_dir / dbi_name
        download_file(dbi_url, dbi_path)
        if dbi_name.endswith(".zip"):
            dbi_temp = temp_dir / "dbi"
            dbi_temp.mkdir()
            extract_zip(dbi_path, dbi_temp)
            dbi_nro = find_nro_in_dir(dbi_temp)
            shutil.copy(dbi_nro, daybreak_dir / "Daybreak.nro")
        else:
            shutil.copy(dbi_path, daybreak_dir / "Daybreak.nro")

        # 7. 启用 Tesla
        (config_dir / "system_settings.ini").write_text('[tesla]\nenabled = u8"1"\n', encoding="utf-8")

        # 8. 打包
        zip_name = "Switch_Atmo_Integration_Pack.zip"
        print(f"\n📦 打包整合包 → {zip_name}")
        shutil.make_archive("Switch_Atmo_Integration_Pack", 'zip', output_dir)

        print("\n✅ 整合包构建成功！")

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
