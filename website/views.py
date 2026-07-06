from django.shortcuts import render
from .models import Consultation
from .forms import ContactForm


TESTIMONIALS_DATA = [
    {
        "client_name": "Meera Basu Sarees",
        "logo_image": "images/meerabasu-home.png",
        "feedback_text": "KK Digital Growth transformed our boutique saree brand with a gorgeous, high-converting Shopify store. The elegant typography and seamless shopping experience perfectly reflect our heritage.",
        "author": "Ananya Basu",
        "designation": "Founder & Creative Director",
        "industry": "E-commerce & Retail",
    },
    {
        "client_name": "KNS Metal Solutions",
        "logo_image": "images/kns-metal.png",
        "feedback_text": "The custom lead generation website built by their team has significantly increased our quote requests. Professional communication, high performance, and robust industrial showcase.",
        "author": "Marcus Vance",
        "designation": "Managing Director",
        "industry": "Industrial Manufacturing",
    },
    {
        "client_name": "LaserFold Australia",
        "logo_image": "images/laserfold.png",
        "feedback_text": "Their developer team delivered a lightning-fast custom web app that lets our clients explore metal fabrication services with ease. Highly recommended tech partner.",
        "author": "David Harrison",
        "designation": "Director of Operations",
        "industry": "Metal Fabrication",
    },
    {
        "client_name": "GenieStudio",
        "logo_image": "images/geniestudio.png",
        "feedback_text": "A highly visual and modern site that showcases our podcast and creative photography studios perfectly. The UI/UX is outstanding and captures our studio's vibe.",
        "author": "Kabir Mehta",
        "designation": "Founder & Producer",
        "industry": "Creative Media Studios",
    },
    {
        "client_name": "Buildzon Projects",
        "logo_image": "images/buildzon.png",
        "feedback_text": "Our real estate property catalog has never looked better. The lead generation workflows and custom admin panel are smooth, intuitive, and extremely fast.",
        "author": "Rohan Sharma",
        "designation": "Managing Director",
        "industry": "Real Estate & Construction",
    },
    {
        "client_name": "Nucon Aerospace",
        "logo_image": "images/nucon.png",
        "feedback_text": "The custom corporate system developed by KK Digital Growth transformed our internal motion control documentation. Enterprise-grade execution and secure infrastructure.",
        "author": "Rajesh K. Prasad",
        "designation": "VP of Operations",
        "industry": "Aerospace & Defense",
    },
    {
        "client_name": "Synergene API",
        "logo_image": "images/synergene.png",
        "feedback_text": "A top-tier pharmaceutical product database and compliance website. Their team adhered to our strict documentation guidelines and delivered a stellar corporate presence.",
        "author": "Dr. S. Srinivasan",
        "designation": "Director of Quality Assurance",
        "industry": "Pharmaceuticals",
    },
    {
        "client_name": "Vivodyne",
        "logo_image": "images/vivodyne.png",
        "feedback_text": "An immersive web experience that explains our AI-powered biotech organ models to global partners. The advanced animations and performance are state-of-the-art.",
        "author": "Dr. Andrei Georgescu",
        "designation": "CEO & Chief Scientist",
        "industry": "Biotechnology",
    },
    {
        "client_name": "Decagon AI",
        "logo_image": "images/decagon.png",
        "feedback_text": "They built a clean, modern marketing website for our conversational AI customer agents. High performance, SEO-focused, and completely responsive on all platforms.",
        "author": "Jesse Zhang",
        "designation": "Head of Customer Experience",
        "industry": "Artificial Intelligence & SaaS",
    },
    {
        "client_name": "Freenome",
        "logo_image": "images/freenome.png",
        "feedback_text": "A highly secure, clean, and modern healthcare informational site for our cancer detection trials. Exceptional attention to detail, accessibility, and speed.",
        "author": "Dr. Sarah Jenkins",
        "designation": "Lead Clinical Researcher",
        "industry": "Healthcare Research",
    },
    {
        "client_name": "Naren Ultrasound",
        "logo_image": "images/naren.png",
        "feedback_text": "The patient booking site has streamlined our clinic's scan scheduling. Patients love the clean, simple interface, and our operational efficiency has doubled.",
        "author": "Dr. N. Hemalatha",
        "designation": "Founder & Head Sonologist",
        "industry": "Medical Diagnostics",
    },
]


