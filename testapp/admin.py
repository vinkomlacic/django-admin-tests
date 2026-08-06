from django.contrib import admin

from testapp.models import Category, EmptyOnlyModel, Product, RestrictedItem


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
