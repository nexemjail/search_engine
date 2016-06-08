from __future__ import unicode_literals

from django.db import models

# Create your models here.


class CrawledPage(models.Model):
    url = models.URLField(null=False)