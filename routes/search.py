"""
Search routes for Opinian platform
Handles site-wide search for blog posts and pages
"""

import logging
from flask import Blueprint, render_template, request
from psycopg2.extras import RealDictCursor
from app import get_db_connection

logger = logging.getLogger(__name__)

bp = Blueprint('search', __name__, url_prefix='/search')


@bp.route('/')
def search_results():
    """Search for blog posts and pages"""
    query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'all')  # all, posts, pages
    author = request.args.get('author', '')
    tag = request.args.get('tag', '')
    group = request.args.get('group', '')
    sort = request.args.get('sort', 'relevance')  # relevance, date, views
    page = request.args.get('page', 1, type=int)
    per_page = 20

    if not query and not tag and not author and not group:
        return render_template('search_results.html',
                             results={'posts': [], 'pages': []},
                             query='',
                             stats={'total': 0, 'posts': 0, 'pages': 0},
                             filters={'type': search_type, 'author': author, 'tag': tag, 'group': group, 'sort': sort},
                             page=page,
                             total_pages=0)

    try:
        conn = get_db_connection()
        if not conn:
            return render_template('search_results.html',
                                 results={'posts': [], 'pages': []},
                                 query=query,
                                 stats={'total': 0, 'posts': 0, 'pages': 0},
                                 filters={'type': search_type, 'author': author, 'tag': tag, 'group': group, 'sort': sort},
                                 page=page,
                                 total_pages=0,
                                 error='Database connection error')

        cursor = conn.cursor(cursor_factory=RealDictCursor)

        results = {'posts': [], 'pages': []}
        stats = {'total': 0, 'posts': 0, 'pages': 0}

        # Build search conditions
        search_conditions = []
        search_params = []

        # Note: We'll handle query differently for posts vs pages since they have different columns

        # Search Blog Posts
        if search_type in ['all', 'posts']:
            blog_conditions = []
            blog_params = []

            if query:
                # Blog posts have excerpt column
                blog_conditions.append("""
                    (bp.title ILIKE %s OR bp.content ILIKE %s OR bp.excerpt ILIKE %s)
                """)
                search_term = f'%{query}%'
                blog_params.extend([search_term, search_term, search_term])

            if author:
                blog_conditions.append("u.username ILIKE %s")
                blog_params.append(f'%{author}%')

            if tag:
                blog_conditions.append("%s = ANY(bp.tags)")
                blog_params.append(tag)

            if group:
                blog_conditions.append("g.name ILIKE %s")
                blog_params.append(f'%{group}%')

            # Base blog query
            blog_where = " AND ".join(blog_conditions) if blog_conditions else "TRUE"

            # Order by clause
            if sort == 'date':
                order_clause = "bp.published_at DESC"
            elif sort == 'views':
                order_clause = "bp.view_count DESC"
            else:  # relevance
                if query:
                    # Simple relevance: title matches are weighted higher
                    order_clause = """
                        CASE
                            WHEN bp.title ILIKE %s THEN 1
                            WHEN bp.excerpt ILIKE %s THEN 2
                            ELSE 3
                        END, bp.published_at DESC
                    """
                    blog_params.extend([f'%{query}%', f'%{query}%'])
                else:
                    order_clause = "bp.published_at DESC"

            offset = (page - 1) * per_page

            blog_query = f"""
                SELECT
                    'post' as result_type,
                    bp.id,
                    bp.title,
                    bp.slug,
                    bp.content,
                    bp.excerpt,
                    bp.featured_image_url,
                    bp.tags,
                    bp.published_at,
                    bp.view_count,
                    u.username,
                    u.first_name,
                    u.last_name,
                    g.name as group_name,
                    (SELECT COUNT(*) FROM comments WHERE blog_post_id = bp.id AND is_approved = TRUE AND is_deleted = FALSE) as comment_count
                FROM blog_posts bp
                JOIN users u ON bp.author_id = u.id
                LEFT JOIN groups g ON bp.group_id = g.id
                WHERE bp.is_published = TRUE
                    AND (g.is_active = TRUE OR bp.group_id IS NULL)
                    AND ({blog_where})
                ORDER BY {order_clause}
                LIMIT %s OFFSET %s
            """

            blog_params.extend([per_page, offset])
            cursor.execute(blog_query, blog_params)
            results['posts'] = cursor.fetchall()

            # Get total count for blog posts (rebuild params for count query)
            count_params = []
            if query:
                search_term = f'%{query}%'
                count_params.extend([search_term, search_term, search_term])
            if author:
                count_params.append(f'%{author}%')
            if tag:
                count_params.append(tag)
            if group:
                count_params.append(f'%{group}%')

            count_query = f"""
                SELECT COUNT(*) as count
                FROM blog_posts bp
                JOIN users u ON bp.author_id = u.id
                LEFT JOIN groups g ON bp.group_id = g.id
                WHERE bp.is_published = TRUE
                    AND (g.is_active = TRUE OR bp.group_id IS NULL)
                    AND ({blog_where})
            """
            cursor.execute(count_query, count_params)
            stats['posts'] = cursor.fetchone()['count']

        # Search Pages
        if search_type in ['all', 'pages']:
            page_conditions = []
            page_params = []

            if query:
                # Pages don't have excerpt column
                page_conditions.append("""
                    (p.title ILIKE %s OR p.content ILIKE %s)
                """)
                search_term = f'%{query}%'
                page_params.extend([search_term, search_term])

            if author:
                page_conditions.append("u.username ILIKE %s")
                page_params.append(f'%{author}%')

            if group:
                page_conditions.append("g.name ILIKE %s")
                page_params.append(f'%{group}%')

            page_where = " AND ".join(page_conditions) if page_conditions else "TRUE"

            # Order by clause for pages
            if sort == 'date':
                page_order = "p.published_at DESC"
            else:  # relevance or views (pages don't have views)
                if query:
                    page_order = """
                        CASE
                            WHEN p.title ILIKE %s THEN 1
                            ELSE 2
                        END, p.published_at DESC
                    """
                    page_params.extend([f'%{query}%'])
                else:
                    page_order = "p.published_at DESC"

            offset = (page - 1) * per_page

            page_query = f"""
                SELECT
                    'page' as result_type,
                    p.id,
                    p.title,
                    p.slug,
                    p.content,
                    p.published_at,
                    u.username,
                    u.first_name,
                    u.last_name,
                    g.name as group_name
                FROM pages p
                JOIN users u ON p.author_id = u.id
                LEFT JOIN groups g ON p.group_id = g.id
                WHERE p.is_published = TRUE
                    AND (g.is_active = TRUE OR p.group_id IS NULL)
                    AND ({page_where})
                ORDER BY {page_order}
                LIMIT %s OFFSET %s
            """

            page_params.extend([per_page, offset])
            cursor.execute(page_query, page_params)
            results['pages'] = cursor.fetchall()

            # Get total count for pages (rebuild params for count query)
            count_params = []
            if query:
                search_term = f'%{query}%'
                count_params.extend([search_term, search_term])
            if author:
                count_params.append(f'%{author}%')
            if group:
                count_params.append(f'%{group}%')

            count_query = f"""
                SELECT COUNT(*) as count
                FROM pages p
                JOIN users u ON p.author_id = u.id
                LEFT JOIN groups g ON p.group_id = g.id
                WHERE p.is_published = TRUE
                    AND (g.is_active = TRUE OR p.group_id IS NULL)
                    AND ({page_where})
            """
            cursor.execute(count_query, count_params)
            stats['pages'] = cursor.fetchone()['count']

        stats['total'] = stats['posts'] + stats['pages']

        # Calculate total pages for pagination
        total_results = stats['posts'] if search_type == 'posts' else (
            stats['pages'] if search_type == 'pages' else stats['total']
        )
        total_pages = (total_results + per_page - 1) // per_page

        cursor.close()
        conn.close()

        return render_template('search_results.html',
                             results=results,
                             query=query,
                             stats=stats,
                             filters={'type': search_type, 'author': author, 'tag': tag, 'group': group, 'sort': sort},
                             page=page,
                             total_pages=total_pages,
                             per_page=per_page)

    except Exception as e:
        logger.error(f"Search error: {e}")
        return render_template('search_results.html',
                             results={'posts': [], 'pages': []},
                             query=query,
                             stats={'total': 0, 'posts': 0, 'pages': 0},
                             filters={'type': search_type, 'author': author, 'tag': tag, 'group': group, 'sort': sort},
                             page=page,
                             total_pages=0,
                             error='An error occurred during search')
