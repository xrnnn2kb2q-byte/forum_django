from django.core.paginator import Paginator


def get_page(queryset, page_no=1, page_size=10):
    try:
        page_no = int(page_no or 1)
        page_size = int(page_size or 10)
    except (TypeError, ValueError):
        raise ValueError('pageNo and pageSize must be integers')
    if page_no < 1 or page_size < 1 or page_size > 100:
        raise ValueError('pageNo must be positive and pageSize must be between 1 and 100')

    paginator = Paginator(queryset, page_size)
    page = paginator.get_page(page_no)
    return {'total': paginator.count, 'list': page.object_list}
