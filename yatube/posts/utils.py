from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.core.paginator import Paginator


def cache_clear(cache_key: str, user=None):
    key = make_template_fragment_key(cache_key, [user])
    cache.delete(key)


def paginator(post_list, request):
    NUMBER_OF_POSTS_TO_SHOW = 10
    paginator = Paginator(post_list, NUMBER_OF_POSTS_TO_SHOW)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
