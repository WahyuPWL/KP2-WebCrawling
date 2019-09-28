from django.db import models

# Create your models here.
class paper(models.Model):
    author = models.CharField(max_length=50)
    judul = models.CharField(max_length=150)
    link = models.CharField(max_length=150,null=True)
    authors = models.CharField(max_length=150,null=True)
    source = models.CharField(max_length=150,null=True)
    linksource = models.CharField(max_length=150,null=True)
    detail = models.CharField(max_length=150,null=True)

    def __str__(self):
        return self.author
