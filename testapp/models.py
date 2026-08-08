from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    """Plain model with no relations — baseline changelist/add/change coverage."""

    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Product(models.Model):
    """Model with an FK relation — exercises change-view instantiation across a foreign key."""

    name = models.CharField(max_length=100)
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="products"
    )
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    def __str__(self):
        return self.name


class EmptyOnlyModel(models.Model):
    """Deliberately left with zero rows in the test DB — the empty-table scenario."""

    label = models.CharField(max_length=100)

    def __str__(self):
        return self.label


class RestrictedItem(models.Model):
    """Model whose admin denies access unconditionally — the permission-restricted scenario."""

    title = models.CharField(max_length=100)

    def __str__(self):
        return self.title


class SelfReferentialItem(models.Model):
    """Model the auto-instantiator genuinely cannot build from an empty table.

    ``parent`` is a required self-referential FK, so building an instance
    would require an instance to already exist. Exercises the change-view
    skip+warning path.
    """

    name = models.CharField(max_length=100)
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, related_name="children"
    )

    def __str__(self):
        return self.name


class SluggedArticle(models.Model):
    """Required field populated in ``save()``, not via a Django field default.

    ``slug`` is NOT NULL with no ``default=``, so it looks auto-buildable —
    but the admin excludes it from the form entirely (it's derived from
    ``name`` and never meant to be hand-edited), which is the scenario from
    GitHub issue #1: a field genuinely required at the DB level that never
    appears in the ``ModelForm``'s fields.
    """

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
