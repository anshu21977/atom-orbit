from django.db import models
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
import os

class ClassRoom(models.Model):
    name = models.CharField(max_length=200, unique=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Subject(models.Model):
    name = models.CharField(max_length=200)
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name='subjects')
    
    class Meta:
        ordering = ['name']
        unique_together = ('name', 'classroom')
    
    def __str__(self):
        return f"{self.name} ({self.classroom.name})"

class PDFFile(models.Model):
    CATEGORY_CHOICES = [
        ('mcqs', 'MCQs'),
        ('sample_paper', 'Sample Paper'),
        ('ncert_solutions', 'NCERT Solutions'),
        ('ncert_textbook', 'NCERT Textbook'),

        ('extra_questions', 'Extra Questions'),          # ✅ ADD
        ('previous_year', 'Previous Year Questions'),    # ✅ ADD
    ]
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='pdfs/')
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name='files')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='files', null=True, blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='sample_paper')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    download_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-uploaded_at']
    

    def __str__(self):
        subject_str = f" - {self.subject}" if self.subject else ""
        return f"{self.title} ({self.classroom}{subject_str})"

class Achiever(models.Model):
    name = models.CharField(max_length=100)
    class_name = models.CharField(max_length=20)
    score = models.IntegerField()
    image = models.ImageField(upload_to='achievers/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# ✅ DELETE FILE WHEN RECORD DELETED
@receiver(post_delete, sender=PDFFile)
def delete_file_on_delete(sender, instance, **kwargs):
    if instance.file:
        if os.path.isfile(instance.file.path):
            os.remove(instance.file.path)

# ✅ DELETE OLD FILE WHEN UPDATED
@receiver(pre_save, sender=PDFFile)
def delete_old_file_on_update(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        old_file = PDFFile.objects.get(pk=instance.pk).file
    except PDFFile.DoesNotExist:
        return

    new_file = instance.file
    if old_file and old_file != new_file:
        if os.path.isfile(old_file.path):
            os.remove(old_file.path)