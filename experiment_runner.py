import pandas as pd
import plotly.graph_objects as go
import math
import webbrowser
from plotly.subplots import make_subplots
from genetic_algorithm import GeneticScheduler
from data_processor import DataProcessor



def print_debug(message):
    """Zaman damgalı debug mesajı yazdırır."""
    from datetime import datetime
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")

# Deney yapmak istediğimiz parametreler
# experiments = [
#     {"population_size": 50, "generations": 10, "cxpb": 0.8, "mutpb": 0.05, "weights": (-2, -3, -10)},
#     {"population_size": 60, "generations": 10, "cxpb": 0.8, "mutpb": 0.05, "weights": (-2, -3, -10)},
#     {"population_size": 70, "generations": 10, "cxpb": 0.8, "mutpb": 0.05, "weights": (-2, -3, -10)},
#     {"population_size": 80, "generations": 10, "cxpb": 0.8, "mutpb": 0.05, "weights": (-2, -3, -10)},
#     {"population_size": 50, "generations": 12, "cxpb": 0.8, "mutpb": 0.05, "weights": (-2, -3, -10)},
#     {"population_size": 50, "generations": 14, "cxpb": 0.8, "mutpb": 0.05, "weights": (-2, -3, -10)},
#     {"population_size": 50, "generations": 16, "cxpb": 0.8, "mutpb": 0.05, "weights": (-2, -3, -10)},
#     {"population_size": 50, "generations": 18, "cxpb": 0.8, "mutpb": 0.05, "weights": (-2, -3, -10)},
#     {"population_size": 50, "generations": 10, "cxpb": 0.7, "mutpb": 0.05, "weights": (-2, -3, -10)},
#     {"population_size": 50, "generations": 10, "cxpb": 0.6, "mutpb": 0.05, "weights": (-2, -3, -10)},
#     {"population_size": 50, "generations": 10, "cxpb": 0.9, "mutpb": 0.05, "weights": (-2, -3, -10)},
#     {"population_size": 50, "generations": 10, "cxpb": 1.0, "mutpb": 0.05, "weights": (-2, -3, -10)},
#     {"population_size": 50, "generations": 10, "cxpb": 0.8, "mutpb": 0.01, "weights": (-2, -3, -10)},
#     {"population_size": 50, "generations": 10, "cxpb": 0.8, "mutpb": 0.02, "weights": (-2, -3, -10)},
#     {"population_size": 50, "generations": 10, "cxpb": 0.8, "mutpb": 0.08, "weights": (-2, -3, -10)},
#     {"population_size": 50, "generations": 10, "cxpb": 0.8, "mutpb": 0.10, "weights": (-2, -3, -10)},
#     {"population_size": 50, "generations": 10, "cxpb": 0.8, "mutpb": 0.05, "weights": (-1, -2, -5)},
#     {"population_size": 50, "generations": 10, "cxpb": 0.8, "mutpb": 0.05, "weights": (-3, -3, -10)},
#     {"population_size": 50, "generations": 10, "cxpb": 0.8, "mutpb": 0.05, "weights": (-2, -4, -8)},
#     {"population_size": 50, "generations": 10, "cxpb": 0.8, "mutpb": 0.05, "weights": (-5, -2, -8)},
#     {"population_size": 50, "generations": 10, "cxpb": 0.8, "mutpb": 0.05, "weights": (-2, -3, -7)}
# ]

def dynamic_parameters(population_size, generations):
    """Popülasyon ve nesil sayısına göre çaprazlama ve mutasyon oranlarını hesaplar."""
    
    cxpb = min(0.7 + (math.log(population_size) / 15), 0.9)  # Çaprazlama oranı sınırlandırıldı
    mutpb = max(0.075, min(1 / math.sqrt(generations), 0.3)) # Mutasyon oranı kontrol altına alındı

    return {
        "population_size": population_size,
        "generations": generations,
        "cxpb": round(cxpb, 3),
        "mutpb": round(mutpb, 3),
        "weights": (-2, -3, -10)  # Sabit fitness ağırlıkları
    }
# Parametreleri belirleyerek experiments listesine ekleyelim
population_values = [5, 10, 15, 20, 50]  # Farklı popülasyon değerleri
generation_values = [10, 20, 50, 250]  # Farklı nesil sayıları

experiments = []

for pop in population_values:
    for gen in generation_values:
        experiments.append(dynamic_parameters(pop, gen))

