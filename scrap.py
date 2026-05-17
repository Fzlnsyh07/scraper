from playwright.sync_api import sync_playwright
import pandas as pd
import time

TARGET_URL = "https://basescan.org/txnAuthList?d=0xcA11bde05977b3631167028862bE2a173976CA11"

def scrape_basescan_auth_list():
    print("🚀 Memulai proses scraping antarmuka Basescan...")
    wallets = []

    with sync_playwright() as p:
        # headless=False sangat penting agar Cloudflare menganggap ini browser manusia sungguhan
        browser = p.chromium.launch(headless=True) 
        page = browser.new_page()
        
        print("🌐 Mengakses halaman txnAuthList...")
        page.goto(TARGET_URL)
        
        # Beri waktu tambahan jika ada proses verifikasi Cloudflare
        page.wait_for_selector("table", timeout=30000)
        time.sleep(3) # Jeda ekstra untuk memastikan tabel terender sempurna

        print("🕵️ Mengekstrak baris data...")
        # Ambil semua baris di dalam tabel
        rows = page.locator("table tbody tr").all()
        
        for row in rows:
            cols = row.locator("td").all()
            if len(cols) >= 4:
                # Kolom ke-2 adalah Signer (Wallet), Kolom ke-4 adalah Delegated To
                signer_address_element = cols[1].locator("a").first
                delegated_to_text = cols[3].inner_text()
                
                # Filter ketat: Pastikan memang mengarah ke Multicall3
                if "Multicall3" in delegated_to_text and signer_address_element.count() > 0:
                    wallet_address = signer_address_element.get_attribute("href").split("/")[-1]
                    wallets.append(wallet_address)
                    print(f"✔️ Ditemukan: {wallet_address}")

        browser.close()

    # Hapus duplikat (jika satu wallet melakukan beberapa transaksi)
    unique_wallets = list(set(wallets))
    
    if unique_wallets:
        df = pd.DataFrame(unique_wallets, columns=["wallet_address"])
        df.to_csv("wallets.csv", index=False)
        print(f"\n✅ Selesai! {len(unique_wallets)} wallet EIP-7702 berhasil disedot ke 'wallets.csv'.")
    else:
        print("\n❌ Tidak ada wallet yang cocok ditemukan di halaman pertama.")

if __name__ == "__main__":
    scrape_basescan_auth_list()
