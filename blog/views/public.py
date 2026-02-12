from __future__ import annotations

from typing import Any

from django.contrib.postgres.search import (
    SearchQuery,
    SearchRank,
    SearchVector,
    TrigramSimilarity,
)
from django_ratelimit.decorators import ratelimit

from core.utils.text import convert_layout
from django.utils.decorators import method_decorator
from django.views.generic import ListView

from blog.cache import (
    get_cached_content_ids,
    set_cached_content_ids,
)
from blog.models import Content
from blog.views.mixins import get_filter_context
from users.models import is_moderator


class HomeView(ListView):  # type: ignore[type-arg]
    model = Content
    template_name = 'blog/index.html'
    context_object_name = 'cards'

    def get_queryset(self) -> list[Content]:  # type: ignore[override]
        """Get content list, using cached IDs for efficiency."""
        cached_ids = get_cached_content_ids()
        if cached_ids is not None:
            return list(
                Content.objects.with_relations()
                .filter(id__in=cached_ids)
                .order_by('-updated_at')
            )
        
        queryset = Content.objects.with_relations().order_by('-updated_at')
        set_cached_content_ids(queryset, limit=6)
        return list(queryset[:6])

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context['is_moderator'] = is_moderator(self.request.user)
        context.update(get_filter_context())
        return context


@method_decorator(ratelimit(key='ip', rate='30/m', method='GET', block=True), name='get')
class SearchView(ListView):  # type: ignore[type-arg]
    """Full-text search view using PostgreSQL search with fuzzy matching."""

    model = Content
    template_name = 'blog/search_results.html'
    context_object_name = 'results'
    paginate_by = 12
    similarity_threshold = 0.3

    def _fulltext_search(self, query: str) -> Any:
        """Perform full-text search."""
        search_vector = SearchVector('title', weight='A') + SearchVector(
            'description', weight='B'
        )
        search_query = SearchQuery(query, search_type='plain')

        return (
            Content.objects.annotate(
                search=search_vector,
                rank=SearchRank(search_vector, search_query),
            )
            .filter(search=search_query)
            .with_relations()
            .order_by('-rank', '-created_at')
        )

    def _fuzzy_search(self, query: str) -> Any:
        """Perform fuzzy search using trigram similarity."""
        return (
            Content.objects.annotate(
                title_similarity=TrigramSimilarity('title', query),
                desc_similarity=TrigramSimilarity('description', query),
            )
            .filter(title_similarity__gt=self.similarity_threshold)
            .with_relations()
            .order_by('-title_similarity', '-created_at')
        )

    def get_queryset(self) -> Any:
        """Search content with fallback to layout conversion and fuzzy search."""
        query = self.request.GET.get('q', '').strip()
        if not query:
            return Content.objects.none()

        results = self._fulltext_search(query)
        if results.exists():
            self._search_mode = 'exact'
            self._suggestion = None
            return results

        alt_query = convert_layout(query)
        if alt_query != query:
            alt_results = self._fulltext_search(alt_query)
            if alt_results.exists():
                self._search_mode = 'layout'
                self._suggestion = alt_query
                return alt_results

        fuzzy_results = self._fuzzy_search(query)
        if fuzzy_results.exists():
            self._search_mode = 'fuzzy'
            first_result = fuzzy_results.first()
            self._suggestion = first_result.title if first_result else None
            return fuzzy_results

        self._search_mode = 'none'
        self._suggestion = None
        return Content.objects.none()

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(**kwargs)
        query = self.request.GET.get('q', '').strip()
        context['query'] = query
        context['is_moderator'] = is_moderator(self.request.user)
        context['search_mode'] = getattr(self, '_search_mode', 'none')
        context['suggestion'] = getattr(self, '_suggestion', None)
        context.update(get_filter_context())
        return context
