import requests
import json
import os
from typing import Dict, Any, Optional


class AIModelCaller:
    """AI模型调用类，支持本地模型和API调用"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化AI模型调用器
        
        Args:
            config: 配置字典，包含:
                - config_type: 'local' 或 'api'
                - base_url: API基础URL
                - api_key: API密钥
                - model_name: 模型名称
        """
        self.config = config or {}
        self.config_type = self.config.get('config_type', 'local')
        self.base_url = self.config.get('base_url', 'http://localhost:8000/v1/chat/completions')
        self.api_key = self.config.get('api_key', '')
        self.model_name = self.config.get('model_name', 'default-model')
        
        # 本地模型默认路径
        self.local_model_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'AiModel'
        )
    
    def clean_and_analyze_data(self, crawler_data: Any, task_type: str = "general") -> Dict[str, Any]:
        """
        清理和分析爬虫数据
        
        Args:
            crawler_data: 原始爬虫数据
            task_type: 任务类型 (general, sentiment, keyword, summary)
        
        Returns:
            包含清理后数据和分析结果的字典
        """
        # 构建提示词
        prompt = self._build_prompt(crawler_data, task_type)
        
        try:
            # 根据配置类型选择调用方式
            if self.config_type == 'api':
                response = self._call_api_model(prompt)
            else:
                response = self._call_local_model(prompt)
            
            # 解析返回结果
            result = self._parse_response(response, crawler_data)
            
            return {
                "success": True,
                "data": result,
                "original_count": len(crawler_data) if isinstance(crawler_data, list) else 1,
                "task_type": task_type,
                "model_type": self.config_type
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "data": None
            }
    
    def _build_prompt(self, data: Any, task_type: str) -> str:
        """构建发送给AI模型的提示词"""
        
        data_str = json.dumps(data, ensure_ascii=False, indent=2) if isinstance(data, (dict, list)) else str(data)
        
        prompts = {
            "general": f"""请对以下爬虫数据进行清理和分析：

原始数据：
{data_str}

请完成以下任务：
1. 清理数据：去除无效、重复、格式错误的数据
2. 提取关键信息：识别并提取主要内容
3. 数据分类：对数据进行合理分类
4. 统计分析：提供数据统计信息

请以JSON格式返回结果，包含以下字段：
- cleaned_data: 清理后的数据列表
- categories: 分类结果
- statistics: 统计信息
- keywords: 提取的关键词列表（包含word、weight、count字段）
- wordcloud_data: 词云数据（包含word、weight、count字段）
""",
            "sentiment": f"""请对以下爬虫数据进行情感分析：

原始数据：
{data_str}

请完成以下任务：
1. 对每个文本内容进行情感分析（正面/负面/中性）
2. 统计各类情感的比例
3. 提取情感强烈的代表性内容

请以JSON格式返回结果，包含以下字段：
- sentiment_results: 每条数据的情感分析结果
- sentiment_distribution: 情感分布统计（正面、中性、负面的数量或百分比）
- key_positive: 关键正面内容
- key_negative: 关键负面内容
- keywords: 提取的关键词列表
""",
            "keyword": f"""请对以下爬虫数据进行关键词提取：

原始数据：
{data_str}

请完成以下任务：
1. 提取高频关键词
2. 识别关键短语
3. 生成词云数据（词和权重）
4. 分析关键词之间的关联

请以JSON格式返回结果，包含以下字段：
- keywords: 关键词列表（包含word、weight、count字段）
- phrases: 关键短语列表
- wordcloud_data: 词云数据（包含word、weight、count字段）
- keyword_relations: 关键词关联分析
- categories: 按关键词分类的结果
""",
            "summary": f"""请对以下爬虫数据进行摘要总结：

原始数据：
{data_str}

请完成以下任务：
1. 生成整体内容摘要
2. 提取关键要点
3. 识别主要主题
4. 生成时间线（如有时间信息）

请以JSON格式返回结果，包含以下字段：
- summary: 内容摘要
- key_points: 关键要点列表
- themes: 主题列表
- timeline: 时间线数据（包含time/date和value/count字段）
- keywords: 提取的关键词列表
- statistics: 统计信息
"""
        }
        
        return prompts.get(task_type, prompts["general"])
    
    def _call_local_model(self, prompt: str) -> str:
        """调用本地AI模型"""
        
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model_name or "local-model",
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个专业的数据分析师，擅长清理和分析爬虫数据。请确保返回的结果是可以解析的JSON格式。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 4096
        }
        
        try:
            response = requests.post(
                api_url,
                headers=headers,
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except requests.exceptions.ConnectionError:
            # 如果本地模型不可用，返回模拟数据
            print(f"警告: 无法连接到本地模型 {self.base_url}，使用模拟数据")
            return self._generate_mock_response(prompt)
        except Exception as e:
            raise Exception(f"调用本地模型失败: {str(e)}")
    
    def _call_api_model(self, prompt: str) -> str:
        """调用API模型"""
        
        # 检查API Key
        if not self.api_key:
            raise Exception("API Key 不能为空，请检查配置")
        
        # 构建完整的API URL
        api_url = self.base_url
        # 如果base_url不以/chat/completions结尾，自动添加/v1/chat/completions
        if not api_url.endswith('/chat/completions'):
            # 移除末尾的斜杠
            api_url = api_url.rstrip('/')
            # 添加完整路径
            if not api_url.endswith('/v1'):
                api_url += '/v1'
            api_url += '/chat/completions'
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个专业的数据分析师，擅长清理和分析爬虫数据。请确保返回的结果是可以解析的JSON格式。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 4096
        }
        
        try:
            print(f"[DEBUG] 原始Base URL: {self.base_url}")
            print(f"[DEBUG] 实际调用API: {api_url}")
            print(f"[DEBUG] 模型: {self.model_name}")
            print(f"[DEBUG] API Key前10位: {self.api_key[:10] if len(self.api_key) > 10 else self.api_key}...")
            
            response = requests.post(
                api_url,
                headers=headers,
                json=payload,
                timeout=120
            )
            
            # 打印响应状态
            print(f"[DEBUG] 响应状态码: {response.status_code}")
            
            response.raise_for_status()
            
            result = response.json()
            
            # 处理不同API的响应格式
            if "choices" in result:
                return result["choices"][0]["message"]["content"]
            elif "output" in result:
                # 某些API可能使用不同的格式
                return result["output"]["text"]
            else:
                return str(result)
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                raise Exception(f"API授权失败(401): 请检查API Key是否正确。当前Key: {self.api_key[:10]}...")
            elif response.status_code == 403:
                raise Exception(f"API访问被拒绝(403): 请检查API Key是否有权限访问该模型")
            elif response.status_code == 429:
                raise Exception(f"API请求过于频繁(429): 请稍后再试")
            else:
                raise Exception(f"API请求失败({response.status_code}): {str(e)}")
        except Exception as e:
            raise Exception(f"调用API模型失败: {str(e)}")
    
    def _parse_response(self, response: str, original_data: Any) -> Dict[str, Any]:
        """解析AI模型的返回结果"""
        
        try:
            # 尝试直接解析JSON
            result = json.loads(response)
            return result
        except json.JSONDecodeError:
            # 如果返回的不是纯JSON，尝试提取JSON部分
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass
            
            # 如果无法解析，返回结构化数据
            return {
                "cleaned_data": original_data if isinstance(original_data, list) else [original_data],
                "raw_response": response,
                "parse_error": True,
                "keywords": [],
                "categories": {},
                "statistics": {}
            }
    
    def _generate_mock_response(self, prompt: str) -> str:
        """生成模拟响应（当模型不可用时）"""
        
        # 根据提示词类型返回不同的模拟数据
        if "情感" in prompt or "sentiment" in prompt.lower():
            return json.dumps({
                "sentiment_results": [
                    {"text": "示例内容1", "sentiment": "正面", "score": 0.85},
                    {"text": "示例内容2", "sentiment": "中性", "score": 0.5},
                    {"text": "示例内容3", "sentiment": "负面", "score": 0.2}
                ],
                "sentiment_distribution": {
                    "正面": 40,
                    "中性": 35,
                    "负面": 25
                },
                "key_positive": ["优秀的产品质量", "出色的服务"],
                "key_negative": ["物流速度慢", "包装破损"],
                "keywords": [
                    {"word": "产品", "weight": 0.95, "count": 120},
                    {"word": "服务", "weight": 0.88, "count": 98},
                    {"word": "质量", "weight": 0.82, "count": 85}
                ]
            }, ensure_ascii=False)
        
        elif "关键词" in prompt or "keyword" in prompt.lower():
            return json.dumps({
                "keywords": [
                    {"word": "产品", "weight": 0.95, "count": 120},
                    {"word": "服务", "weight": 0.88, "count": 98},
                    {"word": "质量", "weight": 0.82, "count": 85},
                    {"word": "价格", "weight": 0.75, "count": 72},
                    {"word": "物流", "weight": 0.68, "count": 65},
                    {"word": "包装", "weight": 0.60, "count": 55},
                    {"word": "客服", "weight": 0.55, "count": 50},
                    {"word": "体验", "weight": 0.50, "count": 45}
                ],
                "phrases": ["产品质量", "客户服务", "物流速度", "购物体验"],
                "wordcloud_data": [
                    {"word": "产品", "weight": 100, "count": 120},
                    {"word": "服务", "weight": 82, "count": 98},
                    {"word": "质量", "weight": 71, "count": 85},
                    {"word": "价格", "weight": 60, "count": 72},
                    {"word": "物流", "weight": 54, "count": 65},
                    {"word": "包装", "weight": 46, "count": 55},
                    {"word": "客服", "weight": 42, "count": 50},
                    {"word": "体验", "weight": 38, "count": 45}
                ],
                "keyword_relations": [
                    {"source": "产品", "target": "质量", "strength": 0.8},
                    {"source": "服务", "target": "物流", "strength": 0.6},
                    {"source": "价格", "target": "产品", "strength": 0.7}
                ],
                "categories": {
                    "产品相关": 45,
                    "服务相关": 35,
                    "物流相关": 25,
                    "价格相关": 20
                }
            }, ensure_ascii=False)
        
        else:
            return json.dumps({
                "cleaned_data": [
                    {"title": "示例数据1", "content": "清理后的内容1", "category": "类别A"},
                    {"title": "示例数据2", "content": "清理后的内容2", "category": "类别B"},
                    {"title": "示例数据3", "content": "清理后的内容3", "category": "类别A"}
                ],
                "categories": {
                    "类别A": 25,
                    "类别B": 20,
                    "类别C": 10
                },
                "statistics": {
                    "total_count": 55,
                    "valid_count": 50,
                    "duplicate_count": 3,
                    "invalid_count": 2
                },
                "keywords": [
                    {"word": "关键词1", "weight": 0.9, "count": 100},
                    {"word": "关键词2", "weight": 0.8, "count": 85},
                    {"word": "关键词3", "weight": 0.7, "count": 70}
                ],
                "wordcloud_data": [
                    {"word": "关键词1", "weight": 100, "count": 100},
                    {"word": "关键词2", "weight": 85, "count": 85},
                    {"word": "关键词3", "weight": 70, "count": 70}
                ],
                "summary": "这是数据的整体摘要",
                "key_points": ["要点1", "要点2", "要点3"],
                "themes": ["主题A", "主题B", "主题C"]
            }, ensure_ascii=False)
    
    def batch_process(self, data_list: list, batch_size: int = 10) -> list:
        """批量处理数据"""
        
        results = []
        for i in range(0, len(data_list), batch_size):
            batch = data_list[i:i + batch_size]
            result = self.clean_and_analyze_data(batch)
            results.append(result)
        
        return results


# 便捷函数
def analyze_crawler_data(data: Any, task_type: str = "general", config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    便捷函数：分析爬虫数据
    
    Args:
        data: 爬虫数据
        task_type: 分析类型 (general, sentiment, keyword, summary)
        config: AI配置字典，如果不提供则使用本地默认配置
    
    Returns:
        分析结果
    """
    caller = AIModelCaller(config)
    return caller.clean_and_analyze_data(data, task_type)


def extract_keywords(data: Any, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """便捷函数：提取关键词"""
    return analyze_crawler_data(data, "keyword", config)


def analyze_sentiment(data: Any, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """便捷函数：情感分析"""
    return analyze_crawler_data(data, "sentiment", config)


def summarize_data(data: Any, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """便捷函数：数据摘要"""
    return analyze_crawler_data(data, "summary", config)
