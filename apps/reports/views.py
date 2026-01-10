from django.http import HttpResponse, JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from datetime import datetime
from io import BytesIO

@api_view(['GET'])
@permission_classes([AllowAny])
def export_report(request):
    fmt = request.GET.get('format', 'csv')
    rtype = request.GET.get('type', 'deliveries')
    from_ts = request.GET.get('from')
    to_ts = request.GET.get('to')

    # parse dates if provided
    try:
        dt_from = datetime.fromisoformat(from_ts) if from_ts else None
    except Exception:
        dt_from = None
    try:
        dt_to = datetime.fromisoformat(to_ts) if to_ts else None
    except Exception:
        dt_to = None

    # Collect data depending on requested type: deliveries or orders
    rows = []
    try:
        if rtype in ('deliveries', 'livraisons'):
            from apps.sales.models import Livraison
            qs = Livraison.objects.all()
            if dt_from:
                qs = qs.filter(timestamp__gte=dt_from)
            if dt_to:
                qs = qs.filter(timestamp__lte=dt_to)
            for l in qs.order_by('timestamp'):
                rows.append({
                    'id': l.id,
                    'client': str(l.client),
                    'timestamp': l.timestamp.isoformat(),
                    'lat': l.gps_lat,
                    'lng': l.gps_lng,
                })
        elif rtype in ('orders', 'commandes'):
            from apps.sales.models import Commande
            qs = Commande.objects.all()
            if dt_from:
                qs = qs.filter(created_at__gte=dt_from)
            if dt_to:
                qs = qs.filter(created_at__lte=dt_to)
            for c in qs.order_by('created_at'):
                rows.append({
                    'id': c.id,
                    'client': str(c.client),
                    'status': getattr(c, 'statut', getattr(c, 'status', '')),
                    'amount': float(c.montant) if c.montant is not None else 0,
                    'requested_at': c.date_souhaitee.isoformat() if c.date_souhaitee else '',
                    'created_at': c.created_at.isoformat() if c.created_at else '',
                })
        else:
            # unknown type: fallback to deliveries behavior
            from apps.sales.models import Livraison
            qs = Livraison.objects.all()
            for l in qs.order_by('timestamp'):
                rows.append({
                    'id': l.id,
                    'client': str(l.client),
                    'timestamp': l.timestamp.isoformat(),
                    'lat': l.gps_lat,
                    'lng': l.gps_lng,
                })
    except Exception:
        # generic fallback sample row
        rows = [
            {'id': 1, 'client': 'Client A', 'timestamp': timezone.now().isoformat()},
        ]

    if fmt == 'csv':
        import csv, io
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        # Write headers depending on requested type
        if rtype in ('deliveries', 'livraisons'):
            writer.writerow(['id', 'client', 'timestamp', 'lat', 'lng'])
            for r in rows:
                writer.writerow([r.get('id'), r.get('client'), r.get('timestamp', ''), r.get('lat') or '', r.get('lng') or ''])
        elif rtype in ('orders', 'commandes'):
            writer.writerow(['id', 'client', 'status', 'amount', 'requested_at', 'created_at'])
            for r in rows:
                writer.writerow([r.get('id'), r.get('client'), r.get('status', ''), r.get('amount', ''), r.get('requested_at', ''), r.get('created_at', '')])
        else:
            writer.writerow(['id', 'client', 'timestamp', 'lat', 'lng'])
            for r in rows:
                writer.writerow([r.get('id'), r.get('client'), r.get('timestamp', ''), r.get('lat') or '', r.get('lng') or ''])
        resp = HttpResponse(buffer.getvalue(), content_type='text/csv; charset=utf-8')
        resp['Content-Disposition'] = 'attachment; filename="reports.csv"'
        return resp

    if fmt == 'excel':
        try:
            import openpyxl
            wb = openpyxl.Workbook()
            ws = wb.active
            if rtype in ('deliveries', 'livraisons'):
                ws.append(['id', 'client', 'timestamp', 'lat', 'lng'])
                for r in rows:
                    ws.append([r.get('id'), r.get('client'), r.get('timestamp', ''), r.get('lat'), r.get('lng')])
            elif rtype in ('orders', 'commandes'):
                ws.append(['id', 'client', 'status', 'amount', 'requested_at', 'created_at'])
                for r in rows:
                    ws.append([r.get('id'), r.get('client'), r.get('status', ''), r.get('amount', ''), r.get('requested_at', ''), r.get('created_at', '')])
            else:
                ws.append(['id', 'client', 'timestamp', 'lat', 'lng'])
                for r in rows:
                    ws.append([r.get('id'), r.get('client'), r.get('timestamp', ''), r.get('lat'), r.get('lng')])
            bio = BytesIO()
            wb.save(bio)
            bio.seek(0)
            resp = HttpResponse(bio.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            resp['Content-Disposition'] = 'attachment; filename="reports.xlsx"'
            return resp
        except Exception as e:
            return JsonResponse({'error': 'Excel support not installed on server', 'detail': str(e)}, status=501)

    if fmt == 'pdf':
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
            bio = BytesIO()
            c = canvas.Canvas(bio, pagesize=A4)
            y = 800
            c.setFont('Helvetica', 10)
            c.drawString(40, y, 'Report')
            y -= 30
            if rtype in ('orders', 'commandes'):
                c.drawString(40, y, 'id | client | status | amount | requested_at')
            else:
                c.drawString(40, y, 'id | client | timestamp | lat | lng')
            y -= 20
            for r in rows:
                if rtype in ('orders', 'commandes'):
                    line = f"{r.get('id')} | {r.get('client')} | {r.get('status','')} | {r.get('amount','')} | {r.get('requested_at','')}"
                else:
                    line = f"{r.get('id')} | {r.get('client')} | {r.get('timestamp','')} | {r.get('lat') or ''} | {r.get('lng') or ''}"
                c.drawString(40, y, line[:120])
                y -= 14
                if y < 60:
                    c.showPage()
                    y = 800
            c.save()
            bio.seek(0)
            resp = HttpResponse(bio.read(), content_type='application/pdf')
            resp['Content-Disposition'] = 'attachment; filename="report.pdf"'
            return resp
        except Exception as e:
            return JsonResponse({'error': 'PDF support not installed on server', 'detail': str(e)}, status=501)

    return JsonResponse({'error': 'Unsupported format'}, status=400)
import csv
import io as _io
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.http import HttpResponse
from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from openpyxl import Workbook
import io as _io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


class ReportsExportCSVView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        # sample data; replace with real query logic
        rows = [
            {"id": 1, "name": "Client A", "orders": 5, "revenue": 10000},
            {"id": 2, "name": "Client B", "orders": 2, "revenue": 4000},
        ]

        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["id", "name", "orders", "revenue"])
        for r in rows:
            writer.writerow([r["id"], r["name"], r["orders"], r["revenue"]])

        resp = HttpResponse(buf.getvalue(), content_type='text/csv')
        resp['Content-Disposition'] = 'attachment; filename="report.csv"'
        return resp


