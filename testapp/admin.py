from django.contrib import admin

from testapp.models import (
    Category,
    EmptyOnlyModel,
    Product,
    RestrictedItem,
    SelfReferentialItem,
    SluggedArticle,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price")
    list_filter = ("category",)


@admin.register(EmptyOnlyModel)
class EmptyOnlyModelAdmin(admin.ModelAdmin):
    list_display = ("label",)


@admin.register(SelfReferentialItem)
class SelfReferentialItemAdmin(admin.ModelAdmin):
    list_display = ("name", "parent")


@admin.register(RestrictedItem)
class RestrictedItemAdmin(admin.ModelAdmin):
    """Denies all access unconditionally, regardless of user.

    Overrides every permission hook (not just has_module_permission/
    has_view_permission) because Django's changelist/add/change views gate
    on has_view_or_change_permission / has_add_permission individually —
    a superuser still passes has_change_permission by default even when
    has_view_permission is denied.
    """

    list_display = ("title",)

    def has_module_permission(self, request):
        return False

    def has_view_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SluggedArticle)
class SluggedArticleAdmin(admin.ModelAdmin):
    """``slug`` is required at the DB level but excluded from the form —
    it's derived from ``name`` in ``save()``, so there's nothing for a user
    to fill in. Exercises the required-but-not-in-the-form scenario from
    issue #1: this alone is valid and must smoke-test clean. See
    ``tests/test_admin_smoke.py::test_admin_smoke_reports_fieldset_keyerror_clearly``
    for the *misconfigured* variant (field also referenced in ``fieldsets``
    without ``readonly_fields``), which is a genuine Django admin bug this
    tool must surface with a clear message, not a bare ``KeyError``.
    """

    list_display = ("name", "slug")
    exclude = ("slug",)
