"""Utility functions for blog app."""
from __future__ import annotations

from typing import TYPE_CHECKING

from django.db.models import Q, QuerySet

if TYPE_CHECKING:
    from blog.models import Category, Content, Tag, TagGroup


def filter_content(
    queryset: QuerySet[Content],
    category: Category | None = None,
    tags: list[Tag] | None = None,
    search_query: str = '',
    no_category: bool = False,
) -> QuerySet[Content]:
    """Filter content queryset by category, tags, and search query.
    
    Args:
        queryset: Base queryset to filter
        category: Filter by category (None = all categories)
        tags: Filter by tags (AND logic - content must have all tags)
        search_query: Search in title and description
        no_category: If True, filter to content without a category
        
    Returns:
        Filtered queryset
    """
    if no_category:
        queryset = queryset.filter(category__isnull=True)
    elif category:
        queryset = queryset.filter(category=category)
    
    if tags:
        for tag in tags:
            queryset = queryset.filter(tags=tag)
    
    if search_query:
        queryset = queryset.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    return queryset.distinct()


def get_visible_tag_groups(
    tag_groups: QuerySet[TagGroup],
    category: Category | None = None,
) -> list[TagGroup]:
    """Get tag groups visible for a specific category.
    
    Args:
        tag_groups: Base queryset of tag groups
        category: Filter by category visibility (None = show groups with no categories)
        
    Returns:
        List of visible tag groups
    """
    if category is None:
        return list(tag_groups)
    
    return [
        group for group in tag_groups
        if group.is_visible_for_category(category)
    ]


def filter_tag_groups(
    queryset: QuerySet[TagGroup],
    category: Category | None = None,
    search_query: str = '',
    no_category: bool = False,
) -> QuerySet[TagGroup]:
    """Filter tag groups by category and search query.
    
    Args:
        queryset: Base queryset to filter
        category: Filter by category (None = all)
        search_query: Search in group name and tag names
        no_category: If True, filter to groups that apply to all categories
        
    Returns:
        Filtered queryset
    """
    if no_category:
        queryset = queryset.filter(categories__isnull=True)
    elif category:
        queryset = queryset.filter(
            Q(categories__isnull=True) |
            Q(categories=category)
        )
    
    if search_query:
        queryset = queryset.filter(
            Q(name__icontains=search_query) |
            Q(tags__name__icontains=search_query)
        )
    
    return queryset.distinct()
