import uuid
import logging
from typing import List
import numpy as np
from sklearn.cluster import KMeans
import umap
from sqlalchemy import select, delete

from app.database.models.cluster import Cluster
from app.database.models.cluster_news import ClusterNews
from app.database.models.embedding import Embedding
from app.database.models.embedding_projection import EmbeddingProjection
from app.database.database import async_session_maker

logger = logging.getLogger(__name__)

class ClusteringService:
    async def perform_clustering(self, digest_id: uuid.UUID, news_ids: List[uuid.UUID], n_clusters: int):
        async with async_session_maker() as session:
            # 1. Проверяем, есть ли уже кластеры для этого дайджеста
            stmt = select(Cluster).where(Cluster.digest_id == digest_id)
            existing_clusters = (await session.execute(stmt)).scalars().all()
            if existing_clusters:
                logger.info(f"Кластеры для дайджеста {digest_id} уже существуют, используем их")
                return existing_clusters

            # 2. Получаем эмбеддинги для переданных новостей
            stmt = select(Embedding).where(Embedding.news_id.in_(news_ids))
            result = await session.execute(stmt)
            embeddings_rows = result.scalars().all()
            if not embeddings_rows:
                logger.warning(f"Нет эмбеддингов для новостей {news_ids}")
                return []

            emb_dict = {row.news_id: row.vector for row in embeddings_rows}
            valid_news_ids = [nid for nid in news_ids if nid in emb_dict]
            if not valid_news_ids:
                return []

            # 3. Корректируем число кластеров, если оно больше количества новостей
            if n_clusters > len(valid_news_ids):
                n_clusters = len(valid_news_ids)
                logger.info(f"Количество кластеров уменьшено до {n_clusters} (мало новостей)")

            if n_clusters == 0:
                return []

            X = np.array([emb_dict[nid] for nid in valid_news_ids])

            # 4. KMeans кластеризация
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            labels = kmeans.fit_predict(X)

            # 5. Создаём кластеры в БД
            clusters_map = {}
            for label in set(labels):
                cluster = Cluster(digest_id=digest_id)
                session.add(cluster)
                await session.flush()
                clusters_map[label] = cluster

            # 6. Проекция для визуализации (UMAP для >=5 точек, иначе упрощённая)
            if len(valid_news_ids) >= 5:
                reducer = umap.UMAP(random_state=42)
                X_proj = reducer.fit_transform(X)
                logger.info(f"UMAP проекция выполнена для {len(valid_news_ids)} точек")
            else:
                logger.info(f"Слишком мало точек для UMAP ({len(valid_news_ids)}), используем упрощённую проекцию")
                # Создаём простую проекцию: точки равномерно распределяем по окружности
                angles = np.linspace(0, 2*np.pi, len(valid_news_ids), endpoint=False)
                X_proj = np.column_stack((np.cos(angles), np.sin(angles))) * 2

            # 7. Создаём связи и проекции
            for idx, (news_id, label) in enumerate(zip(valid_news_ids, labels)):
                cluster = clusters_map[label]

                # Связь новости с кластером
                cn = ClusterNews(cluster_id=cluster.id, news_id=news_id)
                session.add(cn)

                x, y = X_proj[idx]

                # Проверяем, есть ли уже проекция для этой новости в этом дайджесте
                stmt = select(EmbeddingProjection).where(
                    EmbeddingProjection.news_id == news_id,
                    EmbeddingProjection.digest_id == digest_id
                )
                existing_proj = (await session.execute(stmt)).scalar_one_or_none()
                if existing_proj:
                    logger.debug(f"Проекция для новости {news_id} уже существует в дайджесте {digest_id}, пропускаем")
                    continue

                proj = EmbeddingProjection(
                    news_id=news_id,
                    cluster_id=cluster.id,
                    digest_id=digest_id,
                    x=float(x),
                    y=float(y)
                )
                session.add(proj)

            await session.commit()
            logger.info(f"Создано кластеров: {len(clusters_map)}")
            return list(clusters_map.values())