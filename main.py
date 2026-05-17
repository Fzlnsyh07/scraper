import pandas as pd
import requests
import time
import os

# ===================================================
# KONFIGURASI ANKR ADVANCED API (BEBAS LIMIT & GRATIS)
# ===================================================
# MASUKKAN URL Advanced/Multichain API kamu dari dashboard Ankr di sini:
ANKR_ENDPOINT = "https://rpc.ankr.com/multichain/2b3a7d7536e26f0e9db506be561d2eafdcc4b60ebf53157ccbb06824f527bedf"

INPUT_CSV = "wallets.csv"       
OUTPUT_CSV = "bsc_networth_results.csv" 
MIN_NET_WORTH_USD = 0.1  # Hanya simpan wallet dengan total aset di atas $1 USD

def get_wallet_net_worth_ankr(wallet_address):
    """Mengambil seluruh saldo token dan menghitung total Net Worth di BSC via Ankr"""
    payload = {
        "jsonrpc": "2.0",
        "method": "ankr_getAccountBalance",
        "params": {
            "blockchain": "base", # Menargetkan jaringan BNB Smart Chain
            "walletAddress": wallet_address,
            "onlyWhitelisted": True # Mengabaikan token scam / dust airdrop sampah
        },
        "id": 1
    }
    
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(ANKR_ENDPOINT, json=payload, headers=headers)
        if response.status_code == 200:
            json_data = response.json()
            
            # Jika ada error internal dari RPC
            if 'error' in json_data:
                print(f" [API ERROR] {json_data['error']['message']}")
                return 0.0, []
                
            result = json_data.get("result", {})
            total_balance_usd = float(result.get("totalBalanceUsd", 0.0))
            assets = result.get("assets", [])
            
            # Kumpulkan detail koin yang bernilai saja
            coin_details = []
            for asset in assets:
                usd_value = float(asset.get("balanceUsd", 0.0))
                if usd_value > 0.01: # Hanya catat koin yang ada harganya
                    coin_name = asset.get("tokenSymbol", "UNKNOWN")
                    coin_balance = float(asset.get("balance", 0.0))
                    coin_details.append(f"{coin_name}: {coin_balance:.4f} (${usd_value:.2f})")
            
            return total_balance_usd, coin_details
            
        elif response.status_code == 429:
            print("⚠️ Rate limit Ankr tersentuh, rehat 3 detik...")
            time.sleep(3)
            return get_wallet_net_worth_ankr(wallet_address)
        else:
            print(f" [ERROR] Status {response.status_code}")
            return 0.0, []
            
    except Exception as e:
        print(f" [KONEKSI ERROR] {e}")
        return 0.0, []

def start_filtering():
    if "MASUKKAN_KODE_UNIK" in ANKR_ENDPOINT:
        print("❌ GAGAL: Kamu belum memasukkan URL API Ankr milikmu di baris ke-8!")
        return

    if not os.path.exists(INPUT_CSV):
        print(f"❌ File '{INPUT_CSV}' tidak ditemukan!")
        return

    print("====================================================")
    print("🚀 BOT SCANNER NET WORTH & TOKEN BSC (VIA ANKR) 🚀")
    print("====================================================")
    
    df_wallets = pd.read_csv(INPUT_CSV)
    if 'wallet_address' not in df_wallets.columns:
        df_wallets.rename(columns={df_wallets.columns[0]: 'wallet_address'}, inplace=True)
        
    total_wallets = len(df_wallets)
    print(f"[INFO] Siap memproses {total_wallets} alamat wallet.\n")

    filtered_results = []

    for index, row in df_wallets.iterrows():
        address = str(row['wallet_address']).strip()
        if not address.startswith("0x") or len(address) != 42:
            continue

        print(f"[{index + 1}/{total_wallets}] Memeriksa {address[:10]}... ", end="", flush=True)
        
        net_worth, coins = get_wallet_net_worth_ankr(address)
        
        if net_worth >= MIN_NET_WORTH_USD:
            print(f"🔥 SULTAN! Net Worth: ${net_worth:,.2f}")
            # Tampilkan 3 koin teratas di terminal sebagai preview
            if coins:
                print(f"   └─ Aset: {', '.join(coins[:3])}")
                
            filtered_results.append({
                "wallet_address": address,
                "total_net_worth_usd": net_worth,
                "all_assets_holding": " | ".join(coins)
            })
        else:
            print(f"❌ Ringan (Hanya ${net_worth:.2f})")
            
        # Jeda tipis 0.2 detik agar performa tetap stabil dan sopan ke server
        time.sleep(0.2)

    # Export Data
    if filtered_results:
        df_output = pd.DataFrame(filtered_results)
        # Urutkan dari yang paling kaya raya
        df_output = df_output.sort_values(by="total_net_worth_usd", ascending=False)
        df_output.to_csv(OUTPUT_CSV, index=False)
        print(f"\n====================================================")
        print(f"✅ BERHASIL! {len(filtered_results)} wallet aktif tersimpan di '{OUTPUT_CSV}'")
        print("====================================================")
    else:
        print("\n❌ Tidak ada dompet yang isinya di atas batas minimal.")

if __name__ == "__main__":
    start_filtering()
