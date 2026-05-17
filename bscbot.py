import pandas as pd
from web3 import Web3
import time
import os

# ==========================================
# KONFIGURASI BOT BSC (GRATIS & TANPA API KEY)
# ==========================================
INPUT_CSV = "wallets.csv"       
OUTPUT_CSV = "bsc_active_wallets.csv" 
MIN_BNB_BALANCE = 0.0005  # Batas minimal saldo (0.0005 BNB = sekitar $0.3)

# Menggunakan Public RPC BNB Smart Chain Resmi
BSC_RPC = "https://bsc-dataseed.binance.org/"
w3 = Web3(Web3.HTTPProvider(BSC_RPC))

def get_bnb_balance(wallet_address):
    """Mengecek saldo BNB murni langsung dari Node BSC"""
    try:
        # Konversi ke Checksum Address (wajib di Web3.py)
        checksum_addr = w3.to_checksum_address(wallet_address)
        
        # Tarik saldo dalam Wei, konversi ke BNB (Ether format)
        balance_wei = w3.eth.get_balance(checksum_addr)
        balance_bnb = w3.from_wei(balance_wei, 'ether')
        
        return float(balance_bnb)
    except Exception as e:
        print(f" [ERROR RPC] Gagal membaca {wallet_address[:8]}... : {e}")
        return 0.0

def start_filtering():
    # Cek koneksi ke jaringan BSC
    if not w3.is_connected():
        print("❌ Gagal terhubung ke jaringan BSC. Cek koneksi internet atau ganti RPC.")
        return

    if not os.path.exists(INPUT_CSV):
        print(f"❌ File {INPUT_CSV} tidak ditemukan di folder ini!")
        return

    print("=============================================")
    print("🚀 MEMULAI BOT FILTER SALDO BNB SMART CHAIN 🚀")
    print("=============================================")
    
    # Membaca data
    df_wallets = pd.read_csv(INPUT_CSV)
    
    # Pastikan nama kolom sesuai
    if 'wallet_address' not in df_wallets.columns:
        # Jika tidak ada header wallet_address, asumsikan kolom pertama adalah alamat
        df_wallets.rename(columns={df_wallets.columns[0]: 'wallet_address'}, inplace=True)

    total_wallets = len(df_wallets)
    print(f"[INFO] Memuat {total_wallets} alamat untuk diperiksa.\n")

    filtered_results = []

    for index, row in df_wallets.iterrows():
        # Bersihkan spasi kosong jika ada
        address = str(row['wallet_address']).strip() 
        
        # Lewati baris kosong atau yang bukan alamat EVM
        if not address.startswith("0x") or len(address) != 42:
            continue

        print(f"[{index + 1}/{total_wallets}] Cek: {address} ... ", end="", flush=True)
        
        bnb_balance = get_bnb_balance(address)
        
        if bnb_balance >= MIN_BNB_BALANCE:
            print(f"🔥 AKTIF! Saldo: {bnb_balance:.6f} BNB")
            filtered_results.append({
                "wallet_address": address,
                "bnb_balance": bnb_balance
            })
        else:
            print("❌ Di bawah batas bensin.")
            
        # Jeda 0.1 detik agar IP tidak diblokir sementara oleh Binance Node
        time.sleep(0.1)

    # Simpan hasil akhir
    if filtered_results:
        df_output = pd.DataFrame(filtered_results)
        df_output = df_output.sort_values(by="bnb_balance", ascending=False)
        df_output.to_csv(OUTPUT_CSV, index=False)
        print(f"\n✅ Eksekusi selesai! {len(filtered_results)} dompet sultan disimpan di '{OUTPUT_CSV}'")
    else:
        print("\n❌ Tidak ada wallet yang mencapai target minimal BNB.")

if __name__ == "__main__":
    start_filtering()
