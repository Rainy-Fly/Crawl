import threading
import time
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from models import CrawlerTask, CrawlerResult

class CrawlerService:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        self.running_tasks = {}
        self.task_threads = {}
        self.task_paused = {}
    
    def start_task(self, task_id, config):
        """立即启动爬虫任务"""
        print(f"[DEBUG] Starting task {task_id}")
        task = CrawlerTask.get_by_id(task_id)
        if not task:
            print(f"[DEBUG] Task {task_id} not found")
            return False
        
        task.start()
        
        thread = threading.Thread(target=self._run_crawler, args=(task_id, config))
        thread.daemon = True
        thread.start()
        
        self.task_threads[task_id] = thread
        self.task_paused[task_id] = False
        
        return True
    
    def schedule_task(self, task_id, config, time_config):
        """定时启动爬虫任务"""
        task = CrawlerTask.get_by_id(task_id)
        if not task:
            return False
        
        cron_expr = time_config.get('cron', '0 0 * * *')
        minute, hour, day, month, day_of_week = cron_expr.split()
        
        trigger = CronTrigger(
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week
        )
        
        self.scheduler.add_job(
            func=self.start_task,
            trigger=trigger,
            args=[task_id, config],
            id=str(task_id),
            replace_existing=True
        )
        
        return True
    
    def pause_task(self, task_id):
        """暂停任务"""
        if task_id in self.task_paused:
            self.task_paused[task_id] = True
        return True
    
    def resume_task(self, task_id, config):
        """恢复任务"""
        if task_id in self.task_paused:
            self.task_paused[task_id] = False
            if task_id not in self.task_threads or not self.task_threads[task_id].is_alive():
                thread = threading.Thread(target=self._run_crawler, args=(task_id, config))
                thread.daemon = True
                thread.start()
                self.task_threads[task_id] = thread
        return True
    
    def stop_task(self, task_id):
        """停止任务"""
        self.task_paused[task_id] = True
        
        try:
            self.scheduler.remove_job(str(task_id))
        except:
            pass
        
        task = CrawlerTask.get_by_id(task_id)
        if task:
            task.stop()
        
        return True
    
    def _run_crawler(self, task_id, config):
        """执行爬虫"""
        print(f"[DEBUG] _run_crawler started for task {task_id}")
        print(f"[DEBUG] Config type: {type(config)}")
        print(f"[DEBUG] Config content: {config}")
        
        try:
            urls = config.get('urls', [])
            selectors = config.get('selectors', {})
            headers = config.get('headers', {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            # 确保 delay 是数字（支持嵌套配置 {min, max, random}）
            delay = config.get('delay', 1)
            if isinstance(delay, dict):
                # 如果是嵌套配置，使用 min 值作为默认延迟
                delay = delay.get('min', 3)
            try:
                delay = float(delay)
            except (ValueError, TypeError):
                delay = 3
            
            # 确保 max_pages 是整数
            max_pages = config.get('max_pages', 10)
            if isinstance(max_pages, dict):
                max_pages = 10
            try:
                max_pages = int(max_pages)
            except (ValueError, TypeError):
                max_pages = 10
            
            # 获取超时和重试配置
            timeout = config.get('timeout', 30)
            if isinstance(timeout, dict):
                timeout = 30
            try:
                timeout = int(timeout)
            except (ValueError, TypeError):
                timeout = 30
            
            retry_times = config.get('retry_times', 3)
            if isinstance(retry_times, dict):
                retry_times = 3
            try:
                retry_times = int(retry_times)
            except (ValueError, TypeError):
                retry_times = 3
            
            retry_delay = config.get('retry_delay', 5)
            if isinstance(retry_delay, dict):
                retry_delay = 5
            try:
                retry_delay = int(retry_delay)
            except (ValueError, TypeError):
                retry_delay = 5
            
            print(f"[DEBUG] URLs: {urls}")
            print(f"[DEBUG] Selectors: {selectors}")
            
            results = []
            pages_crawled = 0
            
            for url in urls:
                print(f"[DEBUG] Processing URL: {url}")
                
                if self.task_paused.get(task_id, False):
                    print(f"[DEBUG] Task {task_id} is paused, breaking")
                    break
                
                if pages_crawled >= max_pages:
                    print(f"[DEBUG] Max pages reached")
                    break
                
                try:
                    print(f"[DEBUG] Sending request to {url} with timeout {timeout}")
                    
                    # 实现重试机制
                    response = None
                    for attempt in range(retry_times):
                        try:
                            print(f"[DEBUG] Attempt {attempt + 1}/{retry_times}")
                            response = requests.get(url, headers=headers, timeout=timeout)
                            response.encoding = response.apparent_encoding
                            print(f"[DEBUG] Response status: {response.status_code}")
                            break  # 成功则跳出重试循环
                        except requests.exceptions.Timeout:
                            print(f"[WARN] Timeout on attempt {attempt + 1}")
                            if attempt < retry_times - 1:
                                print(f"[DEBUG] Waiting {retry_delay} seconds before retry...")
                                time.sleep(retry_delay)
                            else:
                                raise  # 最后一次重试失败，抛出异常
                    
                    if response is None:
                        raise Exception("All retry attempts failed")
                    
                    print(f"[DEBUG] Parsing HTML with BeautifulSoup")
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    page_data = {
                        'url': url,
                        'title': soup.title.string if soup.title else '',
                        'data': {}
                    }
                    print(f"[DEBUG] Page title: {page_data['title']}")
                    
                    print(f"[DEBUG] Processing selectors: {selectors}")
                    for key, selector in selectors.items():
                        print(f"[DEBUG] Selector key: {key}, selector: {selector}")
                        print(f"[DEBUG] Selector type: {type(selector)}")
                        
                        # 处理嵌套选择器（如 book_info: {author: ".info a"}）
                        if isinstance(selector, dict):
                            print(f"[DEBUG] Nested selector detected for key: {key}")
                            nested_data = {}
                            for nested_key, nested_selector in selector.items():
                                if isinstance(nested_selector, str):
                                    try:
                                        elements = soup.select(nested_selector)
                                        print(f"[DEBUG] Found {len(elements)} elements for nested selector '{nested_selector}'")
                                        nested_data[nested_key] = [elem.get_text(strip=True) for elem in elements]
                                    except Exception as nested_error:
                                        print(f"[ERROR] Error with nested selector '{nested_selector}': {nested_error}")
                                        nested_data[nested_key] = []
                                else:
                                    nested_data[nested_key] = []
                            page_data['data'][key] = nested_data
                        elif isinstance(selector, str):
                            # 简单选择器
                            try:
                                elements = soup.select(selector)
                                print(f"[DEBUG] Found {len(elements)} elements for selector '{selector}'")
                                page_data['data'][key] = [elem.get_text(strip=True) for elem in elements]
                            except Exception as selector_error:
                                print(f"[ERROR] Error with selector '{selector}': {selector_error}")
                                import traceback
                                print(traceback.format_exc())
                                page_data['data'][key] = []
                        else:
                            print(f"[ERROR] Unknown selector type: {type(selector)}")
                            page_data['data'][key] = []
                    
                    results.append(page_data)
                    pages_crawled += 1
                    print(f"[DEBUG] Page data appended. Total results: {len(results)}")
                    
                    time.sleep(delay)
                    
                except Exception as e:
                    import traceback
                    error_msg = f"{str(e)}\n{traceback.format_exc()}"
                    print(f"[ERROR] Crawler error for URL {url}: {error_msg}")
                    results.append({
                        'url': url,
                        'error': str(e)
                    })
            
            print(f"[DEBUG] Crawling finished. Total results: {len(results)}")
            
            if not self.task_paused.get(task_id, False):
                print(f"[DEBUG] Completing task {task_id}")
                task = CrawlerTask.get_by_id(task_id)
                if task:
                    task.complete()
                
                print(f"[DEBUG] Saving results to database")
                print(f"[DEBUG] Results type: {type(results)}")
                print(f"[DEBUG] Results content: {results[:2] if len(results) > 2 else results}")
                
                try:
                    CrawlerResult.create(task_id, results)
                    print(f"[DEBUG] Results saved successfully")
                except Exception as save_error:
                    print(f"[ERROR] Error saving results: {save_error}")
                    import traceback
                    print(traceback.format_exc())
                    
        except Exception as e:
            print(f"[ERROR] Crawler error for task {task_id}: {e}")
            import traceback
            print(traceback.format_exc())
            task = CrawlerTask.get_by_id(task_id)
            if task:
                task.stop()
