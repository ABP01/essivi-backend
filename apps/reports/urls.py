from django.urls import path
from . import views

# Use the function-based `export_report` for the generic `/export/` endpoint
# (it allows anonymous access for development). Keep class-based endpoints
# for explicit format routes.
urlpatterns = [
    path('export/', views.export_report, name='reports-export'),
    # Explicit CSV path endpoint (avoid DRF format query handling)
    path('export/csv/', views.export_report, name='reports-export-csv-path'),
    path('export/excel/', views.ReportsExportExcelView.as_view(), name='reports-export-excel'),
    path('export/pdf/', views.ReportsExportPDFView.as_view(), name='reports-export-pdf'),
]
