import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from genetic_algorithm import GeneticScheduler
from data_processor import DataProcessor

def print_debug(message):
    """Zaman damgalı debug mesajı yazdırır."""
    from datetime import datetime
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")

# Deney yapmak istediğimiz parametreler
experiments = [
    {"population_size": 50, "generations": 10, "cxpb": 0.8, "mutpb": 0.05, "weights": (-2, -3, -10)},
    {"population_size": 60, "generations": 10, "cxpb": 0.8, "mutpb": 0.05, "weights": (-2, -3, -10)},
    {"population_size": 70, "generations": 10, "cxpb": 0.8, "mutpb": 0.05, "weights": (-2, -3, -10)},
    {"population_size": 80, "generations": 10, "cxpb": 0.8, "mutpb": 0.05, "weights": (-2, -3, -10)},
    {"population_size": 50, "generations": 12, "cxpb": 0.8, "mutpb": 0.05, "weights": (-2, -3, -10)},
    {"population_size": 50, "generations": 14, "cxpb": 0.8, "mutpb": 0.05, "weights": (-2, -3, -10)},
    {"population_size": 50, "generations": 16, "cxpb": 0.8, "mutpb": 0.05, "weights": (-2, -3, -10)},
    {"population_size": 50, "generations": 18, "cxpb": 0.8, "mutpb": 0.05, "weights": (-2, -3, -10)},
    {"population_size": 50, "generations": 10, "cxpb": 0.7, "mutpb": 0.05, "weights": (-2, -3, -10)},
    {"population_size": 50, "generations": 10, "cxpb": 0.6, "mutpb": 0.05, "weights": (-2, -3, -10)},
    {"population_size": 50, "generations": 10, "cxpb": 0.9, "mutpb": 0.05, "weights": (-2, -3, -10)},
    {"population_size": 50, "generations": 10, "cxpb": 1.0, "mutpb": 0.05, "weights": (-2, -3, -10)},
    {"population_size": 50, "generations": 10, "cxpb": 0.8, "mutpb": 0.01, "weights": (-2, -3, -10)},
    {"population_size": 50, "generations": 10, "cxpb": 0.8, "mutpb": 0.02, "weights": (-2, -3, -10)},
    {"population_size": 50, "generations": 10, "cxpb": 0.8, "mutpb": 0.08, "weights": (-2, -3, -10)},
    {"population_size": 50, "generations": 10, "cxpb": 0.8, "mutpb": 0.10, "weights": (-2, -3, -10)},
    {"population_size": 50, "generations": 10, "cxpb": 0.8, "mutpb": 0.05, "weights": (-1, -2, -5)},
    {"population_size": 50, "generations": 10, "cxpb": 0.8, "mutpb": 0.05, "weights": (-3, -3, -10)},
    {"population_size": 50, "generations": 10, "cxpb": 0.8, "mutpb": 0.05, "weights": (-2, -4, -8)},
    {"population_size": 50, "generations": 10, "cxpb": 0.8, "mutpb": 0.05, "weights": (-5, -2, -8)},
    {"population_size": 50, "generations": 10, "cxpb": 0.8, "mutpb": 0.05, "weights": (-2, -3, -7)}
]

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

# DataFrame oluştur ve Excel'e kaydet
df = pd.DataFrame(results, columns=columns)
df.to_excel("deney_sonuclari.xlsx", index=False)
print_debug("✅ Tüm deneyler tamamlandı! Sonuçlar 'deney_sonuclari.xlsx' dosyasına kaydedildi.")

# Excel dosyasını oku
df = pd.read_excel("deney_sonuclari.xlsx")

# Fitness Ağırlıkları sütununun string olarak gelmesini önle
if isinstance(df["Fitness Ağırlıkları"].iloc[0], str):
    df["Fitness Ağırlıkları"] = df["Fitness Ağırlıkları"].apply(lambda x: eval(x))

# Alt grafikleri olan tek bir HTML sayfası oluştur
fig = make_subplots(
    rows=3, cols=1,
    subplot_titles=(
        "Fitness Değeri vs. Parametreler", 
        "Toplam Süre (Saat) vs. Parametreler", 
        "Makine Yük Dengesizliği vs. Parametreler"
    )
)

# Fitness Değeri Grafiği
fig.add_trace(go.Scatter(x=df["Deney No"], y=df["Fitness Değeri"], mode='lines+markers', name='Fitness Değeri'), row=1, col=1)
fig.add_trace(go.Scatter(x=df["Deney No"], y=df["Popülasyon"], mode='lines', name='Popülasyon', line=dict(dash='dot')), row=1, col=1)
fig.add_trace(go.Scatter(x=df["Deney No"], y=df["Nesiller"], mode='lines', name='Nesiller', line=dict(dash='dashdot')), row=1, col=1)

# Toplam Süre Grafiği
fig.add_trace(go.Scatter(x=df["Deney No"], y=df["Toplam Süre (Saat)"], mode='lines+markers', name='Toplam Süre'), row=2, col=1)
fig.add_trace(go.Scatter(x=df["Deney No"], y=df["Çaprazlama"], mode='lines', name='Çaprazlama Oranı', line=dict(dash='dot')), row=2, col=1)
fig.add_trace(go.Scatter(x=df["Deney No"], y=df["Mutasyon"], mode='lines', name='Mutasyon Oranı', line=dict(dash='dashdot')), row=2, col=1)

# Makine Yük Dengesizliği Grafiği
fig.add_trace(go.Scatter(x=df["Deney No"], y=df["Makine Yük Dengesizliği"], mode='lines+markers', name='Makine Yük Dengesizliği'), row=3, col=1)
fig.add_trace(go.Scatter(x=df["Deney No"], y=[sum(w) for w in df["Fitness Ağırlıkları"]], mode='lines', name='Fitness Ağırlıkları Toplamı', line=dict(dash='dot')), row=3, col=1)

# Layout Ayarları
fig.update_layout(
    height=1000, width=1200, 
    title_text="Genetik Algoritma Deney Sonuçları - Parametre Etkileri",
    showlegend=True
)

# HTML olarak kaydet
fig.write_html("deney_sonuclari_grafik.html")

print("✅ Açıklayıcı HTML grafik oluşturuldu: deney_sonuclari_grafik.html")