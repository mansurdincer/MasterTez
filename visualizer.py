import plotly.figure_factory as ff
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import json
from plotly.subplots import make_subplots

class ScheduleVisualizer:
    def __init__(self):
        self.colors = {
            'VARYANT'.lower(): 'rgb(144, 238, 144)',  # açık yeşil
            'ULAK'.lower(): 'rgb(238, 130, 238)',     # lila
            'TAKIM'.lower(): 'rgb(173, 216, 230)',    # açık mavi
            'change': 'rgb(220, 20, 60)'      # kızıl
        }
    
    def format_duration(self, hours):
        """Saat cinsinden süreyi saat ve dakika olarak biçimlendirir"""
        total_minutes = int(hours * 60)
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours} saat {minutes} dakika"
    
    def create_gantt(self, machine_schedules, filename):
        # Gantt şeması için veri hazırlama
        df = pd.DataFrame(columns=['Task', 'Start', 'Finish', 'Resource', 'Type', 'Duration', 'Quantity', 'Pick_Frequency', 'Description'])
        grid_data = []
        
        for machine_name, tasks in machine_schedules.items():
            for task in tasks:
                try:
                    start_time = pd.to_datetime('2025-01-01') + pd.Timedelta(hours=task['Start'])
                    end_time = pd.to_datetime('2025-01-01') + pd.Timedelta(hours=task['Start'] + task['Duration'])
                    
                    duration_str = self.format_duration(task['Duration'])
                    quantity = task.get('quantity', None)
                    quantity_str = f"{quantity:.2f}" if quantity is not None else ""
                    pick_frequency = task.get('atki_sikligi', '')
                    
                    if task['Type'].lower() == 'change':
                        hover_text = (
                            f"Tip Değişim: {task['Type']}<br>"
                            f"Süre: {duration_str}"
                        )
                    else:
                        hover_text = (
                            f"Sipariş No: {task.get('siparisId', '')}<br>"
                            f"Sipariş Detay No: {task.get('siparisDetayId', '')}<br>"
                            f"Tip: {task.get('tipAd', '')}<br>"
                            f"Varyant Kodu: {task.get('varyantKodu', '')}<br>"
                            f"Ulak Kodu: {task.get('ulakKodu', '')}<br>"
                            f"Tip Değişim: {task['Type']}<br>"
                            f"Süre: {duration_str}<br>"
                            f"Miktar: {quantity_str} metre<br>"
                            f"Atkı Sıklığı: {pick_frequency}"
                        )
                        
                        # Sadece üretim işleri grid'e eklenecek
                        termin_date = task.get('hamTermin')
                        termin_str = termin_date.strftime('%Y-%m-%d %H:%M:%S') if termin_date is not None else ''
                        
                        grid_data.append({
                            'Makine': machine_name,
                            'İşlem Tipi': 'Üretim',
                            'Başlangıç': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                            'Bitiş': end_time.strftime('%Y-%m-%d %H:%M:%S'),
                            'Süre': duration_str,
                            'Sipariş No': task.get('siparisId', ''),
                            'Sipariş Detay No': task.get('siparisDetayId', ''),
                            'Tip': task.get('tipAd', ''),
                            'Varyant Kodu': task.get('varyantKodu', ''),
                            'Ulak Kodu': task.get('ulakKodu', ''),
                            'Miktar': quantity_str,
                            'Atkı Sıklığı': pick_frequency if pick_frequency else '',
                            'Termin': termin_str
                        })
                    
                    new_row = pd.DataFrame({
                        'Task': [machine_name],
                        'Start': [start_time],
                        'Finish': [end_time],
                        'Resource': [machine_name],
                        'Type': [task['Type']],
                        'SiparisId': [task.get('siparisId', '')],
                        'SiparisDetayId': [task.get('siparisDetayId', '')],
                        'TipAd': [task.get('tipAd', '')],
                        'VaryantKodu': [task.get('varyantKodu', '')],
                        'UlakKodu': [task.get('ulakKodu', '')],
                        'Duration': [duration_str],
                        'Quantity': [quantity_str],
                        'Pick_Frequency': [pick_frequency if pick_frequency else ''],
                        'Description': [hover_text]
                    })
                    
                    df = pd.concat([df, new_row], ignore_index=True)
                        
                except Exception as e:
                    print(f"Hata oluştu (Makine {machine_name}): {str(e)}")
                    continue

        try:
            colors = {
                'varyant': 'rgb(144, 238, 144)',  # açık yeşil
                'takim': 'rgb(173, 216, 230)',    # açık mavi
                'change': 'rgb(220, 20, 60)',     # kızıl
                'ulak': 'rgb(238, 130, 238)'      # lila
            }

            fig = px.timeline(df, 
                            x_start="Start", 
                            x_end="Finish", 
                            y="Task", 
                            color="Type",
                            color_discrete_map=colors,
                            hover_data={
                                'SiparisId': True,
                                'SiparisDetayId': True,
                                'TipAd': True,
                                'VaryantKodu': True,
                                'UlakKodu': True,
                                'Type': True,
                                'Duration': True,
                                'Quantity': True,
                                'Pick_Frequency': True,
                                'Start': False,
                                'Finish': False,
                                'Task': False
                            },
                            labels={"Task": "Makine", "Type": "İş Tipi"})

            for trace in fig.data:
                if trace.name.lower() == 'change':
                    trace.hovertemplate = "<b>Tip Değişim:</b> %{customdata[5]}<br>" + \
                                        "<b>Süre:</b> %{customdata[6]}<extra></extra>"
                else:
                    trace.hovertemplate = (
                        "<b>Sipariş No:</b> %{customdata[0]}<br>" + \
                        "<b>Sipariş Detay No:</b> %{customdata[1]}<br>" + \
                        "<b>Tip:</b> %{customdata[2]}<br>" + \
                        "<b>Varyant Kodu:</b> %{customdata[3]}<br>" + \
                        "<b>Ulak Kodu:</b> %{customdata[4]}<br>" + \
                        "<b>Tip Değişim:</b> %{customdata[5]}<br>" + \
                        "<b>Süre:</b> %{customdata[6]}<br>" + \
                        "<b>Miktar:</b> %{customdata[7]} metre<br>" + \
                        "<b>Atkı Sıklığı:</b> %{customdata[8]}<extra></extra>"
                    )

            fig.update_layout(
                title="Üretim Çizelgesi",
                xaxis_title="Zaman",
                yaxis_title="Makineler",
                height=800,
                showlegend=True,
                legend_title="İş Tipi"
            )

            # HTML şablonu
            html_template = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Üretim Çizelgesi</title>
                <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.11.5/css/jquery.dataTables.css">
                <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/buttons/2.2.2/css/buttons.dataTables.min.css">
                <script type="text/javascript" src="https://code.jquery.com/jquery-3.5.1.min.js"></script>
                <script type="text/javascript" src="https://cdn.datatables.net/1.11.5/js/jquery.dataTables.min.js"></script>
                <script type="text/javascript" src="https://cdn.datatables.net/buttons/2.2.2/js/dataTables.buttons.min.js"></script>
                <script type="text/javascript" src="https://cdn.datatables.net/buttons/2.2.2/js/buttons.html5.min.js"></script>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    #gridContainer {{ margin-top: 30px; }}
                    .dataTables_wrapper {{ margin-top: 20px; }}
                    table.dataTable thead th {{ background-color: #f8f9fa; }}
                    table.dataTable tbody tr:hover {{ background-color: #f5f5f5; }}
                </style>
            </head>
            <body>
                <div id="ganttChart">
                    {gantt_div}
                </div>
                <div id="gridContainer">
                    <h2>Detaylı Üretim Planı</h2>
                    <table id="scheduleGrid" class="display" style="width:100%">
                        <thead>
                            <tr>
                                <th>Makine</th>
                                <th>İşlem Tipi</th>
                                <th>Başlangıç</th>
                                <th>Bitiş</th>
                                <th>Süre</th>
                                <th>Sipariş No</th>
                                <th>Sipariş Detay No</th>
                                <th>Tip</th>
                                <th>Varyant Kodu</th>
                                <th>Ulak Kodu</th>
                                <th>Miktar</th>
                                <th>Atkı Sıklığı</th>
                                <th>Termin</th>
                            </tr>
                        </thead>
                    </table>
                </div>
                <script>
                    $(document).ready(function() {{
                        var gridData = {grid_data};
                        $('#scheduleGrid').DataTable({{
                            data: gridData,
                            columns: [
                                {{ data: 'Makine' }},
                                {{ data: 'İşlem Tipi' }},
                                {{ data: 'Başlangıç' }},
                                {{ data: 'Bitiş' }},
                                {{ data: 'Süre' }},
                                {{ data: 'Sipariş No' }},
                                {{ data: 'Sipariş Detay No' }},
                                {{ data: 'Tip' }},
                                {{ data: 'Varyant Kodu' }},
                                {{ data: 'Ulak Kodu' }},
                                {{ data: 'Miktar' }},
                                {{ data: 'Atkı Sıklığı' }},
                                {{ data: 'Termin' }}
                            ],
                            dom: 'Bfrtip',
                            buttons: ['copy', 'csv', 'excel'],
                            pageLength: 25,
                            order: [[0, 'asc'], [2, 'asc']],
                            language: {{
                                url: 'https://cdn.datatables.net/plug-ins/1.11.5/i18n/tr.json'
                            }}
                        }});
                    }});
                </script>
            </body>
            </html>
            """

            # Gantt şemasını HTML'e çevir
            gantt_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
            grid_json = json.dumps(grid_data, ensure_ascii=False)
            
            # HTML şablonunu doldur ve kaydet
            complete_html = html_template.format(gantt_div=gantt_html, grid_data=grid_json)
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(complete_html)
            
        except Exception as e:
            print(f"Hata oluştu: {str(e)}")
            raise
    
    def save_gantt(self, fig, filename='schedule.html'):
        """Gantt şemasını HTML dosyası olarak kaydeder"""
        fig.write_html(filename) 
    
    def create_analysis_charts(self, debug_stats, filename='analiz.html'):
        """Optimizasyon analiz grafiklerini oluşturur"""
        
        # Alt grafikler için düzen oluştur
        fig = make_subplots(
            rows=2, cols=2,
            specs=[
                [{"type": "xy"}, {"type": "domain"}],  # İlk satır: normal grafik ve pasta grafik
                [{"type": "xy"}, {"type": "xy"}]       # İkinci satır: normal grafikler
            ],
            subplot_titles=(
                'Nesil Bazında İyileşme',
                'Tip Değişim Dağılımı',
                'Makine Yükü Dağılımı',
                'Makine Başına İş Dağılımı'
            )
        )
        
        # 1. Grafik: Nesil bazında iyileşme
        generations = [stat['generation'] for stat in debug_stats['generation_stats']]
        best_fitness = [stat['best_fitness'] for stat in debug_stats['generation_stats']]
        avg_fitness = [stat['avg_fitness'] for stat in debug_stats['generation_stats']]
        
        fig.add_trace(
            go.Scatter(x=generations, y=best_fitness, name='En İyi Fitness',
                      line=dict(color='green')),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=generations, y=avg_fitness, name='Ortalama Fitness',
                      line=dict(color='blue')),
            row=1, col=1
        )
        
        # 2. Grafik: Tip değişim pasta grafiği
        labels = list(debug_stats['type_changes'].keys())
        values = list(debug_stats['type_changes'].values())
        
        fig.add_trace(
            go.Pie(labels=labels, values=values,
                  marker=dict(colors=[self.colors[t.lower()] for t in labels])),
            row=1, col=2
        )
        
        # 3. Grafik: Makine yükü dağılımı
        machine_times = []
        machine_labels = []
        for machine_id, stats in debug_stats['machine_loads'].items():
            machine_labels.append(f"Makine {machine_id+1}")
            machine_times.append(stats['total_time'])
        
        fig.add_trace(
            go.Bar(x=machine_labels, y=machine_times,
                  marker_color='lightblue',
                  name='Toplam Süre'),
            row=2, col=1
        )
        
        # 4. Grafik: Makine başına iş sayısı
        job_counts = []
        for machine_id, stats in debug_stats['machine_loads'].items():
            job_counts.append(stats['job_count'])
        
        fig.add_trace(
            go.Bar(x=machine_labels, y=job_counts,
                  marker_color='lightgreen',
                  name='İş Sayısı'),
            row=2, col=2
        )
        
        # Grafik düzenlemeleri
        fig.update_layout(
            height=800,
            showlegend=True,
            title_text="Optimizasyon Analiz Grafikleri",
            title_x=0.5,  # Başlığı ortala
        )
        
        # X ve Y ekseni başlıkları
        fig.update_xaxes(title_text="Nesil", row=1, col=1)
        fig.update_yaxes(title_text="Fitness Değeri", row=1, col=1)
        
        fig.update_xaxes(title_text="Makine", row=2, col=1)
        fig.update_yaxes(title_text="Toplam Süre (Saat)", row=2, col=1)
        
        fig.update_xaxes(title_text="Makine", row=2, col=2)
        fig.update_yaxes(title_text="İş Sayısı", row=2, col=2)
        
        # Pasta grafiği için düzenleme
        fig.update_traces(
            hole=.4,  # Ortada boşluk bırak (donut chart görünümü)
            hoverinfo="label+percent+value",
            textinfo="percent+label",
            row=1, col=2
        )
        
        # Grafiği HTML olarak kaydet
        fig.write_html(filename)
        print(f"Analiz grafikleri {filename} dosyasına kaydedildi.") 