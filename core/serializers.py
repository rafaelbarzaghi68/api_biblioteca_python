# serializers.py
from rest_framework import serializers
from .models import Book, Loan


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = [
            "id",
            "title",
            "author",
            "year",
            "available",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class LoanSerializer(serializers.ModelSerializer):
    book_id = serializers.PrimaryKeyRelatedField(
        source="book",
        queryset=Book.objects.all()
    )

    class Meta:
        model = Loan
        fields = ["id", "book_id", "person_name", "loan_date"]
        read_only_fields = ["id"]

    def validate_book_id(self, book):
        if self.instance and self.instance.book_id == book.id:
            return book
        if not book.available:
            raise serializers.ValidationError(
                "Este livro não está disponível para empréstimo."
            )
        return book