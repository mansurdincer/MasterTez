import sys
from data_processor import DataProcessor
from genetic_algorithm import GeneticScheduler, print_timestamp
from visualizer import ScheduleVisualizer

def main(test_mode=False):
    print("Debug: Program başlıyor...")
    print_timestamp("Program başladı")
    
    # Veri okuma
    print("Debug: Veri okuma başlıyor...")
    print_timestamp("Veri okuma başladı")
    data_processor = DataProcessor('siparis.xlsx', test_mode=test_mode)
    work_orders = data_processor.create_work_orders()
    print_timestamp(f"Veri okuma tamamlandı. {len(work_orders)} iş emri oluşturuldu")
    
    # Genetik algoritma
    print_timestamp("Genetik algoritma başlatılıyor")
    population_size = 20 if test_mode else 50  # Test modunda daha küçük popülasyon
    scheduler = GeneticScheduler(work_orders, machines=10, population_size=population_size)
    
    # Optimizasyon
    generations = 50 if test_mode else 100  # Test modunda çok daha az nesil
    machine_schedules = scheduler.optimize(generations=generations)
    print_timestamp("Genetik algoritma tamamlandı")
    
    # Çözümü değerlendir
    print_timestamp("Çözüm değerlendirme başladı")
    gantt_schedules = {}
    for machine_id in range(10):
        gantt_schedules[f'mk{101+machine_id}'] = []
    
    for machine_id, group_list in enumerate(machine_schedules):
        machine_name = f'mk{101+machine_id}'
        current_time = 0
        
        for order_idx, order in enumerate(group_list):
            # Tip değişim süresini hesapla
            if order_idx > 0:
                prev_order = group_list[order_idx - 1]
                prev_variant = prev_order.get('varyantKodu', '')
                prev_ulak = prev_order.get('ulakKodu', '')
                
                type_change = data_processor.check_type_change(
                    order.get('varyantKodu', ''), order.get('ulakKodu', ''),
                    prev_variant, prev_ulak
                )
                
                type_change_duration = {
                    'VARYANT': 30,  # 30 dakika
                    'ULAK': 120,    # 120 dakika
                    'TAKIM': 180    # 180 dakika
                }.get(type_change, 180)  # Varsayılan olarak takım değişimi
                
                # Tip değişimini Gantt'a ekle
                if type_change_duration > 0:
                    gantt_schedules[machine_name].append({
                        'Task': f'Tip Değişimi ({type_change})',
                        'Start': current_time,
                        'Duration': type_change_duration / 60,  # Dakikayı saate çevir
                        'Type': 'change'
                    })
                    current_time += type_change_duration / 60
            else:
                # İlk iş için takım hazırlığı
                type_change_duration = 180  # 3 saat
                gantt_schedules[machine_name].append({
                    'Task': 'İlk Takım Hazırlığı',
                    'Start': current_time,
                    'Duration': type_change_duration / 60,
                    'Type': 'change'
                })
                current_time += type_change_duration / 60
            
            # İş emri bilgileri
            task_info = {
                'Task': f'İş Emri {order["id"]}',
                'Start': current_time,
                'Duration': order['duration'],  # Sadece üretim süresi
                'Type': type_change.lower() if order_idx > 0 else 'takim',
                'quantity': order['quantity'],
                'atki_sikligi': order['atkiSikligi'],
                'siparisId': order['siparisId'],
                'siparisDetayId': order['siparisDetayId'],
                'tipAd': order['tipAd'],
                'varyantKodu': order['varyantKodu'],
                'ulakKodu': order['ulakKodu'],
                'hamTermin': order['hamTermin']
            }
            
            gantt_schedules[machine_name].append(task_info)
            current_time += order['duration']
    
    # Görselleştirme
    print_timestamp("Görselleştirmeler oluşturuluyor")
    visualizer = ScheduleVisualizer()
    
    # Gantt şeması oluştur
    gantt_filename = 'test_cizelge.html' if test_mode else 'cizelge.html'
    visualizer.create_gantt(gantt_schedules, gantt_filename)
    print_timestamp(f"Gantt şeması kaydedildi: {gantt_filename}")
    
    # Analiz grafikleri oluştur
    analysis_filename = 'test_analiz.html' if test_mode else 'analiz.html'
    visualizer.create_analysis_charts(scheduler.debug_stats, analysis_filename)
    print_timestamp(f"Analiz grafikleri kaydedildi: {analysis_filename}")

if __name__ == '__main__':
    test_mode = '--test' in sys.argv
    main(test_mode=test_mode) 