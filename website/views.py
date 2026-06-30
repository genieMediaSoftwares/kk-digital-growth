from django.shortcuts import render
from .models import Consultation
from .forms import ContactForm


def home(request):
    return render(request, "home.html")


def consultation(request):

    if request.method == "POST":

        Consultation.objects.create(
            first_name=request.POST.get("first_name"),
            last_name=request.POST.get("last_name"),
            company_name=request.POST.get("company_name"),
            email=request.POST.get("email"),
            phone_number=request.POST.get("phone_number"),
            project_name=request.POST.get("project_name"),
        )

        return render(
            request,
            "consultation.html",
            {"success": True},
        )

    return render(request, "consultation.html")


def services(request):
    return render(request, "services.html")


def process(request):
    return render(request, "process.html")


def clients(request):
    return render(request, "clients.html")


def projects(request):
    return render(request, "projects.html")


def contact(request):

    success = False

    if request.method == "POST":

        print(request.POST)

        form = ContactForm(request.POST)

        print(form.is_valid())
        print(form.errors)

        if form.is_valid():
            form.save()
            success = True
            print("Saved Successfully!")

            form = ContactForm()

    else:
        form = ContactForm()

    return render(
        request,
        "contact.html",
        {
            "form": form,
            "success": success,
        },
    )
def about(request):
    return render(request, "about.html")

CASE_STUDIES_DATA = {
    "custom-erp-system": {
        "slug": "custom-erp-system",
        "title": "Custom ERP System",
        "industry": "ERP Development",
        "project": "Nucon Aerospace",
        "client_challenge": "Nucon Aerospace was managing multiple departments using spreadsheets and disconnected software, resulting in duplicate data entry, delayed reporting, inventory inaccuracies, slow approval workflows, difficult employee management, and a lack of real-time business insights.",
        "solution": "KK Digital Growth designed and developed a fully customized ERP platform tailored to the client's workflow including modules for inventory management, procurement management, production tracking, employee management, billing & invoicing, and a reports dashboard.",
        "technologies": ["Frappe Framework", "Python", "Django", "React", "PostgreSQL", "REST API"],
        "results": [
            "45% Faster Operations",
            "Reduced Manual Work",
            "Real-Time Reports",
            "Better Inventory Accuracy",
            "Improved Employee Productivity"
        ],
        "image": "images/case-erp.png",
        "overview": "KK Digital Growth partnered with Nucon Aerospace to replace their manual business operations with a centralized ERP platform. The company required a secure and scalable solution to manage inventory, procurement, production workflows, employee records, billing, reporting and day-to-day operations from one integrated system.",
        "research": "Conducted comprehensive on-site analysis of Nucon's inventory workflows, warehouse layout, and billing bottlenecks.",
        "planning": "Planned a robust, modular ERP architecture with role-based access controls and detailed database schemas for stock management.",
        "ui_ux": "Designed a clean administrative dashboard prioritizing fast data entry, clear tabular logs, and interactive visual charts for reporting.",
        "development": "Developed custom backend systems utilizing Django/Frappe and configured a dynamic React frontend with secure token authentication.",
        "testing": "Performed automated integration tests for transaction concurrency and verified access permissions across user levels.",
        "deployment": "Deployed to secure cloud staging, ran staff onboarding workshops, and successfully transitioned operations to the live environment.",
        "testimonial": "The ERP system developed by KK Digital Growth transformed our business operations. Everything is now centralized, faster and easier to manage.",
        "testimonial_author": "Operations & Logistics Team, Nucon Aerospace",
        "duration": "6 Months"
    },
    "business-website": {
        "slug": "business-website",
        "title": "Corporate Business Website",
        "industry": "Website Development",
        "project": "KNS Metal Solutions",
        "client_challenge": "KNS Metal Solutions lacked a modern digital presence and branding, and needed a responsive, SEO-friendly corporate website with an integrated enquiry system to capture customer requests.",
        "solution": "KK Digital Growth designed and developed a fully responsive corporate website with a premium UI/UX, product showcase, service pages, contact forms, admin management dashboard, and SEO optimization.",
        "technologies": ["HTML", "CSS", "JavaScript", "React", "Django", "PostgreSQL", "REST API"],
        "results": [
            "Improved Brand Visibility",
            "Increased Customer Enquiries",
            "Better User Experience",
            "Faster Website Performance"
        ],
        "image": "images/case-web.png",
        "overview": "KK Digital Growth designed and developed a modern corporate website for KNS Metal Solutions to establish a strong online presence, showcase products and services, improve customer engagement and generate business enquiries.",
        "research": "Audited competing industrial websites and identified key opportunities to optimize search ranking and inquiry conversion rate.",
        "planning": "Mapped a clear visitor journey focusing on seamless navigation from the services list directly to custom inquiry forms.",
        "ui_ux": "Created a premium corporate design using custom typography, subtle scroll animations, and a responsive showcase layout.",
        "development": "Implemented responsive frontend templates using HTML/CSS/JavaScript and built a secure inquiry pipeline in the Django backend.",
        "testing": "Validated contact form submissions, optimized asset delivery for fast load speeds, and tested responsive screen sizes.",
        "deployment": "Configured SSL certifications and hosted the website on a secure VPS server for maximum uptime.",
        "testimonial": "KK Digital Growth delivered exactly what we needed. The website reflects our company professionally and has significantly improved our online visibility.",
        "testimonial_author": "Management Team, KNS Metal Solutions",
        "duration": "2 Months"
    },
    "mobile-application": {
        "slug": "mobile-application",
        "title": "Law Management Mobile Application",
        "industry": "Mobile Application Development",
        "project": "Law App",
        "client_challenge": "The client required a secure mobile solution for digital appointment booking, document management, direct communication, case tracking, and push notifications.",
        "solution": "KK Digital Growth developed a custom cross-platform mobile application with secure login, dashboard, appointment booking, case tracking, notifications, document upload, user profile management, and REST API integration.",
        "technologies": ["Flutter", "Django REST API", "Python", "PostgreSQL", "Firebase Notifications"],
        "results": [
            "Improved Client Communication",
            "Faster Appointment Management",
            "Digital Case Tracking",
            "Better User Experience"
        ],
        "image": "images/case-app.png",
        "overview": "KK Digital Growth developed a smart mobile application for legal professionals and clients to simplify appointment booking, case tracking, document management and legal consultation.",
        "research": "Interviewed legal practitioners and clients to determine key mobile features, focusing on secure communication and easy booking.",
        "planning": "Designed appointment slot synchronization logic, secure document upload flow, and Firebase notification event schemas.",
        "ui_ux": "Developed a user-friendly mobile interface utilizing interactive calendar widgets, secure file upload lists, and a dark mode.",
        "development": "Built a cross-platform mobile application in Flutter and integrated it with a secure Django REST API database backend.",
        "testing": "Validated real-time Firebase notification delivery, appointment scheduling conflicts, and secure document upload/download.",
        "deployment": "Configured App Store and Play Store metadata and launched the application, setting up automated CI/CD update workflows.",
        "testimonial": "The mobile application streamlined our legal services and made communication with clients much easier.",
        "testimonial_author": "Legal Operations Team, Law App",
        "duration": "4 Months"
    }
}

def case_studies(request):
    return render(request, "case-studies.html", {"case_studies": CASE_STUDIES_DATA.values()})

def case_study_detail(request, slug):
    case_study = CASE_STUDIES_DATA.get(slug)
    if not case_study:
        from django.http import Http404
        raise Http404("Case study not found")
    return render(request, "case-study-detail.html", {"case": case_study})