class ReportsExportExcelView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        rows = [
            {"id": 1, "name": "Client A", "orders": 5, "revenue": 10000},
            {"id": 2, "name": "Client B", "orders": 2, "revenue": 4000},
        ]

        wb = Workbook()
        ws = wb.active
        ws.append(["id", "name", "orders", "revenue"])
        for r in rows:
            ws.append([r["id"], r["name"], r["orders"], r["revenue"]])

        buf = _io.BytesIO()
        wb.save(buf)
        buf.seek(0)

        resp = HttpResponse(buf.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        resp['Content-Disposition'] = 'attachment; filename="report.xlsx"'
        return resp


class ReportsExportPDFView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        rows = [
            {"id": 1, "name": "Client A", "orders": 5, "revenue": 10000},
            {"id": 2, "name": "Client B", "orders": 2, "revenue": 4000},
        ]
        # compute KPIs
        total_revenue = sum(r.get('revenue', 0) for r in rows)
        total_clients = len(rows)
        avg_basket = int(total_revenue / total_clients) if total_clients else 0

        buf = _io.BytesIO()
        p = canvas.Canvas(buf, pagesize=A4)
        width, height = A4
        margin = 40
        y = height - margin

        # Title
        p.setFont('Helvetica-Bold', 18)
        p.drawString(margin, y, 'RÉSUMÉ DES VENTES')
        p.setFont('Helvetica', 10)
        p.drawString(width - margin - 150, y, datetime.now().strftime('%Y-%m-%d'))
        y -= 30

        # KPI cards (three cards horizontally)
        card_w = (width - margin * 2 - 20) / 3
        card_h = 60
        card_x = margin
        card_y = y - card_h
        from reportlab.lib import colors

        def draw_card(x, y, w, h, title, value):
            p.setFillColor(colors.whitesmoke)
            p.roundRect(x, y, w, h, 6, stroke=0, fill=1)
            p.setFillColor(colors.black)
            p.setFont('Helvetica', 9)
            p.drawString(x + 10, y + h - 18, title)
            p.setFont('Helvetica-Bold', 14)
            p.drawString(x + 10, y + 12, value)

        draw_card(card_x, card_y, card_w, card_h, 'TOTAL REVENU', f"{total_revenue:,} FCFA")
        draw_card(card_x + card_w + 10, card_y, card_w, card_h, 'TOTAL CLIENTS', str(total_clients))
        draw_card(card_x + 2 * (card_w + 10), card_y, card_w, card_h, 'PANIER MOYEN', f"{avg_basket:,} FCFA")

        y = card_y - 30

        # Details table header
        p.setFont('Helvetica-Bold', 11)
        p.drawString(margin, y, 'CLIENT')
        p.drawString(margin + 200, y, 'COMMANDES')
        p.drawString(margin + 280, y, 'BARRE VISUELLE')
        p.drawRightString(width - margin, y, 'REVENU')
        y -= 12
        p.setLineWidth(0.5)
        p.line(margin, y, width - margin, y)
        y -= 8

        # prepare bar scale
        max_orders = max((r.get('orders', 0) for r in rows), default=1)
        bar_x = margin + 280
        bar_w = 160
        for r in rows:
            if y < margin + 80:
                p.showPage()
                y = height - margin
            # client name
            p.setFont('Helvetica', 10)
            p.drawString(margin, y, r.get('name', ''))
            # orders
            p.drawString(margin + 200, y, str(r.get('orders', 0)))
            # visual bar background
            p.setStrokeColor(colors.lightgrey)
            p.setFillColor(colors.lightgrey)
            p.rect(bar_x, y - 6, bar_w, 10, stroke=0, fill=1)
            # filled portion
            fill_w = int((r.get('orders', 0) / max_orders) * bar_w) if max_orders else 0
            p.setFillColor(colors.darkblue)
            p.rect(bar_x, y - 6, fill_w, 10, stroke=0, fill=1)
            # revenue (right aligned)
            p.setFillColor(colors.black)
            p.drawRightString(width - margin, y, f"{r.get('revenue', 0):,} FCFA")
            y -= 20

        p.showPage()
        p.save()
        buf.seek(0)
        resp = HttpResponse(buf.read(), content_type='application/pdf')
        resp['Content-Disposition'] = 'attachment; filename="sales_summary.pdf"'
        return resp
