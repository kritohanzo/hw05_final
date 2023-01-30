from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page
from django.views.generic.edit import CreateView

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User


POSTS_PER_PAGE = 10


def paginate_posts(queryset, page_number):
    paginator = Paginator(queryset, POSTS_PER_PAGE)
    page_object = paginator.get_page(page_number)
    return page_object


@cache_page(20, key_prefix="index_page")
def index(request):
    posts = Post.objects.select_related("group", "author")
    page_number = request.GET.get("page")
    page_obj = paginate_posts(posts, page_number)
    template = "posts/index.html"
    context = {"page_obj": page_obj}
    return render(request, template, context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related("author")
    page_number = request.GET.get("page")
    page_obj = paginate_posts(posts, page_number)
    template = "posts/group_list.html"
    context = {"group": group, "page_obj": page_obj}
    return render(request, template, context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.select_related("group")
    page_number = request.GET.get("page")
    page_obj = paginate_posts(posts, page_number)
    posts_count = page_obj.paginator.count
    template = "posts/profile.html"
    following = (
        request.user.is_authenticated
        and Follow.objects.filter(author=author, user=request.user).exists()
    )
    context = {
        "page_obj": page_obj,
        "posts_count": posts_count,
        "username": author,
        "following": following,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    comments = Comment.objects.select_related("author").filter(post=post)
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
    context = {"form": form, "is_edit": True, "post": post}
    return render(request, template, context)


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
    posts = Post.objects.filter(author__following__user=request.user.id)
    page_number = request.GET.get("page")
    page_obj = paginate_posts(posts, page_number)
    return render(request, "posts/follow.html", context={"page_obj": page_obj})


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    if author != user:
        Follow.objects.get_or_create(author=author, user=user)
    return redirect("posts:profile", username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    Follow.objects.filter(author=author.id, user=user.id).delete()
    return redirect("posts:profile", username=username)
