from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils import timezone
from .models import ClassRoom, Subject, PDFFile
from django import forms
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q
import re   
from django.http import FileResponse
from .models import PDFFile
from django.http import JsonResponse
from .models import Achiever
from django.http import JsonResponse
from .models import Subject
from django.http import FileResponse, Http404
import os
from django.db.models import F


def home(request):
    categories = [
        ('mcqs', 'MCQs'),
        ('sample_paper','Sample Papers'),
        ('ncert_solutions','NCERT Solutions'),
        ('ncert_textbook','NCERT Textbooks'),
        ('extra_questions', 'Extra Questions'),
        ('previous_year', 'Previous Year Questions'),
    ]

    achievers = Achiever.objects.order_by('-created_at')[:6]

    return render(request, 'home.html', {
        'categories': categories,
        'achievers': achievers
    })

def _num_from_name(s: str) -> int:
    m = re.search(r"\d+", s or "")
    return int(m.group()) if m else 0

def category_view(request, category):
    classes_qs = ClassRoom.objects.all()

    # >>> Sorting happens here <<<
    classes = sorted(classes_qs, key=lambda c: (_num_from_name(c.name), c.name))

    pretty = dict(
        mcqs='MCQs',
        sample_paper='Sample Papers',
        ncert_solutions='NCERT Solutions',
        ncert_textbook='NCERT Textbooks',
        extra_questions='Extra Questions',              # ✅ ADD
        previous_year='Previous Year Questions',        # ✅ ADD
    ).get(category, category)

    return render(request, 'category.html', {
        'classes': classes,
        'category': category,
        'pretty': pretty
    })


def class_subjects(request, category, class_id):
    classroom = get_object_or_404(ClassRoom, pk=class_id)
    subjects = Subject.objects.filter(classroom=classroom).order_by('name')
    pretty = dict(
        mcqs='MCQs',
        sample_paper='Sample Papers',
        ncert_solutions='NCERT Solutions',
        ncert_textbook='NCERT Textbooks',
        extra_questions='Extra Questions',              # ✅ ADD
        previous_year='Previous Year Questions',        # ✅ ADD
    ).get(category, category)
    return render(request,'subjects.html',{'classroom':classroom,'subjects':subjects,'category':category,'pretty':pretty})

def subject_files(request, category, class_id, subject_id):
    classroom = get_object_or_404(ClassRoom, pk=class_id)
    subject = get_object_or_404(Subject, pk=subject_id)
    files = PDFFile.objects.filter(classroom=classroom, subject=subject, category=category)
    pretty = dict(
        mcqs='MCQs',
        sample_paper='Sample Papers',
        ncert_solutions='NCERT Solutions',
        ncert_textbook='NCERT Textbooks',
        extra_questions='Extra Questions',              # ✅ ADD
        previous_year='Previous Year Questions',        # ✅ ADD
    ).get(category, category)
    return render(request,'files.html',{'classroom':classroom,'subject':subject,'files':files,'category':category,'pretty':pretty})

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
        super(PDFFileForm, self).__init__(*args, **kwargs)
        self.fields['classroom'].queryset = self.fields['classroom'].queryset.order_by('name')
        if 'classroom' in self.initial:
            self.fields['subject'].queryset = Subject.objects.filter(classroom=self.initial['classroom']).order_by('name')
        else:
            self.fields['subject'].queryset = Subject.objects.none()
        
    class Meta:
        model = PDFFile
        fields = ['title','category','classroom','subject','file']

# ---------- DASHBOARD ----------
@login_required
@user_passes_test(is_admin)
def dashboard(request):
    files = PDFFile.objects.select_related('classroom', 'subject').order_by('-uploaded_at')
    return render(request,'dashboard/dashboard.html',{'files':files})

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

def contact_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        
        # Prepare email content
        subject = f"New Contact Form Submission from {name}"
        message_body = f"""
        Name: {name}
        Email: {email}
        Message: {message}
        """
        
        try:
            # Send email
            send_mail(
                subject,
                message_body,
                settings.DEFAULT_FROM_EMAIL,
                [settings.EMAIL_HOST_USER],
                fail_silently=False,
            )
            messages.success(request, 'Thank you for your message. We will get back to you soon!')
        except Exception as e:
            messages.error(request, 'Sorry, there was an error sending your message. Please try again later.')
        
        return redirect('contact')
    
    return render(request, 'contact.html')


def search_files(request):
    query = request.GET.get('q')
    files = None

    categories = [
        ('mcqs', 'MCQs'),
        ('sample_paper', 'Sample Papers'),
        ('ncert_solutions', 'NCERT Solutions'),
        ('ncert_textbook', 'NCERT Textbooks'),
        ('extra_questions', 'Extra Questions'),
        ('previous_year', 'Previous Year Questions'),
    ]

    if query:
        files = PDFFile.objects.filter(
            Q(title__icontains=query) | 
            Q(classroom__name__icontains=query) |
            Q(subject__name__icontains=query)
        ).select_related('classroom', 'subject').order_by('-uploaded_at')

    return render(request, 'search_results.html', {
        'files': files,
        'query': query,
        'categories': categories
    })


def live_search(request):
    query = request.GET.get('q', '')
    results = []

    if query:
        files = PDFFile.objects.filter(title__icontains=query)[:5]

        for f in files:
            results.append({
                'title': f.title,
                'url': f"/files/{f.id}/"   # 👈 custom page URL
            })

    return JsonResponse(results, safe=False)

def file_detail(request, id):
    file = PDFFile.objects.get(id=id)
    return render(request, 'file_detail.html', {'file': file})


def load_subjects(request):
    class_id = request.GET.get('class_id')
    subjects = Subject.objects.filter(classroom_id=class_id).values('id', 'name')
    return JsonResponse(list(subjects), safe=False)



def all_achievers(request):
    achievers = Achiever.objects.order_by('-created_at')  # ✅ latest first
    return render(request, 'achievers.html', {
        'achievers': achievers
    })



def serve_pdf(request, id):
    file = PDFFile.objects.get(id=id)

    # ✅ increment download count
    file.download_count += 1
    file.save()

    response = FileResponse(file.file.open(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{file.title}.pdf"'
    
    return response


def secure_download(request, file_id):
    try:
        file = PDFFile.objects.get(id=file_id)

        # ✅ Increase download count
        PDFFile.objects.filter(id=file_id).update(
            download_count=F('download_count') + 1
        )

        file_path = file.file.path

        if not os.path.exists(file_path):
            raise Http404

        # ✅ USE ADMIN TITLE (IMPORTANT)
        safe_title = re.sub(r'[^a-zA-Z0-9 ]', '', file.title)
        filename = f"{safe_title}.pdf"

        response = FileResponse(open(file_path, 'rb'), as_attachment=True)

        # 🔥 THIS LINE CONTROLS DOWNLOAD NAME
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response

    except PDFFile.DoesNotExist:
        raise Http404