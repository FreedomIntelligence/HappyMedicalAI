# models.py
import os
import yaml

from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.embeddings import Embeddings

class ModelProvider:
    """模型提供商基类"""
    def __init__(self, config):
        self.config = config

    def get_chat_model(self, model_name: str) -> BaseChatModel:
        """获取聊天模型"""
        raise NotImplementedError

    def get_embedding_model(self, model_name: str) -> Embeddings:
        """获取嵌入模型"""
        raise NotImplementedError

class OllamaProvider(ModelProvider):
    """Ollama本地模型提供商"""
    def get_chat_model(self, model_name: str) -> BaseChatModel:
        return ChatOllama(
            model=model_name,
            base_url=self.config.get("base_url", "http://localhost:11434")
        )

    def get_embedding_model(self, model_name: str) -> Embeddings:
        return OllamaEmbeddings(
            model=model_name,
            base_url=self.config.get("base_url", "http://localhost:11434")
        )

class OpenAICompatibleProvider(ModelProvider):
    """兼容OpenAI API格式的提供商（如Qwen、DeepSeek等）"""
    def get_chat_model(self, model_name: str) -> BaseChatModel:
        return ChatOpenAI(
            model=model_name,
            api_key=self.config.get("api_key"),
            base_url=self.config.get("base_url")
        )

    def get_embedding_model(self, model_name: str) -> Embeddings:
        return OpenAIEmbeddings(
            model=model_name,
            api_key=self.config.get("api_key"),
            base_url=self.config.get("base_url")
        )

class ModelManager:
    """模型管理器，统一管理不同提供商的模型"""
    def __init__(self, config_path: str = "config.yaml"):
        # 加载配置文件
        self.config = self.load_config(config_path)

        # 注册模型提供商
        self.providers = {
            "ollama": OllamaProvider(self.config.get("ollama", {})),
            "qwen": OpenAICompatibleProvider(self.config.get("qwen", {})),
            "deepseek": OpenAICompatibleProvider(self.config.get("deepseek", {})),
            "seed-doubao": OpenAICompatibleProvider(self.config.get("seed-doubao", {})),
            "zhipu": OpenAICompatibleProvider(self.config.get("zhipu", {}))
        }

        # 缓存可用的模型信息
        self.available_providers = self._get_available_providers()

    def load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件 {config_path} 不存在")

        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _get_available_providers(self) -> dict:
        """获取可用的模型提供商及其模型"""
        available = {}

        for provider_name, provider_config in self.config.items():
            # Ollama不需要API密钥
            if provider_name == "ollama":
                available[provider_name] = {
                    "chat_models": provider_config.get("chat_models", []),
                    "embedding_models": provider_config.get("embedding_models", []),
                    "available": True
                }
            else:
                # 其他提供商需要检查API密钥是否配置
                api_key = provider_config.get("api_key", "").strip()
                available[provider_name] = {
                    "chat_models": provider_config.get("chat_models", []),
                    "embedding_models": provider_config.get("embedding_models", []),
                    "available": len(api_key) > 0
                }

        return available

    def get_provider(self, provider_name: str) -> ModelProvider:
        """获取指定的模型提供商"""
        if provider_name not in self.providers:
            raise ValueError(f"不支持的模型提供商: {provider_name}")

        return self.providers[provider_name]

    def get_chat_model(self, provider_name: str, model_name: str) -> BaseChatModel:
        """获取指定提供商的聊天模型"""
        provider = self.get_provider(provider_name)
        return provider.get_chat_model(model_name)

    def get_embedding_model(self, provider_name: str, model_name: str) -> Embeddings:
        """获取指定提供商的嵌入模型"""
        provider = self.get_provider(provider_name)
        return provider.get_embedding_model(model_name)

    def get_default_chat_model(self, provider_name: str) -> str:
        """获取指定提供商的默认聊天模型"""
        for model in self.available_providers[provider_name]["chat_models"]:
            if model.get("default", False):
                return model["name"]
        # 如果没有默认模型，返回第一个
        if self.available_providers[provider_name]["chat_models"]:
            return self.available_providers[provider_name]["chat_models"][0]["name"]
        return None

    def get_default_embedding_model(self, provider_name: str) -> str:
        """获取指定提供商的默认嵌入模型"""
        for model in self.available_providers[provider_name]["embedding_models"]:
            if model.get("default", False):
                return model["name"]
        # 如果没有默认模型，返回第一个
        if self.available_providers[provider_name]["embedding_models"]:
            return self.available_providers[provider_name]["embedding_models"][0]["name"]
        return None