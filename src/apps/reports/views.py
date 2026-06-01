from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from apps.defects.models import Defect
from apps.requirements.models import Requirement
from apps.testcases.models import TestCase

from .forms import ReportForm
from .models import Report


REPORT_CARDS = [
    {
        'title': 'Informe de Cobertura',
        'description': 'Reporte completo de cobertura de pruebas',
        'icon': 'bi-file-earmark-text',
        'tone': 'brand',
        'type': Report.ReportType.COVERAGE,
    },
    {
        'title': 'Reporte de Ejecución',
        'description': 'Resultados de ejecución de casos de prueba',
        'icon': 'bi-file-earmark-check',
        'tone': 'success',
        'type': Report.ReportType.EXECUTION,
    },
    {
        'title': 'Análisis de Defectos',
        'description': 'Estadísticas y métricas de defectos',
        'icon': 'bi-file-earmark-medical',
        'tone': 'danger',
        'type': Report.ReportType.DEFECTS,
    },
]

CONTENT_LABELS = {
    'project': 'Proyecto',
    'requirements': 'Total de requisitos',
    'covered_requirements': 'Requisitos cubiertos',
    'coverage': 'Cobertura (%)',
    'test_cases': 'Casos de prueba',
    'defects': 'Defectos',
    'open_defects': 'Defectos abiertos',
}


def build_report_content(report):
    project = report.project
    requirements = Requirement.objects.filter(project=project)
    test_cases = TestCase.objects.filter(test_plan__project=project)
    defects = Defect.objects.filter(project=project)
    covered_requirements = requirements.filter(test_cases__isnull=False).distinct().count()
    total_requirements = requirements.count()
    coverage = round((covered_requirements / total_requirements) * 100) if total_requirements else 0

    return {
        'project': project.name,
        'requirements': total_requirements,
        'covered_requirements': covered_requirements,
        'coverage': coverage,
        'test_cases': test_cases.count(),
        'defects': defects.count(),
        'open_defects': defects.filter(status=Defect.Status.OPEN).count(),
    }


@login_required
def report_list_view(request):
    form = ReportForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        report = form.save(commit=False)
        report.generated_by = request.user
        report.content = build_report_content(report)
        report.save()
        return redirect('reports:index')

    return render(
        request,
        'reports/index.html',
        {
            'report_cards': REPORT_CARDS,
            'reports': Report.objects.select_related('project', 'generated_by'),
            'form': form,
            'show_modal': request.method == 'POST' and form.errors,
        },
    )


@login_required
def report_detail_view(request, pk):
    report = get_object_or_404(Report.objects.select_related('project', 'generated_by'), pk=pk)
    return render(
        request,
        'reports/detail.html',
        {
            'report': report,
            'content_items': [
                (CONTENT_LABELS.get(key, key.replace('_', ' ').title()), value)
                for key, value in report.content.items()
            ],
        },
    )


def build_unl_pdf(buffer, report):
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name='UNLTitle',
            parent=styles['Title'],
            alignment=TA_CENTER,
            textColor=colors.HexColor('#0b315f'),
            fontSize=16,
            leading=20,
            spaceAfter=10,
        )
    )
    styles.add(
        ParagraphStyle(
            name='UNLSubtitle',
            parent=styles['Normal'],
            alignment=TA_CENTER,
            textColor=colors.HexColor('#24496f'),
            fontSize=10,
            leading=13,
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name='SectionTitle',
            parent=styles['Heading2'],
            textColor=colors.HexColor('#0b315f'),
            fontSize=12,
            leading=16,
            spaceBefore=14,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name='BodySmall',
            parent=styles['Normal'],
            alignment=TA_LEFT,
            fontSize=9,
            leading=12,
        )
    )

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=1.6 * cm,
        bottomMargin=1.8 * cm,
        title=report.title,
    )

    story = [
        Paragraph('UNIVERSIDAD NACIONAL DE LOJA', styles['UNLTitle']),
        Paragraph('Facultad de la Energía, las Industrias y los Recursos Naturales no Renovables', styles['UNLSubtitle']),
        Paragraph('Carrera de Computación', styles['UNLSubtitle']),
        Paragraph('Plataforma ISTQB - Gestión del Ciclo de Vida de Pruebas', styles['UNLSubtitle']),
        Spacer(1, 0.35 * cm),
    ]

    generated_by = 'Sistema'
    if report.generated_by:
        generated_by = report.generated_by.get_full_name() or report.generated_by.email

    header_table = Table(
        [
            ['Informe', report.title],
            ['Tipo', report.get_report_type_display()],
            ['Proyecto', report.project.name],
            ['Generado por', generated_by],
            ['Fecha', report.created_at.strftime('%d/%m/%Y')],
        ],
        colWidths=[4 * cm, 12 * cm],
    )
    header_table.setStyle(
        TableStyle(
            [
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#eaf4fb')),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#0b315f')),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#dbe7f2')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('PADDING', (0, 0), (-1, -1), 7),
            ]
        )
    )
    story.append(header_table)
    story.append(Paragraph('Resumen del reporte', styles['SectionTitle']))

    content_rows = [['Métrica', 'Valor']]
    for key, value in report.content.items():
        content_rows.append([CONTENT_LABELS.get(key, key.replace('_', ' ').title()), str(value)])

    content_table = Table(content_rows, colWidths=[8 * cm, 8 * cm])
    content_table.setStyle(
        TableStyle(
            [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0b315f')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#dbe7f2')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fbfe')]),
                ('PADDING', (0, 0), (-1, -1), 7),
            ]
        )
    )
    story.append(content_table)
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph('Observación institucional', styles['SectionTitle']))
    story.append(
        Paragraph(
            'Este documento fue generado por la Plataforma ISTQB como evidencia de seguimiento académico '
            'del ciclo de vida de pruebas de software. La información debe ser revisada por el docente tutor '
            'o responsable del proyecto antes de su presentación formal.',
            styles['BodySmall'],
        )
    )

    doc.build(story)


@login_required
def report_download_view(request, pk):
    report = get_object_or_404(Report, pk=pk)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=\"reporte-unl-{report.id}.pdf\"'
    build_unl_pdf(response, report)
    return response
