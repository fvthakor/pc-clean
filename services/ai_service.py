"""AI / ML Frameworks, Model Weights, and CLI Assistants Scanner."""

import logging

from app.constants import SafetyLevel
from app.paths import get_roaming_appdata, get_user_home
from models.developer_tool import DeveloperTool, DevPackage
from utils.filesystem import get_dir_size_and_count

logger = logging.getLogger("PcClean.AIService")


class AIService:
    @classmethod
    def scan(cls) -> list[DeveloperTool]:
        tools: list[DeveloperTool] = []
        user_home = get_user_home()
        roaming = get_roaming_appdata()

        # 1. Hugging Face Hub Model Cache
        hf_hub = user_home / ".cache" / "huggingface" / "hub"
        if hf_hub.exists():
            size, files, _ = get_dir_size_and_count(hf_hub)
            models: list[DevPackage] = []
            try:
                for m in hf_hub.iterdir():
                    if m.is_dir() and m.name.startswith("models--"):
                        m_size, _, _ = get_dir_size_and_count(m)
                        clean_name = m.name.replace("models--", "").replace("--", "/")
                        models.append(
                            DevPackage(
                                name=clean_name,
                                version="hub",
                                size=m_size,
                                path=m,
                                is_active=True,
                                description=f"Hugging Face Model: {clean_name}",
                            )
                        )
            except Exception:
                pass

            tools.append(
                DeveloperTool(
                    ecosystem="AI/ML",
                    name="Hugging Face Hub Cache",
                    version="Models",
                    path=hf_hub,
                    size=size,
                    status="ACTIVE MODEL",
                    safety_level=SafetyLevel.IMPORTANT,
                    description=f"Hugging Face models ({len(models)} cached models)",
                    is_active=True,
                    explanation=(
                        "Hugging Face model weights and tokenizers. Deleting will require re-downloading "
                        "multi-gigabyte weights on the next inference or training run."
                    ),
                    packages=models,
                )
            )

        # 2. Ollama Local LLM Models
        ollama_models = user_home / ".ollama" / "models"
        if ollama_models.exists():
            size, files, _ = get_dir_size_and_count(ollama_models)
            tools.append(
                DeveloperTool(
                    ecosystem="AI/ML",
                    name="Ollama LLM Models",
                    version="Local Models",
                    path=ollama_models,
                    size=size,
                    status="ACTIVE MODEL",
                    safety_level=SafetyLevel.IMPORTANT,
                    description="Local Ollama quantized LLM models (blobs & manifests)",
                    is_active=True,
                    explanation="Local LLM weights used by Ollama. Removing them requires 'ollama pull' to re-download.",
                    packages=[],
                )
            )

        # 3. PyTorch Model Cache
        torch_cache = user_home / ".cache" / "torch"
        if torch_cache.exists():
            size, _, _ = get_dir_size_and_count(torch_cache)
            tools.append(
                DeveloperTool(
                    ecosystem="AI/ML",
                    name="PyTorch Checkpoint Cache",
                    version="Cache",
                    path=torch_cache,
                    size=size,
                    status="CACHE",
                    safety_level=SafetyLevel.REVIEW,
                    description="PyTorch hub checkpoints and cached pretrained weights",
                    is_active=False,
                    explanation="Pretrained weights downloaded via torchvision / PyTorch hub. Can be redownloaded on demand.",
                    packages=[],
                )
            )

        # 4. Claude Code & Desktop Cache (Strictly preserving config/skills)
        claude_dir = user_home / ".claude"
        if claude_dir.exists():
            size, _, _ = get_dir_size_and_count(claude_dir)
            tools.append(
                DeveloperTool(
                    ecosystem="AI/ML",
                    name="Claude Code Environment",
                    version="CLI",
                    path=claude_dir,
                    size=size,
                    status="IMPORTANT",
                    safety_level=SafetyLevel.BLOCKED,
                    description="Claude Code config, memory, authentication, and skills",
                    is_active=True,
                    explanation="CRITICAL: Contains your Claude CLI credentials, conversation memories, and custom skills. DO NOT DELETE.",
                    packages=[],
                )
            )

        # Claude Desktop Cache
        claude_desktop_cache = roaming / "Claude" / "Cache"
        if claude_desktop_cache.exists():
            size, _, _ = get_dir_size_and_count(claude_desktop_cache)
            if size > 0:
                tools.append(
                    DeveloperTool(
                        ecosystem="AI/ML",
                        name="Claude Desktop Cache",
                        version="Cache",
                        path=claude_desktop_cache,
                        size=size,
                        status="CACHE",
                        safety_level=SafetyLevel.SAFE,
                        description="Claude Desktop Electron HTTP cache",
                        is_active=False,
                        explanation="Temporary web cache for Claude Desktop. Safe to clear; credentials and chats are stored on the server.",
                        packages=[],
                    )
                )

        return tools
