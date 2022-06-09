from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User
from .utils import cache_clear, paginator


def index(request):
    post_list = Post.objects.all()
    page_obj = paginator(post_list, request)
    context = {
        'page_obj': page_obj
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    page_obj = paginator(post_list, request)
    context = {
        'group': group,
        'page_obj': page_obj
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    user = get_object_or_404(User, username=username)

    post_list = user.posts.all()
    page_obj = paginator(post_list, request)

    if request.user.is_authenticated and Follow.objects.filter(
            user=request.user,
            author=user
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
    post = get_object_or_404(Post, pk=post_id)
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
    post = get_object_or_404(Post, pk=post_id)
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
    post = get_object_or_404(Post, pk=post_id)
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
        page_obj = paginator(post_list, request)
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
    author = get_object_or_404(User, username=username)
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
        author = get_object_or_404(User, username=username)
    ).delete()

    cache_clear('follow_index_page_cache', request.user)
    return redirect('posts:profile', username=username)