def home(request):
    return render(request, "home.html", {"testimonials": TESTIMONIALS_DATA})


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
            {"success": True, "testimonials": TESTIMONIALS_DATA},
        )

    return render(request, "consultation.html", {"testimonials": TESTIMONIALS_DATA})


def services(request):
    return render(request, "services.html")


def process(request):
    return render(request, "process.html")


def clients(request):
    return render(request, "clients.html")


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
        "title": "Custom ERP system",
        "industry": "ERP development",
        "project": "Nucon Aerospace",
        "summary": "Nucon Aerospace replaced manual processes and spreadsheets with a custom, secure ERP solution that accelerated their operations by 45%.",
        "client_challenge": "Nucon Aerospace was managing complex manufacturing processes across three separate facilities using manual spreadsheets and disconnected legacy software. This split workflow led to severe operational challenges, including duplicate data entries, inventory counting errors, delayed invoice calculations, raw materials procurement bottlenecks, and an inability for the management team to view aggregate business performance metrics in real-time.",
        "solution": "KK Digital Growth engineered a centralized, cloud-based ERP solution built with Django on the backend and custom React widgets on the frontend. The platform integrates real-time inventory ledgers with multi-warehouse tracking, automated procurement and RFQ approval matrices, production routing stages, HR payroll configurations, automated invoicing, and interactive reporting dashboards for executive oversight.",
        "technologies": ["Frappe Framework", "Python", "Django", "React", "PostgreSQL", "REST API"],
        "results": [
            "45% Faster Operations",
            "Reduced Manual Work",
            "Real-Time Reports",
            "Better Inventory Accuracy",
            "Improved Employee Productivity"
        ],
        "image": "images/case-erp.png",
        "overview": "We partnered with Nucon Aerospace to replace their manual business operations with a centralized ERP platform. The company required a secure and scalable solution to manage inventory, procurement, production workflows, employee records, billing, reporting and day-to-day operations from one integrated system, optimizing resource planning across all manufacturing facilities.",
        "research": "Conducted comprehensive on-site analysis of Nucon's inventory workflows, warehouse layout, and billing bottlenecks, interviewing department heads and floor operators to map the baseline logistics and identify processing lag points.",
        "planning": "Planned a modular ERP architecture with role-based access controls and detailed database schemas for stock management, securing transaction concurrency handles and database index triggers in PostgreSQL for high-speed tracking.",
        "ui_ux": "Designed a clean administrative dashboard prioritizing fast data entry, clear tabular logs, and interactive visual charts for reporting, allowing administrative users to view stock fluctuations and approve quotes with minimal clicks.",
        "development": "Developed custom backend systems utilizing Django/Frappe and configured a dynamic React frontend with secure token authentication, creating automatic PDF invoicing layouts and integrating multiple API hooks.",
        "testing": "Performed automated integration tests for transaction concurrency and verified access permissions across user levels, executing load testing scenarios to simulate peak system stress during shifts.",
        "deployment": "Deployed to secure cloud staging, ran staff onboarding workshops, and successfully transitioned operations to the live environment, monitoring error metrics and offering ongoing post-launch scaling services.",
        "testimonial": "The ERP system developed by KK Digital Growth transformed our business operations. Everything is now centralized, faster and easier to manage.",
        "testimonial_author": "Operations & Logistics Team, Nucon Aerospace",
        "duration": "6 Months"
    },
    "business-website": {
        "slug": "business-website",
        "title": "Corporate business website",
        "industry": "Website development",
        "project": "KNS Metal Solutions",
        "summary": "KNS Metal Solutions established a modern corporate website with a custom inquiry system, boosting search visibility and customer leads.",
        "client_challenge": "KNS Metal Solutions lacked a modern digital presence, relying heavily on offline brochures and word-of-mouth. Their legacy web page was outdated, unresponsive on mobile screens, and failed to appear in search queries for key metal fabrication services. Additionally, they lacked a structured way for potential clients to upload CAD design blueprints and request custom engineering estimates online.",
        "solution": "KK Digital Growth developed a high-speed corporate web platform featuring a mobile-first UI, a custom product catalog with categorization, a secure customer inquiry system supporting large file uploads (CAD designs/PDF estimates), a custom administrative management dashboard, and advanced SEO configuration targeting commercial terms.",
        "client_challenge_detail": "KNS Metal Solutions lacked a modern digital presence and branding, and needed a responsive, SEO-friendly corporate website with an integrated enquiry system to capture customer requests.",
        "solution_detail": "KK Digital Growth designed and developed a fully responsive corporate website with a premium UI/UX, product showcase, service pages, contact forms, admin management dashboard, and SEO optimization.",
        "technologies": ["HTML", "CSS", "JavaScript", "React", "Django", "PostgreSQL", "REST API"],
        "results": [
            "Improved Brand Visibility",
            "Increased Customer Enquiries",
            "Better User Experience",
            "Faster Website Performance"
        ],
        "image": "images/case-web.png",
        "overview": "We designed and developed a modern corporate website for KNS Metal Solutions to establish a strong online presence, showcase products and services, improve customer engagement and generate business enquiries, turning passive traffic into qualified project leads.",
        "research": "Audited competing industrial websites and identified key opportunities to optimize search ranking and inquiry conversion rate, reviewing the high-volume search terms used by engineering procurement managers.",
        "planning": "Mapped a clear visitor journey focusing on seamless navigation from the services list directly to custom inquiry forms, designing secure upload paths for CAD file schemas.",
        "ui_ux": "Created a premium corporate design using custom typography, subtle scroll animations, and a responsive showcase layout, utilizing high-resolution imagery and industrial design tones.",
        "development": "Implemented responsive frontend templates using HTML/CSS/JavaScript and built a secure inquiry pipeline in the Django backend, configuring automatic email triggers for the sales team.",
        "testing": "Validated contact form submissions, optimized asset delivery for fast load speeds, and tested responsive screen sizes, assuring cross-browser compatibility.",
        "deployment": "Configured SSL certifications and hosted the website on a secure VPS server for maximum uptime, connecting Google Search Console metrics for indexing checks.",
        "testimonial": "KK Digital Growth delivered exactly what we needed. The website reflects our company professionally and has significantly improved our online visibility.",
        "testimonial_author": "Management Team, KNS Metal Solutions",
        "duration": "2 Months"
    },
    "mobile-application": {
        "slug": "mobile-application",
        "title": "Law management mobile application",
        "industry": "Mobile application development",
        "project": "Law App",
        "summary": "Law App modernized attorney-client scheduling and case records tracking with a secure Flutter cross-platform mobile application.",
        "client_challenge": "The law firm was struggling with high administrative overhead from scheduling client consultations, tracking legal case progression, managing document exchanges via insecure email chains, and answering constant phone calls regarding status updates. They required a secure, mobile-friendly hub accessible on both iOS and Android.",
        "solution": "We built a cross-platform mobile application in Flutter connected to a Django REST API backend. The app integrates: 1) Dynamic appointment scheduling sync. 2) Secure, encrypted document vault supporting PDFs/images. 3) Real-time case tracking timeline widgets. 4) Push notification alerts for upcoming hearings or new files. 5) A legal professional web admin dashboard.",
        "technologies": ["Flutter", "Django REST API", "Python", "PostgreSQL", "Firebase Notifications"],
        "results": [
            "Improved Client Communication",
            "Faster Appointment Management",
            "Digital Case Tracking",
            "Better User Experience"
        ],
        "image": "images/case-app.png",
        "overview": "We developed a smart mobile application for legal professionals and clients to simplify appointment booking, case tracking, document management and legal consultation, reducing call overhead and improving digital security.",
        "research": "Interviewed legal practitioners and clients to determine key mobile features, focusing on secure communication, automated appointment sync, and easy file retrieval.",
        "planning": "Designed appointment slot synchronization logic, secure document upload flow, and Firebase notification event schemas, verifying strict HIPAA compliance data transit rules.",
        "ui_ux": "Developed a user-friendly mobile interface utilizing interactive calendar widgets, secure file upload lists, and a dark mode, creating an accessible user interface for all age groups.",
        "development": "Built a cross-platform mobile application in Flutter and integrated it with a secure Django REST API database backend, building a token-based authentication workflow.",
        "testing": "Validated real-time Firebase notification delivery, appointment scheduling conflicts, and secure document upload/download, testing the app on multiple simulator platforms.",
        "deployment": "Configured App Store and Play Store metadata and launched the application, setting up automated CI/CD update workflows and server crash logging triggers.",
        "testimonial": "The mobile application streamlined our legal services and made communication with clients much easier.",
        "testimonial_author": "Legal Operations Team, Law App",
        "duration": "4 Months"
    },
    "skyroot-aerospace": {
        "slug": "skyroot-aerospace",
        "title": "ERP Development for Skyroot Aerospace",
        "industry": "ERP development",
        "project": "Skyroot Aerospace",
        "summary": "Aerospace Enterprise Resource Planning (ERP) System for a Space Technology Company",
        "client_challenge": "As the organization expanded its rocket design, manufacturing, testing, and launch operations, multiple departments relied on separate tools and spreadsheets for procurement, inventory, engineering documentation, production planning, finance, and HR. This led to: Lack of real-time inventory visibility, Delays in procurement approvals, Difficulty tracking aerospace-grade components, Manual engineering change approvals, Fragmented project reporting, and Compliance documentation challenges.",
        "solution": "Developing a centralized ERP platform capable of: Managing the complete product lifecycle, Tracking aerospace components from procurement to launch, Integrating manufacturing with engineering, Improving quality assurance, Automating finance and procurement workflows, and Providing executive dashboards.",
        "technologies": ["React.js", "TypeScript", "Node.js", "Express.js", "PostgreSQL", "AWS", "Docker", "Kubernetes", "Power BI", "Grafana"],
        "results": [
            "Real-time inventory visibility",
            "BOM & Version Control",
            "ISO/AS9100 Compliance",
            "Automated procurement approvals",
            "Centralized rocket program tracking"
        ],
        "image": "images/case-erp.png",
        "overview": "Aerospace Enterprise Resource Planning (ERP) System for a Space Technology Company. Unifying engineering, inventory, procurement, quality assurance, project management, and launch readiness workflows under a single, high-integrity administrative dashboard.",
        "research": "Conducted workshops with rocket program managers and compliance officers to map the components lifecycle under strict AS9100 tracking standards.",
        "planning": "Designed high-integrity database relational schemas in PostgreSQL supporting nested bills of materials (BOM), CAD versioning history, and state machines for ECO change loops.",
        "ui_ux": "Designed simple floor interface layouts for assembly logs and clean status dashboards for launch programs, key milestone tracking, and approvals management.",
        "development": "Coded modular microservices in Express/Node.js for inventory levels, built client tables in React and TypeScript, and secured roles via JWT token gates.",
        "testing": "Validated engineering change order (ECO) status updates, RFQ approval hierarchies, and material trace paths using automated integration scripts.",
        "deployment": "Successfully deployed production containers using Docker/Kubernetes on AWS, integrated Power BI reporting models, and set up compliance logging.",
        "testimonial": "The custom ERP system designed by KK Digital Growth integrated our entire aerospace supply chain and rocket engineering operations under a single, secure, and compliant platform.",
        "testimonial_author": "Engineering & Program Management Team, Skyroot Aerospace",
        "duration": "12 Months",
        "objectives": [
            "Managing the complete product lifecycle",
            "Tracking aerospace components from procurement to launch",
            "Integrating manufacturing with engineering",
            "Improving quality assurance",
            "Automating finance and procurement workflows",
            "Providing executive dashboards"
        ],
        "erp_modules": [
            {
                "name": "Engineering Management",
                "features": ["Engineering Change Requests (ECR)", "Engineering Change Orders (ECO)", "Bill of Materials (BOM)", "Version Control & CAD File Management"]
            },
            {
                "name": "Procurement",
                "features": ["Vendor Management", "RFQ Management", "Purchase Orders & Vendor Evaluation", "Contract Management"]
            },
            {
                "name": "Inventory",
                "features": ["Rocket Component Tracking", "Warehouse Management", "Batch & Serial Number Tracking", "Material Traceability & Stock Forecasting"]
            },
            {
                "name": "Manufacturing",
                "features": ["Production Planning", "Work Orders", "Shop Floor Management", "Assembly & Component Consumption Tracking"]
            },
            {
                "name": "Quality Management",
                "features": ["Inspection Checklists", "Non-Conformance Reports", "Root Cause Analysis", "Corrective Actions & ISO/AS9100 Compliance"]
            },
            {
                "name": "Project Management",
                "features": ["Rocket Program Tracking", "Budget Management & Resource Allocation", "Milestone Monitoring", "Risk Register"]
            },
            {
                "name": "Finance",
                "features": ["Budget Control", "Accounts Payable & Receivable", "Cost Center Accounting & Project Cost Analysis"]
            },
            {
                "name": "HR",
                "features": ["Employee Management", "Attendance, Leave & Payroll", "Training Records"]
            }
        ],
        "system_workflow": [
            "Supplier", "Procurement", "Inventory", "Production", "Quality Inspection", "Assembly", "Testing", "Launch Readiness", "Finance & Reporting"
        ]
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