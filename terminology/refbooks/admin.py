from django.contrib import admin
from .models import Refbook, RefbookVersion, RefbookItem


class RefbookVersionInline(admin.TabularInline):
    model = RefbookVersion
    extra = 1


@admin.register(Refbook)
class RefbookAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'name', 'get_current_version', 'get_current_version_start_date')
    search_fields = ('code', 'name')
    inlines = [RefbookVersionInline]

    @admin.display(description="Текущая версия")
    def get_current_version(self, obj):
        return obj.current_version

    @admin.display(description="Датя начала действия")
    def get_current_version_start_date(self, obj):
        return obj.current_version_start_date


@admin.register(RefbookVersion)
class RefbookVersionAdmin(admin.ModelAdmin):
    list_display = ('refbook', 'version', 'start_date')
    list_filter = ('refbook',)
    search_fields = ('version',)


@admin.register(RefbookItem)
class RefbookItemAdmin(admin.ModelAdmin):
    list_display = ('version', 'code', 'value')
    search_fields = ('code', 'value')