# Experiment listesini satır satır consola yazdır
for i, exp in enumerate(experiments, start=1):
    print(f"{i}: {exp}")

input("Devam etmek için herhangi bir tuşa basın...")

# Sonuçları saklamak için boş bir liste
results = []

# Excel'e yazılacak kolonlar
columns = ["Deney No", "Popülasyon", "Nesiller", "Çaprazlama", "Mutasyon", "Fitness Ağırlıkları",
           "Fitness Değeri", "Toplam Süre (Saat)", "Makine Yük Dengesizliği", "Tip Değişim Sayısı"]

# Veriyi işle
print_debug("Veri işleme başlatılıyor...")
data_processor = DataProcessor("siparis.xlsx")
work_orders = data_processor.create_work_orders()
print_debug(f"Veri işleme tamamlandı. {len(work_orders)} iş emri oluşturuldu.")

# Deneyleri çalıştır
for i, exp in enumerate(experiments, start=1):
    print_debug(f"🚀 Deney {i} başlatılıyor: {exp}")

    # Genetik algoritmayı başlat
    scheduler = GeneticScheduler(work_orders, machines=10, population_size=exp["population_size"])
    print_debug("Genetik algoritma başlatıldı.")
    
    # Optimizasyonu çalıştır
    machine_schedules = scheduler.optimize(generations=exp["generations"])
    print_debug("Optimizasyon tamamlandı.")
    
    # Debug: machine_schedules içeriğini kontrol et
    if not machine_schedules:
        print_debug("❌ Uyarı: machine_schedules BOŞ!")
    else:
        print_debug(f"🔍 machine_schedules dolu, ilk makinenin görev sayısı: {len(machine_schedules[0])}")

    # for idx, machine in enumerate(machine_schedules[:3]):
    #     print_debug(f"Makine {idx+1}: {machine}")
    
    # Popülasyonun boş olup olmadığını kontrol et
    population = scheduler.toolbox.population(n=scheduler.population_size)
    if not population:
        print_debug("❌ Hata: Popülasyon boş! Varsayılan fitness değeri atanıyor.")
        best_fitness = float('inf')
    else:
        if any(len(ind.fitness.values) == 0 for ind in population):
            print_debug("⚠️ Uyarı: Bazı bireylerin fitness değeri hesaplanmamış! Yeniden hesaplanıyor...")
            fitnesses = list(map(scheduler.evaluate_schedule, population))
            for ind, fit in zip(population, fitnesses):
                ind.fitness.values = fit
        best_fitness = min([ind.fitness.values[0] for ind in population])

    print_debug(f"📌 En iyi fitness değeri: {best_fitness}")
    
    try:
        total_time = max([sum([task['duration'] for task in machine if isinstance(task, dict) and 'duration' in task]) for machine in machine_schedules if machine])
    except KeyError as e:
        print_debug(f"❌ Hata: Eksik anahtar - {e}. Varsayılan değer atanıyor.")
        total_time = float('inf')
    except ValueError:
        print_debug("⚠️ Uyarı: Makine çizelgeleri boş olabilir. Varsayılan toplam süre atanıyor.")
        total_time = 0
    
    print_debug(f"📌 Hesaplanan toplam süre: {total_time}")
    
    load_variance = scheduler.debug_stats["generation_stats"][-1]["best_fitness"]
    type_changes = sum(scheduler.debug_stats["type_changes"].values())
    
    results.append([i, exp["population_size"], exp["generations"], exp["cxpb"], exp["mutpb"], exp["weights"],
                    best_fitness, total_time, load_variance, type_changes])
    print_debug(f"Deney {i} tamamlandı. Fitness: {best_fitness}, Toplam Süre: {total_time} saat.")

    #input("Devam etmek için herhangi bir tuşa basın...")

# DataFrame oluştur ve Excel'e kaydet
df = pd.DataFrame(results, columns=columns)
df.to_excel("deney_sonuclari.xlsx", index=False)
print_debug("✅ Tüm deneyler tamamlandı! Sonuçlar 'deney_sonuclari.xlsx' dosyasına kaydedildi.")
# **Normalizasyon fonksiyonu**
def normalize_column(df, col):
    min_val = df[col].min()
    max_val = df[col].max()
    if max_val - min_val == 0:
        df[f"Normalized_{col}"] = 0
    else:
        df[f"Normalized_{col}"] = (df[col] - min_val) / (max_val - min_val)

