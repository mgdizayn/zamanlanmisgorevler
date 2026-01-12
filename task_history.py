# task_history.py - Görev Geçmişi Yöneticisi
"""
MGD Task Scheduler Pro v4.0 - Task History Manager
Author: Mustafa GÜNEŞDOĞDU (MGdizayn)
Support: Ahmet KAHREMAN (CMX)
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict


@dataclass
class TaskHistoryRecord:
    """Görev çalıştırma kaydı."""
    id: str
    task_id: str
    task_name: str
    start_time: str
    end_time: str
    duration: float
    success: bool
    exit_code: int
    error_message: str = ""
    output: str = ""
    
    def to_dict(self):
        return asdict(self)


class TaskHistoryManager:
    """Görev geçmişi yönetim sınıfı."""
    
    def __init__(self, history_dir: str = "history"):
        self.history_dir = Path(history_dir)
        self.history_dir.mkdir(exist_ok=True)
        self.current_file = self.history_dir / f"history_{datetime.now().strftime('%Y%m')}.json"
    
    def add_record(self, record: TaskHistoryRecord):
        """Yeni kayıt ekle."""
        records = self.load_current_month()
        records.append(record.to_dict())
        
        try:
            with open(self.current_file, 'w', encoding='utf-8') as f:
                json.dump(records, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"History add error: {e}")
    
    def load_current_month(self) -> List[Dict]:
        """Bu ayın kayıtlarını yükle."""
        if self.current_file.exists():
            try:
                with open(self.current_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def get_task_history(self, task_id: str, days: int = 30) -> List[Dict]:
        """Belirli bir görevin geçmişi."""
        all_records = self.load_all_recent(days)
        return [r for r in all_records if r.get('task_id') == task_id]
    
    def load_all_recent(self, days: int = 30) -> List[Dict]:
        """Son X günün kayıtlarını yükle."""
        cutoff_date = datetime.now() - timedelta(days=days)
        all_records = []
        
        for file in sorted(self.history_dir.glob("history_*.json"), reverse=True):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    records = json.load(f)
                    for record in records:
                        start_time = datetime.strptime(record['start_time'], '%Y-%m-%d %H:%M:%S')
                        if start_time >= cutoff_date:
                            all_records.append(record)
            except:
                continue
        
        return sorted(all_records, key=lambda x: x['start_time'], reverse=True)
    
    def get_statistics(self, days: int = 30) -> Dict:
        """İstatistikler."""
        records = self.load_all_recent(days)
        
        total = len(records)
        success = sum(1 for r in records if r.get('success', False))
        failed = total - success
        
        total_duration = sum(r.get('duration', 0) for r in records)
        avg_duration = total_duration / total if total > 0 else 0
        
        # Görev başına istatistikler
        task_stats = {}
        for record in records:
            task_id = record.get('task_id')
            if task_id not in task_stats:
                task_stats[task_id] = {
                    'name': record.get('task_name', 'Unknown'),
                    'total': 0,
                    'success': 0,
                    'failed': 0,
                    'total_duration': 0
                }
            
            task_stats[task_id]['total'] += 1
            if record.get('success', False):
                task_stats[task_id]['success'] += 1
            else:
                task_stats[task_id]['failed'] += 1
            task_stats[task_id]['total_duration'] += record.get('duration', 0)
        
        return {
            'total_runs': total,
            'success': success,
            'failed': failed,
            'success_rate': (success / total * 100) if total > 0 else 0,
            'total_duration': total_duration,
            'avg_duration': avg_duration,
            'task_stats': task_stats
        }
    
    def cleanup_old_records(self, keep_days: int = 30):
        """Eski kayıtları temizle."""
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        cutoff_month = cutoff_date.strftime('%Y%m')
        
        for file in self.history_dir.glob("history_*.json"):
            file_month = file.stem.split('_')[1]
            if file_month < cutoff_month:
                try:
                    file.unlink()
                    print(f"Deleted old history file: {file.name}")
                except Exception as e:
                    print(f"Failed to delete {file.name}: {e}")
    
    def export_to_csv(self, output_path: str, days: int = 30) -> bool:
        """CSV olarak dışa aktar."""
        import csv
        
        records = self.load_all_recent(days)
        
        try:
            with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
                if not records:
                    return False
                
                fieldnames = ['task_name', 'start_time', 'end_time', 'duration', 'success', 'exit_code', 'error_message']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                writer.writeheader()
                for record in records:
                    writer.writerow({k: record.get(k, '') for k in fieldnames})
            
            return True
        except Exception as e:
            print(f"CSV export error: {e}")
            return False
    
    def get_most_failed_tasks(self, limit: int = 5) -> List[Dict]:
        """En çok başarısız olan görevler."""
        stats = self.get_statistics(30)
        task_stats = stats.get('task_stats', {})
        
        failed_tasks = [
            {
                'task_id': task_id,
                'name': data['name'],
                'failed_count': data['failed'],
                'total': data['total'],
                'failure_rate': (data['failed'] / data['total'] * 100) if data['total'] > 0 else 0
            }
            for task_id, data in task_stats.items()
            if data['failed'] > 0
        ]
        
        return sorted(failed_tasks, key=lambda x: x['failure_rate'], reverse=True)[:limit]
    
    def get_longest_running_tasks(self, limit: int = 5) -> List[Dict]:
        """En uzun süren görevler."""
        stats = self.get_statistics(30)
        task_stats = stats.get('task_stats', {})
        
        long_tasks = [
            {
                'task_id': task_id,
                'name': data['name'],
                'avg_duration': data['total_duration'] / data['total'] if data['total'] > 0 else 0,
                'total_runs': data['total']
            }
            for task_id, data in task_stats.items()
        ]
        
        return sorted(long_tasks, key=lambda x: x['avg_duration'], reverse=True)[:limit]
