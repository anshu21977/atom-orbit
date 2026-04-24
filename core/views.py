from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q, F
from django.http import (
    HttpResponse, HttpResponseRedirect, Http404, StreamingHttpResponse, JsonResponse
)
from django.views.decorators.cache import cache_page
from django.utils.encoding import smart_str
from django import forms

import re
import requests

from .models import ClassRoom, Subject, PDFFile, Achiever
from .utils import generate_token   # ✅ single clean import from utils.py


# ---------- HELPERS ----------
def _num_from_name(s: str) -> int:
    m = re.search(r"\d+", s or "")
    return int(m.group()) if m else 0

PRETTY_CATEGORIES = dict(
    mcqs='MCQs',
    sample_paper='Sample Papers',
    ncert_solutions='NCERT Solutions',
    ncert_textbook='NCERT Textbooks',
    extra_questions='Extra Questions',
    previous_year='Previous Year Questions',
)


# ---------- PUBLIC VIEWS ----------
@cache_page(60 * 5)
def home(request):
    achievers = Achiever.objects.order_by('-created_at')[:6]
    categories = list(PRETTY_CATEGORIES.items())
    return render(request, 'home.html', {
        'achievers': achievers,
        'categories': categories,
    })


def category_view(request, category):
    classes = sorted(ClassRoom.objects.all(), key=lambda c: (_num_from_name(c.name), c.name))
    return render(request, 'category.html', {
        'classes': classes,
        'category': category,
        'pretty': PRETTY_CATEGORIES.get(category, category),
    })


def class_subjects(request, category, class_id):
    classroom = get_object_or_404(ClassRoom, pk=class_id)
    subjects = Subject.objects.filter(classroom=classroom).order_by('name')
    return render(request, 'subjects.html', {
        'classroom': classroom,
        'subjects': subjects,
        'category': category,
        'pretty': PRETTY_CATEGORIES.get(category, category),
    })


def subject_files(request, category, class_id, subject_id):
    classroom = get_object_or_404(ClassRoom, pk=class_id)
    subject = get_object_or_404(Subject, pk=subject_id)
    files = PDFFile.objects.filter(classroom=classroom, subject=subject, category=category)

    return render(request, 'files.html', {
        'classroom': classroom,
        'subject': subject,
        'files': files,
        'category': category,
        'pretty': PRETTY_CATEGORIES.get(category, category),
    })


def download_file(request, file_id):
    try:
        file = PDFFile.objects.get(id=file_id)
    except PDFFile.DoesNotExist:
        raise Http404("File not found")

    PDFFile.objects.filter(id=file_id).update(download_count=F('download_count') + 1)

    cloudinary_url = file.file.url.split("?")[0]

    try:
        r = requests.get(cloudinary_url, stream=True, timeout=30)
        r.raise_for_status()
    except requests.RequestException:
        raise Http404("Could not fetch file")

    filename = cloudinary_url.split("/")[-1]
    if not filename.lower().endswith(".pdf"):
        filename += ".pdf"

    response = StreamingHttpResponse(
        r.iter_content(chunk_size=8192),
        content_type="application/pdf",
    )
    response["Content-Disposition"] = f'attachment; filename="{smart_str(filename)}"'
    response["X-Content-Type-Options"] = "nosniff"
    response["Cache-Control"] = "no-store"
    return response

# ---------- AUTH ----------
def admin_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid credentials or not an admin user.')
    return render(request, 'login.html')


def admin_logout(request):
    logout(request)
    return redirect('admin_login')


def is_admin(user):
    return user.is_authenticated and user.is_staff


# ---------- FORMS ----------
class PDFFileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['classroom'].queryset = self.fields['classroom'].queryset.order_by('name')
        if 'classroom' in self.initial:
            self.fields['subject'].queryset = Subject.objects.filter(
                classroom=self.initial['classroom']
            ).order_by('name')
        else:
            self.fields['subject'].queryset = Subject.objects.none()

    class Meta:
        model = PDFFile
        fields = ['title', 'category', 'classroom', 'subject', 'file']


# ---------- DASHBOARD ----------
@login_required
@user_passes_test(is_admin)
def dashboard(request):
    files = PDFFile.objects.select_related('classroom', 'subject').order_by('-uploaded_at')
    return render(request, 'dashboard/dashboard.html', {'files': files})


@login_required
@user_passes_test(is_admin)
def upload_pdf(request):
    form = PDFFileForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        pdf = form.save(commit=False)
        pdf.uploaded_at = timezone.now()
        pdf.save()
        messages.success(request, 'File uploaded successfully.')
        return redirect('dashboard')
    return render(request, 'dashboard/upload.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def edit_pdf(request, pk):
    pdf = get_object_or_404(PDFFile, pk=pk)
    form = PDFFileForm(request.POST or None, request.FILES or None, instance=pdf)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'File updated successfully.')
        return redirect('dashboard')
    return render(request, 'dashboard/edit.html', {'form': form, 'pdf': pdf})


@login_required
@user_passes_test(is_admin)
def delete_pdf(request, pk):
    pdf = get_object_or_404(PDFFile, pk=pk)
    if request.method == 'POST':
        pdf.delete()
        messages.success(request, 'File deleted successfully.')
        return redirect('dashboard')
    return render(request, 'dashboard/delete_confirm.html', {'pdf': pdf})


# ---------- OTHER ----------
def contact_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        subject = f"New Contact Form Submission from {name}"
        message_body = f"Name: {name}\nEmail: {email}\nMessage: {message}"
        try:
            send_mail(subject, message_body, settings.DEFAULT_FROM_EMAIL,
                      [settings.EMAIL_HOST_USER], fail_silently=False)
            messages.success(request, 'Thank you for your message. We will get back to you soon!')
        except Exception:
            messages.error(request, 'Sorry, there was an error. Please try again later.')
        return redirect('contact')
    return render(request, 'contact.html')


def search_files(request):
    query = request.GET.get('q')
    files = None
    if query:
        files = PDFFile.objects.filter(
            Q(title__icontains=query) |
            Q(classroom__name__icontains=query) |
            Q(subject__name__icontains=query)
        ).select_related('classroom', 'subject').order_by('-uploaded_at')
    return render(request, 'search_results.html', {
        'files': files,
        'query': query,
        'categories': list(PRETTY_CATEGORIES.items()),
    })


def live_search(request):
    query = request.GET.get('q', '')
    results = []
    if query:
        for f in PDFFile.objects.filter(title__icontains=query)[:5]:
            results.append({'title': f.title, 'url': f"/files/{f.id}/"})
    return JsonResponse(results, safe=False)


def file_detail(request, id):
    file = get_object_or_404(PDFFile, id=id)
    return render(request, 'file_detail.html', {'file': file})


def load_subjects(request):
    class_id = request.GET.get('class_id')
    subjects = Subject.objects.filter(classroom_id=class_id).values('id', 'name')
    return JsonResponse(list(subjects), safe=False)


def all_achievers(request):
    achievers = Achiever.objects.order_by('-created_at')
    return render(request, 'achievers.html', {'achievers': achievers})


def robots_txt(request):
    return HttpResponse("User-agent: *\nAllow: /", content_type="text/plain")