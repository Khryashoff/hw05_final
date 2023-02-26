from django.core.paginator import Paginator
from django.conf import settings


def get_page(request, post_list):
    paginator = Paginator(post_list, settings.POSTS_VOL)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
