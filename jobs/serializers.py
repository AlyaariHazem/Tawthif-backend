from rest_framework import serializers
from .models import Job, JobCategory, JobBookmark, JobAlert
from companies.models import Company
from companies.serializers import CompanySerializer
from job_forms.serializers import JobFormSerializer


class JobCategorySerializer(serializers.ModelSerializer):
    jobs_count = serializers.SerializerMethodField()
    
    class Meta:
        model = JobCategory
        fields = ['id', 'name', 'slug', 'description', 'icon', 'is_active', 'jobs_count']
    
    def get_jobs_count(self, obj):
        return obj.jobs.filter(is_active=True).count()


class JobListSerializer(serializers.ModelSerializer):
    company = CompanySerializer(read_only=True)
    category = JobCategorySerializer(read_only=True)
    is_bookmarked = serializers.SerializerMethodField()
    applications_count = serializers.ReadOnlyField()
    custom_form = JobFormSerializer(read_only=True)
    class Meta:
        model = Job
        fields = [
            'id', 'title', 'slug','description','requirements', 'company', 'category', 'job_type', 
            'experience_level', 'city', 'salary_min', 'salary_max', 
            'is_salary_negotiable', 'application_deadline', 'is_active', 
            'is_featured', 'is_urgent', 'views_count', 'applications_count',
            'is_bookmarked', 'created_at','application_method', 'custom_form',
            'application_template', 'external_application_url', 'application_email',
            'is_ai_summary_enabled', 'ai_summary'
        ]
    
    def get_is_bookmarked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return JobBookmark.objects.filter(user=request.user, job=obj).exists()
        return False




class JobDetailSerializer(serializers.ModelSerializer):
    company = CompanySerializer(read_only=True)
    category = JobCategorySerializer(read_only=True)
    custom_form = JobFormSerializer(read_only=True)
    is_bookmarked = serializers.SerializerMethodField()
    applications_count = serializers.ReadOnlyField()
    is_applied = serializers.SerializerMethodField()
    
    class Meta:
        model = Job
        fields = '__all__'
    
    def get_is_bookmarked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return JobBookmark.objects.filter(user=request.user, job=obj).exists()
        return False
    
    def get_is_applied(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.applications.filter(applicant=request.user).exists()
        return False


class JobCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = [
            'title', 'description', 'requirements', 'responsibilities', 
            'benefits', 'skills', 'company', 'category', 'job_type', 
            'experience_level', 'education_level', 'city', 'salary_min', 'salary_max',
            'is_salary_negotiable', 'application_deadline',
            'contact_email', 'contact_phone', 'is_featured', 'is_urgent', 'is_active',
            'application_method', 'custom_form', 'application_template', 
            'external_application_url', 'application_email',
      
           'is_ai_summary_enabled', 'ai_summary'
        ]
        read_only_fields = ['ai_summary']
    
    def validate_company(self, value):
        request = self.context.get('request')
        if request and request.user.user_type != 'employer':
            raise serializers.ValidationError("فقط أصحاب العمل يمكنهم نشر الوظائف")
        if not value.is_verified:
            raise serializers.ValidationError("يجب توثيق الشركة لتستطيع نشر وظائف")
        
        # Check if user owns the company
        if value.owner != request.user:
            raise serializers.ValidationError("لا يمكنك نشر وظيفة لشركة لا تملكها")
        
        return value
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['posted_by'] = request.user
        # Generate slug from title
        from slugify import slugify
        import uuid
        base_slug = slugify(validated_data['title'])
        slug = base_slug
        counter = 1
        while Job.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        validated_data['slug'] = slug
        if validated_data.get('is_ai_summary_enabled'):
            from .ai_utils import generate_job_summary
            summary = generate_job_summary(
                job_title=validated_data.get('title'),
                description=validated_data.get('description'),
                requirements=validated_data.get('requirements'),
                benefits=validated_data.get('benefits'),
                experience=validated_data.get('experience_level'),
                salary=f"{validated_data.get('salary_min')} - {validated_data.get('salary_max')}"
            )
            if summary:
                validated_data['ai_summary'] = summary
        return super().create(validated_data)

            # def update(self, instance, validated_data):
            #     # Generate AI Summary if enabled and relevant fields changed, or if it was just enabled
            #     trigger_ai = validated_data.get('is_ai_summary_enabled', instance.is_ai_summary_enabled)
                
            #     if trigger_ai:
            #         # Only regenerate if content changed or if it was just turned on
            #         content_changed = any(
            #             validated_data.get(field) != getattr(instance, field)
            #             for field in ['title', 'description', 'requirements', 'benefits']
            #             if field in validated_data
            #         )
            #         just_enabled = validated_data.get('is_ai_summary_enabled') and not instance.is_ai_summary_enabled
                    
            #         if content_changed or just_enabled:
            #             from .ai_utils import generate_job_summary
            #             summary = generate_job_summary(
            #                 job_title=validated_data.get('title', instance.title),
            #                 description=validated_data.get('description', instance.description),
            #                 requirements=validated_data.get('requirements', instance.requirements),
            #                 benefits=validated_data.get('benefits', instance.benefits),
            #                 experience=validated_data.get('experience_level', instance.experience_level),
            #                 salary=f"{validated_data.get('salary_min', instance.salary_min)} - {validated_data.get('salary_max', instance.salary_max)}"
            #             )
            #             if summary:
            #                 validated_data['ai_summary'] = summary
                            
                
            #     return super().create(validated_data)


class JobBookmarkSerializer(serializers.ModelSerializer):
    job = JobListSerializer(read_only=True)
    
    class Meta:
        model = JobBookmark
        fields = ['id', 'job', 'created_at']


class JobAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobAlert
        fields = '__all__'
        read_only_fields = ['user']
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['user'] = request.user
        return super().create(validated_data)

