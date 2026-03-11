"""
学术分析服务实现
影响力分析、引用统计、研究趋势
"""

from datetime import datetime, date
from typing import List, Dict, Optional, Any
from collections import defaultdict
import math

from .schemas import (
    AcademicImpactAnalysis,
    CitationMetrics,
    PublicationMetrics,
    ImpactMetrics,
    ResearchTrend,
    CollaborationNetwork,
    VenueMetrics,
    PaperAnalytics,
    ResearcherProfile,
    TrendAnalysisResult,
)


class AnalyticsService:
    """学术分析服务"""

    def __init__(self, db_session=None, semantic_scholar=None):
        self.db = db_session
        self.ss = semantic_scholar

    async def analyze_author_impact(
        self,
        author_id: str,
        author_name: str,
        papers: List[Dict[str, Any]]
    ) -> AcademicImpactAnalysis:
        """
        分析作者的学术影响力

        Args:
            author_id: 作者ID
            author_name: 作者名称
            papers: 作者论文列表

        Returns:
            AcademicImpactAnalysis: 影响力分析结果
        """
        if not papers:
            return AcademicImpactAnalysis(
                author_id=author_id,
                author_name=author_name,
                analysis_date=datetime.now(),
                citations=CitationMetrics(),
                publications=PublicationMetrics(),
                impact=ImpactMetrics(),
                yearly_trends=[],
                top_collaborators=[],
                venue_distribution=[],
                research_fields=[],
            )

        # 计算引用指标
        citations = self._calculate_citation_metrics(papers)

        # 计算发表指标
        publications = self._calculate_publication_metrics(papers, author_name)

        # 计算影响力指标
        impact = self._calculate_impact_metrics(papers, citations)

        # 计算年度趋势
        yearly_trends = self._calculate_yearly_trends(papers)

        # 分析合作网络
        top_collaborators = self._analyze_collaboration_network(papers, author_name)

        # 分析发表 venues
        venue_distribution = self._analyze_venues(papers)

        # 研究领域分析
        research_fields = self._analyze_research_fields(papers)

        return AcademicImpactAnalysis(
            author_id=author_id,
            author_name=author_name,
            analysis_date=datetime.now(),
            citations=citations,
            publications=publications,
            impact=impact,
            yearly_trends=yearly_trends,
            top_collaborators=top_collaborators,
            venue_distribution=venue_distribution,
            research_fields=research_fields,
        )

    def _calculate_citation_metrics(self, papers: List[Dict[str, Any]]) -> CitationMetrics:
        """计算引用指标"""
        citation_counts = [p.get('citation_count', 0) for p in papers]
        citation_counts.sort(reverse=True)

        total_citations = sum(citation_counts)

        # 计算h-index
        h_index = 0
        for i, count in enumerate(citation_counts, 1):
            if count >= i:
                h_index = i
            else:
                break

        # 计算i10-index (被引用10次以上的论文数)
        i10_index = sum(1 for c in citation_counts if c >= 10)

        # 计算g-index
        g_index = 0
        cumulative = 0
        for i, count in enumerate(citation_counts, 1):
            cumulative += count
            if cumulative >= i * i:
                g_index = i
            else:
                break

        # 计算年均引用
        years = [p.get('publication_year') for p in papers if p.get('publication_year')]
        if years:
            career_years = max(1, datetime.now().year - min(years) + 1)
            citations_per_year = total_citations / career_years
        else:
            citations_per_year = 0

        return CitationMetrics(
            total_citations=total_citations,
            citations_per_year=round(citations_per_year, 2),
            h_index=h_index,
            i10_index=i10_index,
            g_index=g_index,
        )

    def _calculate_publication_metrics(
        self,
        papers: List[Dict[str, Any]],
        author_name: str
    ) -> PublicationMetrics:
        """计算发表指标"""
        total = len(papers)

        # 统计各类作者身份
        first_author = 0
        corresponding = 0
        solo = 0
        collaborative = 0

        by_year = defaultdict(int)
        by_type = defaultdict(int)

        for paper in papers:
            authors = paper.get('authors', [])
            author_names = [a.get('name', '').lower() for a in authors]

            # 检查是否是第一作者
            if author_names and author_name.lower() in author_names[0].lower():
                first_author += 1

            # 检查是否是独立作者
            if len(authors) == 1:
                solo += 1
            else:
                collaborative += 1

            # 按年份统计
            year = paper.get('publication_year')
            if year:
                by_year[year] += 1

            # 按类型统计
            pub_type = paper.get('source_type', 'unknown')
            by_type[pub_type] += 1

        return PublicationMetrics(
            total_publications=total,
            first_author_count=first_author,
            corresponding_author_count=corresponding,
            solo_author_count=solo,
            collaborative_count=collaborative,
            publications_by_year=dict(by_year),
            publications_by_type=dict(by_type),
        )

    def _calculate_impact_metrics(
        self,
        papers: List[Dict[str, Any]],
        citations: CitationMetrics
    ) -> ImpactMetrics:
        """计算影响力指标"""
        citation_counts = [p.get('citation_count', 0) for p in papers]

        if not citation_counts:
            return ImpactMetrics()

        avg_citations = sum(citation_counts) / len(citation_counts)

        # 高引用论文 (超过平均值2倍)
        highly_cited = sum(1 for c in citation_counts if c >= avg_citations * 2)

        # 热论文 (近2年发表且引用超过10次)
        current_year = datetime.now().year
        hot = sum(
            1 for p in papers
            if p.get('publication_year', 0) >= current_year - 2
            and p.get('citation_count', 0) > 10
        )

        # 引用增长速度 (简化计算：总引用/最早论文年份到现在)
        years = [p.get('publication_year') for p in papers if p.get('publication_year')]
        if years:
            duration = max(1, current_year - min(years) + 1)
            velocity = citations.total_citations / duration
        else:
            velocity = 0

        return ImpactMetrics(
            average_citations_per_paper=round(avg_citations, 2),
            highly_cited_papers=highly_cited,
            hot_papers=hot,
            citation_velocity=round(velocity, 2),
        )

    def _calculate_yearly_trends(
        self,
        papers: List[Dict[str, Any]]
    ) -> List[ResearchTrend]:
        """计算年度研究趋势"""
        by_year = defaultdict(lambda: {
            'publications': [],
            'citations': 0,
            'keywords': [],
        })

        for paper in papers:
            year = paper.get('publication_year')
            if not year:
                continue

            by_year[year]['publications'].append(paper)
            by_year[year]['citations'] += paper.get('citation_count', 0)

        trends = []
        for year in sorted(by_year.keys()):
            data = by_year[year]

            # 计算当年的h-index
            citations = sorted(
                [p.get('citation_count', 0) for p in data['publications']],
                reverse=True
            )
            h_index = 0
            for i, c in enumerate(citations, 1):
                if c >= i:
                    h_index = i
                else:
                    break

            trends.append(ResearchTrend(
                year=year,
                publication_count=len(data['publications']),
                citation_count=data['citations'],
                h_index=h_index,
                top_keywords=[],  # 可以从论文关键词提取
            ))

        return trends

    def _analyze_collaboration_network(
        self,
        papers: List[Dict[str, Any]],
        author_name: str
    ) -> List[CollaborationNetwork]:
        """分析合作网络"""
        collaborators = defaultdict(lambda: {
            'count': 0,
            'papers': [],
            'years': [],
        })

        for paper in papers:
            authors = paper.get('authors', [])
            year = paper.get('publication_year')

            for author in authors:
                name = author.get('name', '')
                if name and author_name.lower() not in name.lower():
                    collaborators[name]['count'] += 1
                    collaborators[name]['papers'].append(paper.get('title', ''))
                    if year:
                        collaborators[name]['years'].append(year)

        # 取合作最多的前10位
        top_collabs = sorted(
            collaborators.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )[:10]

        return [
            CollaborationNetwork(
                author_name=name,
                collaboration_count=data['count'],
                first_collaboration_year=min(data['years']) if data['years'] else None,
                last_collaboration_year=max(data['years']) if data['years'] else None,
                joint_publications=data['papers'][:5],  # 只取前5篇
            )
            for name, data in top_collabs
        ]

    def _analyze_venues(self, papers: List[Dict[str, Any]]) -> List[VenueMetrics]:
        """分析发表 venues"""
        venues = defaultdict(lambda: {
            'count': 0,
            'citations': 0,
            'papers': [],
        })

        for paper in papers:
            venue = paper.get('journal') or paper.get('venue') or 'Unknown'
            venues[venue]['count'] += 1
            venues[venue]['citations'] += paper.get('citation_count', 0)
            venues[venue]['papers'].append(paper)

        return [
            VenueMetrics(
                venue_name=venue,
                publication_count=data['count'],
                total_citations=data['citations'],
                average_citations=round(data['citations'] / data['count'], 2) if data['count'] > 0 else 0,
                impact_factor=None,  # 需要额外数据
                h_index=0,  # 可以计算
            )
            for venue, data in sorted(
                venues.items(),
                key=lambda x: x[1]['count'],
                reverse=True
            )[:10]
        ]

    def _analyze_research_fields(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """分析研究领域"""
        fields = defaultdict(lambda: {'count': 0, 'citations': 0})

        for paper in papers:
            paper_fields = paper.get('fields_of_study', [])
            citations = paper.get('citation_count', 0)

            for field in paper_fields:
                fields[field]['count'] += 1
                fields[field]['citations'] += citations

        return [
            {
                'field': field,
                'paper_count': data['count'],
                'citation_count': data['citations'],
                'percentage': round(data['count'] / len(papers) * 100, 2),
            }
            for field, data in sorted(
                fields.items(),
                key=lambda x: x[1]['count'],
                reverse=True
            )
        ]

    async def analyze_research_trends(
        self,
        keywords: List[str],
        start_year: int,
        end_year: int,
    ) -> TrendAnalysisResult:
        """分析研究趋势"""
        # 这里应该调用外部API或数据库查询
        # 简化版本返回模拟数据

        yearly_data = []
        for year in range(start_year, end_year + 1):
            yearly_data.append({
                'year': year,
                'paper_count': 100 + (year - start_year) * 10,  # 模拟增长
                'citation_count': 500 + (year - start_year) * 50,
            })

        return TrendAnalysisResult(
            keywords=keywords,
            yearly_data=yearly_data,
            emerging_topics=["AI", "Machine Learning", "Deep Learning"],
            declining_topics=["Traditional Methods"],
            hot_researchers=[],
            hot_papers=[],
        )

    async def get_paper_analytics(self, paper_id: str) -> Optional[PaperAnalytics]:
        """获取单篇论文分析"""
        # 这里应该调用外部API
        return None
