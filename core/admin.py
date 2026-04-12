from django.contrib import admin
from .models import ClassRoom, Subject, PDFFile


class ClassRoomAdmin(admin.ModelAdmin):
    list_display = ('name',)


class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'classroom')
    list_filter = ('classroom',)
    search_fields = ('name',)


class PDFFileAdmin(admin.ModelAdmin):
    list_display = ('title', 'classroom', 'subject', 'category', 'uploaded_at')
    list_filter = ('classroom', 'subject', 'category')
    search_fields = ('title',)

    class Media:
        js = ('js/admin_subject_filter.js',)


admin.site.register(ClassRoom, ClassRoomAdmin)
admin.site.register(Subject, SubjectAdmin)
admin.site.register(PDFFile, PDFFileAdmin)

from .models import Achiever

admin.site.register(Achiever)