# core/views.py
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Book, Loan
from .serializers import BookSerializer, LoanSerializer


# ---------- LIVROS ----------

@api_view(["GET", "POST"])
def book_list_create(request):
    if request.method == "GET":
        books = Book.objects.all()
        return Response(BookSerializer(books, many=True).data)

    serializer = BookSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "PATCH", "DELETE"])
def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)

    if request.method == "GET":
        return Response(BookSerializer(book).data)

    if request.method in ("PUT", "PATCH"):
        serializer = BookSerializer(
            book, data=request.data, partial=(request.method == "PATCH")
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    # DELETE
    if Loan.objects.filter(book=book, return_date__isnull=True).exists():
        return Response(
            {"detail": "Não é possível excluir um livro emprestado."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    book.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ---------- EMPRÉSTIMOS ----------

@api_view(["GET", "POST"])
def loan_list_create(request):
    if request.method == "GET":
        loans = Loan.objects.all()
        return Response(LoanSerializer(loans, many=True).data)

    serializer = LoanSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    book_id = serializer.validated_data["book"].id

    with transaction.atomic():
        book = Book.objects.select_for_update().get(pk=book_id)

        if not book.available:
            return Response(
                {"book_id": ["Este livro não está disponível para empréstimo."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer.save()
        book.available = False
        book.save(update_fields=["available"])

    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "PATCH", "DELETE"])
def loan_detail(request, pk):
    loan = get_object_or_404(Loan, pk=pk)

    if request.method == "GET":
        return Response(LoanSerializer(loan).data)

    if request.method in ("PUT", "PATCH"):
        old_book_id = loan.book_id
        serializer = LoanSerializer(
            loan, data=request.data, partial=(request.method == "PATCH")
        )
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            new_book = serializer.validated_data.get("book", loan.book)

            if new_book.id != old_book_id:
                new_book = Book.objects.select_for_update().get(pk=new_book.id)
                if not new_book.available:
                    return Response(
                        {"book_id": ["Este livro não está disponível para empréstimo."]},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                old_book = Book.objects.select_for_update().get(pk=old_book_id)
                old_book.available = True
                old_book.save(update_fields=["available"])
                new_book.available = False
                new_book.save(update_fields=["available"])

            serializer.save()

        return Response(serializer.data)

    # DELETE
    with transaction.atomic():
        if loan.return_date is None:
            book = Book.objects.select_for_update().get(pk=loan.book_id)
            book.available = True
            book.save(update_fields=["available"])
        loan.delete()

    return Response(status=status.HTTP_204_NO_CONTENT)