# Excel dosyasını tekrar oku
df = pd.read_excel("deney_sonuclari.xlsx")

# Fitness Ağırlıkları sütunu string olmaması için düzeltme
if isinstance(df["Fitness Ağırlıkları"].iloc[0], str):
    df["Fitness Ağırlıkları"] = df["Fitness Ağırlıkları"].apply(lambda x: eval(x))

# **Önce Fitness Ağırlıkları toplamını hesapla ve sütun ekle**
df["Fitness_Ağırlıkları_Toplam"] = df["Fitness Ağırlıkları"].apply(lambda w: sum(w))

# **İhtiyaç duyulan sütunları normalize et**
normalize_column(df, "Fitness Değeri")
normalize_column(df, "Toplam Süre (Saat)")
normalize_column(df, "Makine Yük Dengesizliği")
normalize_column(df, "Popülasyon")
normalize_column(df, "Nesiller")
normalize_column(df, "Çaprazlama")
normalize_column(df, "Mutasyon")
normalize_column(df, "Fitness_Ağırlıkları_Toplam")

# Alt grafikleri olan tek bir HTML sayfası oluştur
fig = make_subplots(
    rows=3, cols=1,
    subplot_titles=(
        "Fitness Değeri vs. Parametreler (Normalize)", 
        "Toplam Süre (Saat) vs. Parametreler (Normalize)", 
        "Makine Yük Dengesizliği vs. Parametreler (Normalize)"
    )
)

# Birinci grafik: Normalleştirilmiş Fitness vs. (Popülasyon, Nesiller)
fig.add_trace(
    go.Scatter(
        x=df["Deney No"], 
        y=df["Normalized_Fitness Değeri"], 
        mode='lines+markers', 
        name='Fitness Değeri (Norm)'
    ), row=1, col=1
)
fig.add_trace(
    go.Scatter(
        x=df["Deney No"], 
        y=df["Normalized_Popülasyon"], 
        mode='lines', 
        name='Popülasyon (Norm)',
        line=dict(dash='dot')
    ), row=1, col=1
)
fig.add_trace(
    go.Scatter(
        x=df["Deney No"], 
        y=df["Normalized_Nesiller"], 
        mode='lines', 
        name='Nesiller (Norm)', 
        line=dict(dash='dashdot')
    ), row=1, col=1
)

# İkinci grafik: Normalleştirilmiş Toplam Süre vs. (Çaprazlama, Mutasyon)
fig.add_trace(
    go.Scatter(
        x=df["Deney No"], 
        y=df["Normalized_Toplam Süre (Saat)"], 
        mode='lines+markers', 
        name='Toplam Süre (Norm)'
    ), row=2, col=1
)
fig.add_trace(
    go.Scatter(
        x=df["Deney No"], 
        y=df["Normalized_Çaprazlama"], 
        mode='lines', 
        name='Çaprazlama (Norm)',
        line=dict(dash='dot')
    ), row=2, col=1
)
fig.add_trace(
    go.Scatter(
        x=df["Deney No"], 
        y=df["Normalized_Mutasyon"], 
        mode='lines', 
        name='Mutasyon (Norm)', 
        line=dict(dash='dashdot')
    ), row=2, col=1
)

# Üçüncü grafik: Normalleştirilmiş Makine Yük Dengesizliği vs. Fitness Ağırlıkları Toplamı
fig.add_trace(
    go.Scatter(
        x=df["Deney No"], 
        y=df["Normalized_Makine Yük Dengesizliği"], 
        mode='lines+markers', 
        name='Makine Yük Dengesizliği (Norm)'
    ), row=3, col=1
)
fig.add_trace(
    go.Scatter(
        x=df["Deney No"], 
        y=df["Normalized_Fitness_Ağırlıkları_Toplam"], 
        mode='lines', 
        name='Fitness Ağırlıkları Toplamı (Norm)',
        line=dict(dash='dot')
    ), row=3, col=1
)

fig.update_layout(
    height=1000, width=1200,
    title_text="Genetik Algoritma Deney Sonuçları - Parametre Etkileri (Normalleştirilmiş)",
    showlegend=True
)

fig.write_html("deney_sonuclari_grafik.html")

print("✅ Normalleştirilmiş verilerle HTML grafik oluşturuldu: deney_sonuclari_grafik.html")
webbrowser.open("deney_sonuclari_grafik.html")