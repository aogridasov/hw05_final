from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.core.paginator import Paginator
from django.shortcuts import redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


NUMBER_OF_POSTS_TO_SHOW = 10


def cache_clear(cache_key: str, user=None):
    key = make_template_fragment_key(cache_key, [user])
    cache.delete(key)


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, NUMBER_OF_POSTS_TO_SHOW)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = Group.objects.get(slug=slug)
    post_list = group.posts.all()
    paginator = Paginator(post_list, NUMBER_OF_POSTS_TO_SHOW)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'page_obj': page_obj
    }
    return render(request, 'posts/group_list.html', context)


# Нужно соблюсти принцип DRY в плане применения паджинатора
def profile(request, username):
    user = User.objects.get(username=username)

    post_list = user.posts.all()
    paginator = Paginator(post_list, NUMBER_OF_POSTS_TO_SHOW)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if request.user.is_authenticated and Follow.objects.filter(
            user=request.user,
            author=User.objects.get(username=username)
    ).exists():
        following = True
    else:
        following = False

    context = {
        'author': user,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = Post.objects.get(pk=post_id)
    comments = post.comments.all()
    context = {
        'post': post,
        'form': CommentForm(),
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=post.author)

    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = Post.objects.get(pk=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post,
    )

    if request.user != post.author:
        return redirect(post)

    if form.is_valid():
        post = form.save()
        return redirect(post)

    return render(request, 'posts/create_post.html', {
        'form': form,
    })


@login_required
def add_comment(request, post_id):
    post = Post.objects.get(pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    user = request.user
    page_obj = {}
    if Follow.objects.filter(user=user).exists():
        follows = user.follower.all()
        followed_authors = User.objects.filter(following__in=follows)
        post_list = Post.objects.filter(author__in=followed_authors)
        paginator = Paginator(post_list, NUMBER_OF_POSTS_TO_SHOW)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context = {
            'page_obj': page_obj
        }
    else:
        context = {
            'page_obj': page_obj
        }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = User.objects.get(username=username)
    if request.user != author and Follow.objects.filter(
        user=request.user,
        author=author
    ).exists() is False:
        Follow.objects.create(
            user=request.user,
            author=author
        )
        cache_clear('follow_index_page_cache', request.user)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    Follow.objects.filter(
        user=request.user,
        author=User.objects.get(username=username)
    ).delete()

    cache_clear('follow_index_page_cache', request.user)
    return redirect('posts:profile', username=username)
