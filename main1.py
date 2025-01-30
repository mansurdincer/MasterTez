import pandas as pd
from genetic_algorithm import GeneticScheduler
from data_processor import DataProcessor

def print_debug(message):
    """Zaman damgalı debug mesajı yazdırır."""
    from datetime import datetime
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")

# Deney yapmak istediğimiz parametreleri belirleyelim
experiments = [
    {"population_size": 50, "generations": 10, "cxpb": 0.8, "mutpb": 0.05, "weights": (-2, -3, -10)},
    {"population_size": 100, "generations": 15, "cxpb": 0.9, "mutpb": 0.1, "weights": (-5, -2, -8)},
    {"population_size": 30, "generations": 8, "cxpb": 0.7, "mutpb": 0.02, "weights": (-3, -5, -7)}
]

# Sonuçları saklamak için boş bir liste oluştur
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
    
    # Popülasyonun boş olup olmadığını kontrol et
    population = scheduler.toolbox.population(n=scheduler.population_size)
    if not population:
        print_debug("❌ Hata: Popülasyon boş! Varsayılan fitness değeri atanıyor.")
        best_fitness = float('inf')  # Sonsuz büyük değer atayarak hatayı önlüyoruz.
    else:
        # Fitness değerleri atanmış mı kontrol et
        if any(len(ind.fitness.values) == 0 for ind in population):
            print_debug("⚠️ Uyarı: Bazı bireylerin fitness değeri hesaplanmamış! Yeniden hesaplanıyor...")
            fitnesses = list(map(scheduler.evaluate_schedule, population))
            for ind, fit in zip(population, fitnesses):
                ind.fitness.values = fit
        
        # En iyi fitness değerini bul
        best_fitness = min([ind.fitness.values[0] for ind in population])

    print_debug(f"📌 En iyi fitness değeri: {best_fitness}")
    
    try:
        total_time = max([sum([task['Duration'] for task in machine if isinstance(task, dict) and 'Duration' in task]) for machine in machine_schedules if machine])
    except KeyError as e:
        print_debug(f"❌ Hata: Eksik anahtar - {e}. Varsayılan değer atanıyor.")
        total_time = float('inf')
    except ValueError:
        print_debug("⚠️ Uyarı: Makine çizelgeleri boş olabilir. Varsayılan toplam süre atanıyor.")
        total_time = 0
    
    load_variance = scheduler.debug_stats["generation_stats"][-1]["best_fitness"]
    type_changes = sum(scheduler.debug_stats["type_changes"].values())
    
    results.append([i, exp["population_size"], exp["generations"], exp["cxpb"], exp["mutpb"], exp["weights"],
                    best_fitness, total_time, load_variance, type_changes])
    print_debug(f"Deney {i} tamamlandı. Fitness: {best_fitness}, Toplam Süre: {total_time} saat.")

# DataFrame oluştur ve Excel'e kaydet
df = pd.DataFrame(results, columns=columns)
df.to_excel("deney_sonuclari.xlsx", index=False)
print_debug("✅ Tüm deneyler tamamlandı! Sonuçlar 'deney_sonuclari.xlsx' dosyasına kaydedildi.")
