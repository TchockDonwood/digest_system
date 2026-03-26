import aiohttp
import asyncio
from typing import List, Optional

ollama_semaphore = asyncio.Semaphore(2)

class SaigaSummarizer:
    def __init__(self, model_name: str, host: str = "http://localhost:11434"):
        self.model_name = model_name
        self.host = host

    def _create_prompt(self, system: str, user: str) -> str:
        return f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
{system}<|eot_id|>
<|start_header_id|>user<|end_header_id|>
{user}<|eot_id|>
<|start_header_id|>assistant<|end_header_id|>"""

    async def _call_ollama(self, prompt: str, temperature: float = 0.3, max_tokens: int = 500, retries: int = 2) -> str:
        async with ollama_semaphore:
            for attempt in range(retries + 1):
                try:
                    async with aiohttp.ClientSession() as session:
                        payload = {
                            "model": self.model_name,
                            "prompt": prompt,
                            "stream": False,
                            "options": {"temperature": temperature, "max_tokens": max_tokens}
                        }
                        async with session.post(f"{self.host}/api/generate", json=payload, timeout=120) as resp:
                            if resp.status != 200:
                                text = await resp.text()
                                raise Exception(f"Ollama error {resp.status}: {text}")
                            data = await resp.json()
                            return data["response"]
                except asyncio.TimeoutError:
                    if attempt < retries:
                        wait = 2 ** attempt
                        print(f"⚠️ Таймаут, повтор через {wait} сек...")
                        await asyncio.sleep(wait)
                    else:
                        return "[Таймаут при генерации после нескольких попыток]"
                except Exception as e:
                    if attempt < retries:
                        print(f"⚠️ Ошибка: {e}, повтор...")
                        await asyncio.sleep(2)
                    else:
                        return f"[Ошибка: {e}]"
            return "[Неизвестная ошибка]"

    async def summarize_cluster(self, news_list: List[str], max_sentences: int = 3, max_length: int = 1000) -> str:
        combined_text = "\n\n".join([f"Новость {i+1}: {text}" for i, text in enumerate(news_list)])
        system_msg = (
            "Ты — Qwen3.5, профессиональный русскоязычный аналитик новостей. "
            "Твоя задача — объединить группу новостей по одной теме в связный, информативный и лаконичный диджест. "
            "Придерживайся следующих принципов:\n"
            "- Сохраняй хронологию событий, если она важна для понимания.\n"
            "- Выдели ключевые факты: даты, участников, места, цифры, цитаты официальных лиц.\n"
            "- Пиши нейтрально, без оценок и эмоциональной окраски.\n"
            "- Если в новостях есть противоречия или разные версии, укажи это кратко.\n"
            "- Структурируй ответ: начни с самого важного (что произошло, итог), затем добавь детали, развитие событий.\n"
            "- Используй абзацы для логического разделения мыслей. При необходимости выделяй подтемы с помощью эмодзи (📌, 🔹, ▪️) или жирного текста (`**текст**`).\n"
            "- Не используй Markdown-заголовки вроде `###` — только текст, адаптированный для Telegram.\n"
            "- Соблюдай заданное ограничение по длине, не выходя за лимит символов.\n"
            "- Используй только русский язык для основного текста. Иностранные слова допускаются только в именах собственных, названиях или цитатах, где это необходимо.\n"
            "- **Важно:** не включай в ответ служебные метки вроде `(Новость 54)` или `Новость 61`. Пиши только содержательный пересказ без ссылок на исходные номера."
        )

        user_msg = (
            f"Проанализируй приведённые ниже новости на одну тему и составь краткое содержание (диджест) не более {max_length} символов. "
            f"Объедини все сообщения в связный пересказ, сохранив хронологию и ключевые детали. "
            f"Вот новости:\n\n{combined_text}"
        )
        prompt = self._create_prompt(system_msg, user_msg)
        # max_tokens оцениваем как max_length * 1.5 (примерно), но лучше оставить запас
        return await self._call_ollama(prompt, temperature=0.3, max_tokens=max_length * 2)

    async def generate_title(self, cluster_news: List[str], max_length: int = 100) -> str:
        if not cluster_news:
            return "Без темы"
        text = cluster_news[0]
        system_msg = (
            "Ты — Qwen3.5, профессиональный редактор новостей. "
            "Твоя задача — создать короткий, ёмкий и информативный заголовок для группы новостей на одну тему. "
            "Заголовок должен:\n"
            "- Отражать суть события (главное действие, результат или ключевую новость).\n"
            "- Быть в публицистическом стиле, без лишних деталей, эмоций и оценок.\n"
            "- Укладываться в заданное ограничение по длине.\n"
            "- При необходимости включать ключевые элементы: действующее лицо, место, цифру или результат.\n"
            "- Использовать только русский язык для основного текста. Иностранные слова допускаются только в именах собственных, названиях или цитатах, где это необходимо.\n"
            "- Для Telegram-формата: допускается использование эмодзи (например, 📌) перед заголовком, но без Markdown-заголовков `###` и без конструкций вроде `**заголовок**`, если это не требуется по смыслу.\n"
            "Не используй вводные конструкции вроде «Заголовок:» — давай только сам заголовок."
        )

        user_msg = (
            f"Придумай заголовок для этой группы новостей. Длина — не более {max_length} символов. "
            f"Вот новости:\n\n{text}"
        )
        prompt = self._create_prompt(system_msg, user_msg)
        return await self._call_ollama(prompt, temperature=0.4, max_tokens=200)