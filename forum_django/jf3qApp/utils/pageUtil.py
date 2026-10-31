from django.core import paginator
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def get_page(all,page_no,page_size=10):
    if page_no:
        page_no = int(page_no)
    else:
        page_no = 1

    paginator = Paginator(all, 10)

    total = paginator.count

    try:
        page_pbj = paginator.page(page_no)
    except PageNotAnInteger:
        page_pbj = paginator.page(1)
    except EmptyPage:
        page_pbj = paginator.page(paginator.num_pages)
    list = page_pbj.object_list

    return {'total':total,'list':list}