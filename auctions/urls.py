from django.urls import path
from . import views

from django.conf.urls import url, include



urlpatterns = [
   
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("create", views.create, name="create"),
    path("auctions/<str:id>", views.listing, name="listing"),
    path("watchlist", views.watchlist, name="watchlist"),
    path("closedbid", views.closedbid, name="closedbid"),
    path("categories", views.categories, name="categories"),
    path("categories/<str:id>", views.catlist, name="catlist"),
] 