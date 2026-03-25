from rest_framework import viewsets, permissions, status, serializers
from rest_framework.response import Response
from .models import JobForm, JobFormQuestion
from .serializers import JobFormSerializer, JobFormQuestionSerializer
from companies.models import Company

class JobFormViewSet(viewsets.ModelViewSet):
    serializer_class = JobFormSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Employers can see their own forms, Job Seekers can see forms attached to jobs they're applying to
        # For simplicity in management, return company's forms
        user = self.request.user
        return JobForm.objects.filter(company__owner=user)

    def perform_create(self, serializer):
        # Allow specifying a company ID in the request data
        company_id = self.request.data.get('company')
        
        if company_id:
            try:
                # Ensure the user owns the specified company
                company = Company.objects.get(id=company_id, owner=self.request.user)
            except (Company.DoesNotExist, ValueError):
                raise serializers.ValidationError({"company": "الشركة المحددة غير موجودة أو لا تملكها."})
        else:
            # Fallback to the first company owned by the user
            company = Company.objects.filter(owner=self.request.user).first()
            
        if not company:
            raise serializers.ValidationError("يجب أن تملك شركة لإنشاء نموذج.")
            
        serializer.save(company=company)
