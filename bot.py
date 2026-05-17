import pandas as pd
from web3 import Web3
import time
import os

# ==========================================
# KONFIGURASI BOT (TANPA API KEY!)
# ==========================================
INPUT_CSV = "wallets.csv"       
OUTPUT_CSV = "active_wallets.csv" 
MIN_ETH_BALANCE = 0.0001  # Batas minimal saldo ETH (0.0001 ETH = sekitar $0.3)

# Menggunakan Public RPC Base (Gratis)
BASE_RPC = "https://mainnet.base.org"
w3 = Web3(Web3.HTTPProvider(BASE_RPC))

def get_eth_balance(wallet_address):
    """Mengecek saldo ETH murni langsung dari Node Base"""
    try:
        # Web3 mewajibkan format alamat Checksum (huruf besar-kecil)
        checksum_addr = w3.to_checksum_address(wallet_address)
        
        # Tarik saldo dalam satuan Wei, lalu konversi ke Ether
        balance_wei = w3.eth.get_balance(checksum_addr)
        balance_eth = w3.from_wei(balance_wei, 'ether')
        
        return float(balance_eth)
    except Exception as e:
        print(f" [ERROR RPC] {e}")
        return 0.0

def start_filtering():
    if not w3.is_connected():
        print("❌ Gagal terhubung ke jaringan Base. Cek koneksi internet.")
        return

    if not os.path.exists(INPUT_CSV):
        print(f"❌ File {INPUT_CSV} tidak ditemukan!")
        return

    print("=========================================")
    print("🚀 MEMULAI BOT FILTER (MODE DIRECT RPC) 🚀")
    print("=========================================")
    
    df_wallets = pd.read_csv(INPUT_CSV)
    total_wallets = len(df_wallets)
    print(f"[INFO] Memuat {total_wallets} alamat dari Dune.")

    filtered_results = []

    for index, row in df_wallets.iterrows():
        address = row['wallet_address']
        print(f"[{index + 1}/{total_wallets}] Cek: {address} ... ", end="", flush=True)
        
        eth_balance = get_eth_balance(address)
        
        if eth_balance >= MIN_ETH_BALANCE:
            print(f"🔥 AKTIF! Saldo: {eth_balance:.6f} ETH")
            filtered_results.append({
                "wallet_address": address,
                "eth_balance": eth_balance
            })
        else:
            print("❌ Kosong / Di bawah batas.")
            
        # Jeda tipis agar Public RPC Base tidak memblokir IP kita karena spam
        time.sleep(0.1)

    if filtered_results:
        df_output = pd.DataFrame(filtered_results)
        df_output = df_output.sort_values(by="eth_balance", ascending=False)
        df_output.to_csv(OUTPUT_CSV, index=False)
        print(f"\n✅ Selesai! {len(filtered_results)} wallet bensin ditemukan di '{OUTPUT_CSV}'")
    else:
        print("\n❌ Tidak ada wallet yang memenuhi target saldo.")

if __name__ == "__main__":
    start_filtering()
