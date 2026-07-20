import os
import sys

sys.path.insert(0, "src")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

import django

django.setup()

from django.utils import timezone

from apps.executions.models import TestExecution
from apps.projects.models import Project
from apps.reports.models import Report
from apps.reports.views import build_report_content
from apps.requirements.models import Requirement, RequirementVersion
from apps.users.models import User


PROJECT_CODES = ("PRJ-002", "PRJ-003", "PRJ-004")


def first_teacher(project):
    return project.members.filter(role=User.Roles.TEACHER).order_by("id").first()


def review_requirements(project, teacher):
    if not teacher:
        return 0

    created = 0
    requirements = Requirement.objects.filter(project=project, status=Requirement.Status.APPROVED)
    for requirement in requirements:
        has_teacher_review = requirement.versions.filter(
            changed_by__role=User.Roles.TEACHER,
            change_reason__icontains="Revision docente",
        ).exists()
        if has_teacher_review:
            continue

        latest_version = requirement.versions.order_by("-version_number").first()
        next_number = (latest_version.version_number if latest_version else 0) + 1
        RequirementVersion.objects.create(
            requirement=requirement,
            version_number=next_number,
            title=requirement.title,
            description=requirement.description,
            requirement_type=requirement.requirement_type,
            priority=requirement.priority,
            status=requirement.status,
            changed_by=teacher,
            change_reason="Revision docente masiva para informe final de calidad",
            snapshot={
                "project_id": project.pk,
                "code": requirement.code,
                "title": requirement.title,
                "status": requirement.status,
            },
        )
        created += 1
    return created


def review_executions(project, teacher):
    if not teacher:
        return 0

    reviewed = 0
    executions = TestExecution.objects.filter(test_case__test_plan__project=project)
    for execution in executions:
        target_status = execution.review_status
        if execution.review_status == TestExecution.ReviewStatus.PENDING:
            if execution.result == TestExecution.Result.PASSED:
                target_status = TestExecution.ReviewStatus.VALIDATED
            else:
                target_status = TestExecution.ReviewStatus.NEEDS_FIX

        needs_reviewer = execution.reviewed_by_id != teacher.pk
        needs_status = execution.review_status != target_status
        if not needs_reviewer and not needs_status and execution.review_notes:
            continue

        execution.review_status = target_status
        execution.reviewed_by = teacher
        execution.reviewed_at = execution.reviewed_at or timezone.now()
        if target_status == TestExecution.ReviewStatus.VALIDATED:
            execution.review_notes = execution.review_notes or "Ejecucion validada para el informe final de calidad."
        elif target_status == TestExecution.ReviewStatus.NEEDS_FIX:
            execution.review_notes = execution.review_notes or "Ejecucion revisada con observaciones; requiere correccion o confirmacion."
        elif target_status == TestExecution.ReviewStatus.REJECTED:
            execution.review_notes = execution.review_notes or "Ejecucion rechazada por revision docente."
        execution.save(update_fields=["review_status", "reviewed_by", "reviewed_at", "review_notes", "updated_at"])
        reviewed += 1
    return reviewed


def sync_report(project, teacher):
    report = Report.objects.filter(project=project, report_type=Report.ReportType.FINAL).order_by("created_at").first()
    if not report:
        report = Report(project=project, report_type=Report.ReportType.FINAL)

    report.title = f"Informe final de calidad - {project.code}"
    report.generated_by = teacher or project.created_by
    report.content = build_report_content(report)
    report.save()
    return report


def main():
    for code in PROJECT_CODES:
        project = Project.objects.get(code=code)
        teacher = first_teacher(project)
        requirement_reviews = review_requirements(project, teacher)
        execution_reviews = review_executions(project, teacher)
        report = sync_report(project, teacher)
        print(
            code,
            "teacher=",
            teacher.email if teacher else "SIN_DOCENTE",
            "requirement_reviews=",
            requirement_reviews,
            "execution_reviews=",
            execution_reviews,
            "report=",
            report.id,
            report.title,
        )


if __name__ == "__main__":
    main()
