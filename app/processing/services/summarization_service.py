import uuid
from sqlalchemy import select
from app.database.models.cluster import Cluster
from app.database.models.cluster_news import ClusterNews
from app.database.models.news import News
from app.database.database import async_session_maker
from app.processing.models.summarizer import SaigaSummarizer

class SummarizationService:
    def __init__(self, summarizer: SaigaSummarizer):
        self.summarizer = summarizer

    async def summarize_clusters(self, digest_id: uuid.UUID):
        async with async_session_maker() as session:
            stmt = select(Cluster).where(Cluster.digest_id == digest_id)
            clusters = (await session.execute(stmt)).scalars().all()

            for cluster in clusters:
                news_stmt = (
                    select(News)
                    .join(ClusterNews, ClusterNews.news_id == News.id)
                    .where(ClusterNews.cluster_id == cluster.id)
                    .order_by(News.published_at)
                )
                news_list = (await session.execute(news_stmt)).scalars().all()
                if not news_list:
                    continue

                texts = [n.text for n in news_list]
                total_chars = sum(len(t) for t in texts)
                # Ограничиваем суммаризацию половиной объёма, но не более 4000 символов (лимит Telegram)
                max_summary_chars = min(total_chars // 2, 4000)
                # Заголовок — максимум 100 символов
                cluster.title = await self.summarizer.generate_title(texts, max_length=100)
                cluster.summary_text = await self.summarizer.summarize_cluster(texts, max_sentences=3, max_length=max_summary_chars)

            await session.commit()