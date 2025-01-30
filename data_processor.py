import pandas as pd
from datetime import datetime, timedelta
import time

def print_timestamp(message):
    """Zaman damgalı mesaj yazdır"""
    current_time = time.strftime("%H:%M:%S")
    print(f"[{current_time}] {message}")

class DataProcessor:
    def __init__(self, file_path, test_mode=False):
        self.file_path = file_path
        self.test_mode = test_mode
        
        # Tezgah parametreleri
        self.ATKI_DEVIR = 450  # dakikada atılan atkı sayısı
        self.RANDIMAN = 0.85   # tezgah randımanı
        self.EFEKTIF_ATKI = self.ATKI_DEVIR * self.RANDIMAN  # efektif atkı sayısı
        
        # Takım hazırlık parametreleri
        self.TAKIM_HAZIRLIK_SURESI = 3  # saat (3 saat = 180 dakika)
        self.MIN_BOLME_MIKTARI = 500    # metre
        self.MAX_PARCA_SAYISI = 10      # maksimum bölünebilecek parça sayısı
        
        # Başlangıçta boş makine hızları sözlüğü
        self.machines = {
            'mk101': 0, 'mk102': 0, 'mk103': 0, 'mk201': 0,
            'mk202': 0, 'mk203': 0, 'mk301': 0, 'mk302': 0,
            'mk303': 0, 'mk304': 0
        }

    def calculate_machine_speed(self, atki_sikligi):
        """Atkı sıklığına göre makine hızını hesaplar (metre/saat)"""
        if not atki_sikligi or atki_sikligi <= 0:
            return 22  # varsayılan hız
        
        # Dakikada santimetre cinsinden hız hesaplama
        hiz_cm_dakika = self.EFEKTIF_ATKI / atki_sikligi
        
        # Saatte metre cinsine çevirme
        hiz_metre_saat = (hiz_cm_dakika * 60) / 100
        
        return round(hiz_metre_saat, 2)

    def update_machine_speeds(self, atki_sikligi):
        """Tüm makinelerin hızlarını günceller"""
        hiz = self.calculate_machine_speed(atki_sikligi)
        for makine in self.machines:
            self.machines[makine] = hiz

    def read_data(self):
        """Excel dosyasından verileri okur"""
        df = pd.read_excel(self.file_path)
        
        # Tarih sütununu datetime'a çevir
        df['hamTermin'] = pd.to_datetime(df['hamTermin'])
        
        # Son iki aylık veriyi filtrele
        son_tarih = df['hamTermin'].max()
        iki_ay_once = son_tarih - pd.DateOffset(months=2)
        df = df[df['hamTermin'] >= iki_ay_once]
        
        if self.test_mode:
            print_timestamp(f"Test modu aktif: Son iki aylık veri okunuyor ({iki_ay_once.strftime('%Y-%m-%d')} - {son_tarih.strftime('%Y-%m-%d')})")
            print(df.head())
            print_timestamp(f"Toplam kayıt sayısı: {len(df)}")
            return df
        return df
    
    def calculate_production_time(self, quantity, machine_speed):
        """Üretim süresini hesaplar (saat)"""
        return float(quantity) / machine_speed
    
    def check_type_change(self, current_variant, current_ulak, prev_variant, prev_ulak):
        """Tip değişim türünü belirler"""
        # İlk iş için veya önceki iş yoksa
        if prev_variant is None and prev_ulak is None:
            return "TAKIM"  # 180 dakika
        
        # Varyant kodu eşleşiyorsa - en verimli değişim
        if current_variant and prev_variant and current_variant == prev_variant:
            return "VARYANT"  # 30 dakika
        # Ulak kodu eşleşiyorsa
        elif current_ulak and prev_ulak and str(current_ulak) == str(prev_ulak):
            return "ULAK"  # 120 dakika
        # Hiçbir eşleşme yoksa
        else:
            return "TAKIM"  # 180 dakika
    
    def create_work_orders(self):
        """İş emirlerini oluşturur"""
        df = self.read_data()
        print("Excel'den okunan hamTermin örnekleri:")
        print(df['hamTermin'].head())
        
        work_orders = []
        now = pd.Timestamp.now()
        
        # DataFrame'i optimize et ve nan değerleri düzelt
        df['quantity'] = df['hamMiktar'].astype(float)
        df['hamTermin'] = pd.to_datetime(df['hamTermin'])
        df['atkiSikligi'] = pd.to_numeric(df['atkiSikligi'], errors='coerce').fillna(0)
        
        # Varyant ve Ulak kodlarını düzelt
        df['varyantKodu'] = df['varyantKodu'].astype(str)
        df['varyantKodu'] = df['varyantKodu'].replace(['nan', 'None', '0', 'NaN'], '')
        df['varyantKodu'] = df['varyantKodu'].apply(lambda x: x.replace('.0', '') if isinstance(x, str) else x)
        
        df['UlakKodu'] = df['UlakKodu'].astype(str)
        df['UlakKodu'] = df['UlakKodu'].replace(['nan', 'None', '0', 'NaN'], '')
        df['UlakKodu'] = df['UlakKodu'].apply(lambda x: x.replace('.0', '') if isinstance(x, str) else x)
        
        for idx, row in df.iterrows():
            if idx < 5:
                print(f"\nSatır {idx} için hamTermin: {row['hamTermin']}")
            
            # Atkı sıklığına göre makine hızlarını güncelle
            self.update_machine_speeds(row['atkiSikligi'])
            max_speed = max(self.machines.values())
            
            # Üretim süresini hesapla (sadece üretim süresi)
            min_production_time = self.calculate_production_time(row['quantity'], max_speed)
            
            # İş emri verilerini hazırla
            work_order_data = {
                'id': f"{row['siparisId']}_{row['siparisDetayId']}",
                'siparisId': str(row['siparisId']),
                'siparisDetayId': str(row['siparisDetayId']),
                'quantity': row['quantity'],
                'duration': min_production_time,  # Sadece üretim süresi
                'hamTermin': row['hamTermin'],
                'tipAd': str(row['tipAd']),
                'varyantKodu': row['varyantKodu'] if row['varyantKodu'] != '' else None,
                'ulakKodu': row['UlakKodu'] if row['UlakKodu'] != '' else None,
                'atkiSikligi': row['atkiSikligi'] if row['atkiSikligi'] > 0 else None
            }
            
            if idx < 5:
                print(f"İş emri {idx} için hamTermin: {work_order_data['hamTermin']}")
            
            # Termin kontrolü ve iş emri bölme
            remaining_time = max((row['hamTermin'] - now).total_seconds() / 3600, 1)
            
            # Sadece üretim süresine göre kontrol et
            if min_production_time > remaining_time:
                # Bölünecek parça sayısını hesapla
                required_splits = int(min_production_time / remaining_time) + 1
                
                # Maksimum parça sayısı kontrolü
                num_splits = min(required_splits, self.MAX_PARCA_SAYISI)
                
                # Minimum bölme miktarı kontrolü
                split_quantity = row['quantity'] / num_splits
                if split_quantity < self.MIN_BOLME_MIKTARI:
                    # Minimum miktara göre parça sayısını yeniden hesapla
                    num_splits = int(row['quantity'] / self.MIN_BOLME_MIKTARI)
                    if num_splits <= 1:
                        work_orders.append(work_order_data)
                        continue
                    split_quantity = row['quantity'] / num_splits
                
                print(f"\nSipariş {work_order_data['id']} termine yetişmeyecek:")
                print(f"Üretim süresi: {min_production_time:.1f} saat")
                print(f"Kalan süre: {remaining_time:.1f} saat")
                print(f"{num_splits} parçaya bölünüyor. Her parça: {split_quantity:.2f} metre")
                
                for i in range(num_splits):
                    split_order = work_order_data.copy()
                    split_order['id'] = f"{work_order_data['id']}_{i+1}"
                    split_order['quantity'] = split_quantity
                    split_order['duration'] = self.calculate_production_time(split_quantity, max_speed)
                    work_orders.append(split_order)
            else:
                work_orders.append(work_order_data)
        
        print(f"\nToplam {len(work_orders)} iş emri oluşturuldu.")
        print(f"Bölünen sipariş sayısı: {len(work_orders) - len(df)}")
        
        return work_orders 