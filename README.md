CREATIVE COACHING AND COMPUTER CLASSES - Django Project (ready to host)
---------------------------------------------------------------------
What you get:
- Django project named `creative_coaching`
- App named `core` with models: ClassRoom, PDFFile
- Public pages: Home -> Categories -> Class -> Files with download links
- Admin: Use Django admin to add/edit/delete classes and PDF files (only staff/superuser)
- Media folder used to store uploaded PDFs (`media/`)
- Responsive templates + CSS, responsive logo SVG

Quick start (on your machine):
1. Make a virtualenv and activate it.
   python3 -m venv venv
   source venv/bin/activate    (Linux/mac) or venv\Scripts\activate (Windows)
2. Install requirements:
   pip install -r requirements.txt
3. Run migrations:
   python manage.py migrate
4. Create a superuser (this will be your admin):
   python manage.py createsuperuser
5. Collect static (optional for production):
   python manage.py collectstatic
6. Run development server:
   python manage.py runserver 0.0.0.0:8000
7. Browse: http://127.0.0.1:8000/  - Public site
   Admin: http://127.0.0.1:8000/admin/

Notes:
- Add PDFs via the admin (Files -> Add). Each file attaches to a Class (ClassRoom).
- Uploaded PDFs will be saved under `media/pdfs/`.
- For production, configure DEBUG=False, set ALLOWED_HOSTS, and serve media/static via proper web server.
