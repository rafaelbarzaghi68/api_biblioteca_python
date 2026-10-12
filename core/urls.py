from django.urls import path
from . import views

urlpatterns = [
    path("books", views.book_list_create, name="book-list-create"),
    path("books/<int:pk>", views.book_detail, name="book-detail"),
    path("loans", views.loan_list_create, name="loan-list-create"),
    path("loans/<int:pk>", views.loan_detail, name="loan-detail"),
]