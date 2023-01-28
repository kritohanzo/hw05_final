from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page
from django.views.generic.edit import CreateView

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User


POSTS_PER_PAGE = 10


def paginator(request, queryset, number_page):
    paginator = Paginator(queryset, number_page)
    page_number = request.GET.get("page")
    page_object = paginator.get_page(page_number)
    return page_object


@cache_page(20, key_prefix="index_page")
def index(request):
    posts = Post.objects.all()
    page_obj = paginator(request, posts, POSTS_PER_PAGE)
    template = "posts/index.html"
    context = {"page_obj": page_obj}
    return render(request, template, context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    page_obj = paginator(request, posts, POSTS_PER_PAGE)
    template = "posts/group_list.html"
    context = {"group": group, "page_obj": page_obj}
    return render(request, template, context)


def profile(request, username):
    author = User.objects.get(username=username)
    posts = author.posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    template = "posts/profile.html"
    if request.user.is_authenticated:
        try:
            following = Follow.objects.get(author=author, user=request.user)
            following = True
        except Follow.DoesNotExist:
            following = False
    else:
        following = False
    context = {
        "page_obj": page_obj,
        "username": author,
        "following": following,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    comments = Comment.objects.filter(post=post)
    comment_form = CommentForm()
    author = post.author
    posts_count = author.posts.count()
    template = "posts/post_detail.html"
    context = {
        "post": post,
        "posts_count": posts_count,
        "user": request.user.id,
        "comments": comments,
        "form": comment_form,
    }
    return render(request, template, context)


class PostCreateView(LoginRequiredMixin, CreateView):
    template_name = "posts/create_post.html"
    model = Post
    form_class = PostForm

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.author = self.request.user
        self.object.save()
        return redirect(self.get_success_url())


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author_id != request.user.id:
        return redirect("posts:post_detail", post_id=post.pk)
    if request.method == "POST":
        form = PostForm(
            request.POST or None, files=request.FILES or None, instance=post
        )
        if form.is_valid():
            form.save()
            return redirect("posts:post_detail", post_id=post.pk)
        template = "posts/create_post.html"
        context = {"form": form}
        return render(request, template, context)
    form = PostForm(instance=post)
    template = "posts/create_post.html"
    context = {"form": form, "is_edit": 1, "post": post}
    return render(request, template, context)


# @login_required
# def add_comment(request, post_id):
#     post = Post.objects.get(pk=post_id)
#     form = CommentForm(request.POST or None)
#     if form.is_valid():
#         comment = form.save(commit=False)
#         comment.author = request.user
#         comment.post = post
#         comment.save()
#     return redirect('posts:post_detail', post_id=post_id)


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.author = self.request.user
        self.object.post = Post.objects.get(pk=self.request.path.split("/")[2])
        self.object.save()
        return redirect(self.get_success_url())


@login_required
def follow_index(request):
    authors = Follow.objects.filter(user=request.user.id)
    authors_list = [i.author.id for i in authors]
    posts = Post.objects.filter(author__in=authors_list)
    page_obj = paginator(request, posts, POSTS_PER_PAGE)
    return render(request, "posts/follow.html", context={"page_obj": page_obj})


@login_required
def profile_follow(request, username):
    author = User.objects.get(username=username)
    user = request.user
    Follow.objects.create(author=author, user=user)
    return redirect("posts:profile", username=username)


@login_required
def profile_unfollow(request, username):
    author = User.objects.get(username=username)
    user = request.user
    Follow.objects.get(author=author.id, user=user.id).delete()
    return redirect("posts:profile", username=username)
