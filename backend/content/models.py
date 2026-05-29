from django.db import models

class Article(models.Model):
    CATEGORY_CHOICES = [
        ("CRYPTO", "Crypto"),
        ("FOREX", "Forex"),
        ("EDUCATION", "Education"),
        ("MARKET", "Market"),
    ]

    title = models.CharField(max_length=200)
    summary = models.TextField(blank=True)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    is_premium = models.BooleanField(default=True)
    published_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Course(models.Model):
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.title


class Lesson(models.Model):
    course = models.ForeignKey(Course, related_name="lessons", on_delete=models.CASCADE)
    title = models.CharField(max_length=160)
    content = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.title
