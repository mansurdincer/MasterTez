import random
import numpy as np
import pandas as pd
from deap import base, creator, tools, algorithms
from collections import defaultdict
from datetime import datetime
import time

def print_timestamp(message):
    """Zaman damgalı mesaj yazdır"""
    current_time = time.strftime("%H:%M:%S")
    print(f"[{current_time}] {message}")

class GeneticScheduler:
    def __init__(self, work_orders, machines=10, population_size=50):
        self.work_orders = work_orders
        self.machines = machines
        self.population_size = population_size
        self.debug_stats = {
            'generation_stats': [],
            'type_changes': {'VARYANT': 0, 'ULAK': 0, 'TAKIM': 0},
            'machine_loads': [],
            'execution_times': []
        }
        
        # Genetik algoritma araçlarını hazırla
        try:
            creator.FitnessMin
        except:
            creator.create("FitnessMin", base.Fitness, weights=(-2, -3, -10))  # (Toplam süre, yük dengesi, tip değişim sayısı)
            creator.create("Individual", list, fitness=creator.FitnessMin)
        
        self.toolbox = base.Toolbox()
        self.toolbox.register("indices", random.sample, range(len(work_orders)), len(work_orders))
        self.toolbox.register("individual", tools.initIterate, creator.Individual, self.toolbox.indices)
        self.toolbox.register("population", tools.initRepeat, list, self.toolbox.individual)
        
        self.toolbox.register("mate", tools.cxUniformPartialyMatched, indpb=0.8)
        self.toolbox.register("mutate", tools.mutShuffleIndexes, indpb=0.05)
        self.toolbox.register("select", tools.selTournament, tournsize=10)
        self.toolbox.register("evaluate", self.evaluate_schedule)
    
    def group_work_orders(self):
        """İş emirlerini varyant ve ulak kodlarına göre grupla"""
        groups = []
        current_group = []
        
        # İlk iş emrini ekle
        if self.work_orders:
            current_group.append(self.work_orders[0])
        
        # Diğer iş emirlerini kontrol et
        for i in range(1, len(self.work_orders)):
            current = self.work_orders[i]
            previous = self.work_orders[i-1]
            
            # Varyant ve ulak kodları aynıysa gruba ekle
            if (current.get('varyantKodu') == previous.get('varyantKodu') and 
                current.get('ulakKodu') == previous.get('ulakKodu')):
                current_group.append(current)
            else:
                # Farklı kodlar varsa yeni grup başlat
                if current_group:
                    groups.append(current_group)
                current_group = [current]
        
        # Son grubu ekle
        if current_group:
            groups.append(current_group)
        
        return groups
    
    def find_best_machine(self, order, machine_loads, machine_times):
        """En uygun makineyi bul"""
        avg_time = sum(machine_times) / len(machine_times)
        max_time = max(machine_times) if machine_times else 0
        min_time = min(machine_times) if machine_times else 0
        
        current_variant = str(order.get('varyantKodu', '')).strip()
        current_ulak = str(order.get('ulakKodu', '')).strip()
        current_siparis_id = str(order.get('siparisId', '')).strip()
        
        if current_variant == '':
            current_variant = None
        if current_ulak == '':
            current_ulak = None
            
        # Aynı siparişin son planlandığı makineyi bul ve engelle
        blocked_machines = set()
        for i in range(self.machines):
            if machine_loads[i]:
                last_three_orders = machine_loads[i][-3:]  # Son 3 işe bak
                for prev_order in last_three_orders:
                    if str(prev_order.get('siparisId', '')).strip() == current_siparis_id:
                        blocked_machines.add(i)
                        break
        
        # Yük dengesizliği kontrolü
        load_imbalance = max_time - min_time
        if load_imbalance > avg_time * 0.3:  # %30'dan fazla dengesizlik varsa
            least_loaded = sorted(range(self.machines), key=lambda x: machine_times[x])
            for machine_id in least_loaded:
                if machine_id not in blocked_machines:
                    return machine_id
        
        # Varyant ve ulak eşleşmesi kontrolü
        best_match = None
        best_match_score = float('inf')
        
        for i in range(self.machines):
            if i in blocked_machines:
                continue
                
            if machine_loads[i]:
                last_order = machine_loads[i][-1]
                prev_variant = str(last_order.get('varyantKodu', '')).strip()
                prev_ulak = str(last_order.get('ulakKodu', '')).strip()
                
                if prev_variant == '':
                    prev_variant = None
                if prev_ulak == '':
                    prev_ulak = None
                
                load_score = abs(machine_times[i] - avg_time) / (max_time + 1)
                
                # Varyant eşleşmesi
                if current_variant and prev_variant and current_variant == prev_variant:
                    if load_score < best_match_score and machine_times[i] < avg_time * 1.2:
                        best_match_score = load_score
                        best_match = i
                # Ulak eşleşmesi
                elif current_ulak and prev_ulak and current_ulak == prev_ulak:
                    if load_score < best_match_score * 1.2 and machine_times[i] < avg_time * 1.2:
                        best_match_score = load_score
                        best_match = i
        
        if best_match is not None:
            return best_match
        
        # Normal skor hesaplama
        machine_scores = []
        for i in range(self.machines):
            if i in blocked_machines:
                machine_scores.append((i, float('inf')))
                continue
                
            # Yük dengesi skoru
            load_balance = abs(machine_times[i] - avg_time) / (max_time + 1)
            
            # Aşırı yüklenme cezası
            overload_penalty = 0
            if machine_times[i] > avg_time * 1.1:  # %10'dan fazla yüklüyse
                overload_penalty = (machine_times[i] - avg_time * 1.1) / avg_time
            
            # Düşük yüklenme teşviki
            underload_bonus = 0
            if machine_times[i] < avg_time * 0.9:  # %10'dan az yüklüyse
                underload_bonus = -0.3
            
            # Tip değişim kontrolü
            type_change_score = 0
            if machine_loads[i]:
                last_order = machine_loads[i][-1]
                prev_variant = str(last_order.get('varyantKodu', '')).strip()
                prev_ulak = str(last_order.get('ulakKodu', '')).strip()
                
                if prev_variant == '':
                    prev_variant = None
                if prev_ulak == '':
                    prev_ulak = None
                
                if not (current_variant and prev_variant and current_variant == prev_variant) and \
                   not (current_ulak and prev_ulak and current_ulak == prev_ulak):
                    type_change_score = 0.8
            
            total_score = (0.6 * load_balance) + (0.4 * type_change_score) + overload_penalty + underload_bonus
            machine_scores.append((i, total_score))
        
        # En düşük skorlu makineyi seç
        best_machine, _ = min(machine_scores, key=lambda x: x[1])
        return best_machine
    
    def evaluate_schedule(self, individual):
        """Çizelgenin uygunluğunu değerlendir"""
        machine_loads = [[] for _ in range(self.machines)]
        machine_times = [0] * self.machines
        total_changes = 0
        parallel_penalties = 0
        
        # İş emirlerini makinalara dağıt
        for idx in individual:
            order = self.work_orders[idx]
            best_machine = self.find_best_machine(order, machine_loads, machine_times)
            machine_loads[best_machine].append(order)
            
            if len(machine_loads[best_machine]) > 1:
                prev_order = machine_loads[best_machine][-2]
                change_time = self.calculate_type_change_time(order, prev_order)
                if change_time > 0:
                    total_changes += 1
                machine_times[best_machine] += change_time
                
                # Aynı sipariş kontrolü
                if str(order.get('siparisId', '')).strip() == str(prev_order.get('siparisId', '')).strip():
                    parallel_penalties += 1
            
            machine_times[best_machine] += order['duration']
        
        # Toplam üretim süresi
        total_time = max(machine_times)
        
        # İş yükü dengesi
        avg_time = sum(machine_times) / len(machine_times)
        load_variance = sum((t - avg_time) ** 2 for t in machine_times) / len(machine_times)
        
        # Boş ve aşırı yüklü makine cezaları
        empty_machines = sum(1 for t in machine_times if t == 0)
        overloaded_machines = sum(1 for t in machine_times if t > avg_time * 1.1)
        
        # Yük dengesi skoru (normalize edilmiş)
        balance_score = (load_variance / (avg_time ** 2)) * (1 + empty_machines * 2 + overloaded_machines)
        
        # Paralel üretim cezası
        parallel_score = parallel_penalties / len(self.work_orders)
        
        return total_time, balance_score + parallel_score * 2, total_changes / len(self.work_orders)
    
    def calculate_type_change_time(self, current_order, prev_order):
        """İki iş emri arasındaki tip değişim süresini hesapla"""
        if not prev_order:
            return 180  # İlk iş için takım değişimi
            
        # Varyant ve ulak kodlarını al ve temizle
        current_variant = str(current_order.get('varyantKodu', '')).strip()
        current_ulak = str(current_order.get('ulakKodu', '')).strip()
        prev_variant = str(prev_order.get('varyantKodu', '')).strip()
        prev_ulak = str(prev_order.get('ulakKodu', '')).strip()
        
        # Boş değer kontrolü
        if current_variant == '':
            current_variant = None
        if current_ulak == '':
            current_ulak = None
        if prev_variant == '':
            prev_variant = None
        if prev_ulak == '':
            prev_ulak = None
        
        # Eğer herhangi bir kod boş ise takım değişimi
        if not current_variant or not prev_variant:
            return 180  # Takım değişimi
        
        # Varyant kodu eşleşmesi
        if current_variant == prev_variant:
            return 30  # Varyant değişimi
        
        # Ulak kodu eşleşmesi
        if current_ulak and prev_ulak and current_ulak == prev_ulak:
            return 120  # Ulak değişimi
            
        return 180  # Takım değişimi
    
    def optimize(self, generations=100):
        """Genetik algoritma ile çizelgeyi optimize et"""
        print_timestamp("\nOptimizasyon başlıyor...")
        
        # Başlangıç zamanı
        start_time = time.time()
        
        print_timestamp("İlk popülasyon oluşturuluyor")
        pop = self.toolbox.population(n=self.population_size)
        
        # İstatistikler için
        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("min_time", lambda x: min(x, key=lambda y: y[0])[0])
        stats.register("min_balance", lambda x: min(x, key=lambda y: y[1])[1])
        stats.register("min_changes", lambda x: min(x, key=lambda y: y[2])[2])
        
        # İlk nesli değerlendir
        fitnesses = list(map(self.toolbox.evaluate, pop))
        for ind, fit in zip(pop, fitnesses):
            ind.fitness.values = fit
        
        # Debug için en iyi değerleri sakla
        best_fitness = float('inf')
        
        # Nesilleri evolve et
        for gen in range(1, generations + 1):
            gen_start_time = time.time()
            
            offspring = algorithms.varAnd(pop, self.toolbox, cxpb=0.8, mutpb=0.2)
            fitnesses = list(map(self.toolbox.evaluate, offspring))
            for ind, fit in zip(offspring, fitnesses):
                ind.fitness.values = fit
            
            # En iyi bireyi bul ve istatistikleri kaydet
            best_ind = tools.selBest(offspring, 1)[0]
            current_best = best_ind.fitness.values[0]
            
            if current_best < best_fitness:
                best_fitness = current_best
            
            # Nesil istatistiklerini kaydet
            self.debug_stats['generation_stats'].append({
                'generation': gen,
                'best_fitness': best_fitness,
                'avg_fitness': sum(ind.fitness.values[0] for ind in offspring) / len(offspring),
                'execution_time': time.time() - gen_start_time
            })
            
            pop[:] = offspring
            
            if gen % 10 == 0:
                print_timestamp(f"Nesil {gen}: En iyi fitness = {best_fitness:.2f}")
        
        # En iyi çözümü analiz et
        best_solution = self.analyze_best_solution(tools.selBest(pop, 1)[0])
        
        return best_solution
    
    def analyze_best_solution(self, best_ind):
        """En iyi çözümün detaylı analizini yapar"""
        machine_loads = [[] for _ in range(self.machines)]
        machine_times = [0] * self.machines
        machine_stats = {i: {'total_time': 0, 'job_count': 0, 'type_changes': 0} for i in range(self.machines)}
        
        for idx in best_ind:
            order = self.work_orders[idx]
            best_machine = self.find_best_machine(order, machine_loads, machine_times)
            machine_loads[best_machine].append(order)
            machine_stats[best_machine]['job_count'] += 1
            
            if len(machine_loads[best_machine]) > 1:
                prev_order = machine_loads[best_machine][-2]
                change_time = self.calculate_type_change_time(order, prev_order)
                
                if change_time == 30:
                    self.debug_stats['type_changes']['VARYANT'] += 1
                elif change_time == 120:
                    self.debug_stats['type_changes']['ULAK'] += 1
                else:
                    self.debug_stats['type_changes']['TAKIM'] += 1
                
                machine_times[best_machine] += change_time
                machine_stats[best_machine]['type_changes'] += 1
            
            machine_times[best_machine] += order['duration']
            machine_stats[best_machine]['total_time'] = machine_times[best_machine]
        
        # Makine yükü istatistiklerini kaydet
        self.debug_stats['machine_loads'] = machine_stats
        
        print("\n=== Optimizasyon Sonuçları ===")
        print(f"Toplam İş Emri Sayısı: {len(self.work_orders)}")
        print("\nTip Değişim İstatistikleri:")
        for change_type, count in self.debug_stats['type_changes'].items():
            print(f"{change_type}: {count}")
        
        print("\nMakine Yükü İstatistikleri:")
        for machine_id, stats in machine_stats.items():
            print(f"\nMakine {machine_id+1}:")
            print(f"Toplam Süre: {stats['total_time']:.2f} saat")
            print(f"İş Sayısı: {stats['job_count']}")
            print(f"Tip Değişim Sayısı: {stats['type_changes']}")
        
        return machine_loads 