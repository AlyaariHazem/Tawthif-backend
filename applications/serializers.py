from rest_framework import serializers
from .models import JobApplication, Interview, ApplicationMessage, ApplicationStatusHistory, ApplicationResponse
from jobs.serializers import JobListSerializer
from job_forms.serializers import JobFormQuestionSerializer
from accounts.serializers import UserSerializer, JobSeekerProfile, ProfileDocumentSerializer

class ApplicationResponseSerializer(serializers.ModelSerializer):
    question_details = JobFormQuestionSerializer(source='question', read_only=True)
    
    class Meta:
        model = ApplicationResponse
        fields = ['id', 'question', 'question_details', 'answer_text', 'answer_file']

class JobApplicationSerializer(serializers.ModelSerializer):
    job = JobListSerializer(read_only=True)
    applicant = UserSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    documents_count = serializers.SerializerMethodField()
    
    class Meta:
        model = JobApplication
        fields = [
            'id', 'job', 'applicant', 'cover_letter', 'resume', 'portfolio_url',
            'expected_salary', 'availability_date', 'status', 'status_display',
            'notes', 'employer_notes', 'rating', 'is_viewed', 'viewed_at',
            'applied_at', 'updated_at', 'documents_count', 'filled_template'
        ]
        read_only_fields = [
            'applicant', 'employer_notes', 'rating', 'is_viewed', 
            'viewed_at', 'applied_at', 'updated_at', 'documents_count'
        ]

    def get_documents_count(self, obj):
        """عدد الوثائق المتاحة لصاحب العمل"""
        if hasattr(obj.applicant, 'job_seeker_profile'):
            return obj.applicant.job_seeker_profile.documents.filter(
                visibility__in=['public', 'employers_only']
            ).count()
        return 0


class JobApplicationDetailSerializer(JobApplicationSerializer):
    """Serializer مفصل لطلب التوظيف يتضمن المرفقات والإجابات المخصصة"""
    documents = serializers.SerializerMethodField()
    responses = ApplicationResponseSerializer(many=True, read_only=True)

    class Meta(JobApplicationSerializer.Meta):
        fields = JobApplicationSerializer.Meta.fields + ['documents', 'responses']

    def get_documents(self, obj):
        request = self.context.get('request')
        if not request:
            return []
            
        user = request.user
        # التحقق من أن المستخدم هو صاحب العمل أو الباحث عن عمل نفسه
        if user == obj.applicant or user == obj.job.posted_by:
            if hasattr(obj.applicant, 'job_seeker_profile'):
                from accounts.models import ProfileDocument
                docs = ProfileDocument.objects.filter(
                    job_seeker_profile=obj.applicant.job_seeker_profile,
                    visibility__in=['public', 'employers_only']
                )
                return ProfileDocumentSerializer(docs, many=True, context=self.context).data
        return []


class JobApplicationCreateSerializer(serializers.ModelSerializer):
    responses = ApplicationResponseSerializer(many=True, required=False)

    class Meta:
        model = JobApplication
        fields = [
            'job', 'cover_letter', 'resume', 'portfolio_url',
            'expected_salary', 'availability_date', 'notes',
            'filled_template', 'responses'
        ]

    # -------------------------------
    # Validate selected job
    # -------------------------------
    def validate_job(self, value):
        request = self.context.get('request')

        if not value.is_active:
            raise serializers.ValidationError("هذه الوظيفة غير متاحة للتقديم")

        if value.is_expired:
            raise serializers.ValidationError("انتهى موعد التقديم لهذه الوظيفة")

        if JobApplication.objects.filter(job=value, applicant=request.user).exists():
            raise serializers.ValidationError("لقد تقدمت لهذه الوظيفة من قبل")

        if request.user.user_type != 'job_seeker':
            raise serializers.ValidationError("فقط الباحثون عن عمل يمكنهم التقديم للوظائف")

        return value

    # -------------------------------
    # Auto-use resume from JobSeekerProfile
    # -------------------------------
    def validate(self, attrs):
        request = self.context.get('request')
        user = request.user

        # If user did not upload a resume in the application
        if not attrs.get('resume'):
            # Only require resume if it's a platform-based application method
            if attrs['job'].application_method in ['platform', 'custom_form', 'template_file']:
                profile = getattr(user, 'job_seeker_profile', None)
                if profile and profile.resume:
                    attrs['resume'] = profile.resume
                else:
                    raise serializers.ValidationError({
                        "resume": "يجب رفع السيرة الذاتية أو إضافتها في ملفك الشخصي"
                    })

        # Validate based on job application method
        # 1. Custom Form Validation
        if attrs['job'].application_method == 'custom_form':
            if not attrs.get('responses'):
                raise serializers.ValidationError({
                    "responses": "يجب الإجابة على استبيان التقديم لهذه الوظيفة"
                })
            
            # Basic check: were all required questions answered?
            form = attrs['job'].custom_form
            if form:
                required_question_ids = form.questions.filter(required=True).values_list('id', flat=True)
                provided_question_ids = [r['question'].id for r in attrs.get('responses', [])]
                
                for q_id in required_question_ids:
                    if q_id not in provided_question_ids:
                        raise serializers.ValidationError({
                            "responses": f"يجب الإجابة على جميع الأسئلة المطلوبة في الاستبيان"
                        })
                
                # Deep check: validate file answers and types
                for r in attrs.get('responses', []):
                    question = r['question']
                    if question.question_type == 'file':
                        if not r.get('answer_file'):
                            if question.required:
                                raise serializers.ValidationError({
                                    "responses": f"يجب رفع ملف للسؤال: {question.label}"
                                })
                        else:
                            # Validate file extension against question options if provided
                            if question.options:
                                import os
                                allowed_exts = [ext.strip().lower() for ext in question.options.split(',')]
                                # ensure dots are present
                                allowed_exts = [ext if ext.startswith('.') else f".{ext}" for ext in allowed_exts]
                                
                                file_ext = os.path.splitext(r['answer_file'].name)[1].lower()
                                if file_ext not in allowed_exts:
                                    raise serializers.ValidationError({
                                        "responses": f"نوع الملف للسؤال '{question.label}' غير مدعوم. الأنواع المسموحة هي: {question.options}"
                                    })
                    else:
                        # Non-file questions should use answer_text
                        if r.get('answer_file'):
                            raise serializers.ValidationError({
                                "responses": f"لا يمكن رفع ملف لهذا السؤال المخصص للنص: {question.label}"
                            })

        # 2. Template File Validation
        if attrs['job'].application_method == 'template_file':
            if not attrs.get('filled_template'):
                raise serializers.ValidationError({
                    "filled_template": "يجب رفع ملف تقديم الوظيفة المعبأ"
                })

        return attrs

    # -------------------------------
    # Set applicant automatically and handle responses
    # -------------------------------
    def create(self, validated_data):
        responses_data = validated_data.pop('responses', [])
        validated_data['applicant'] = self.context['request'].user
        
        # Set status for external methods
        job = validated_data.get('job')
        if job and job.application_method in ['external_link', 'email']:
            validated_data['status'] = 'external_redirect'
            
        application = super().create(validated_data)
        
        # Create responses
        for response_data in responses_data:
            ApplicationResponse.objects.create(application=application, **response_data)
            
        return application


class JobApplicationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobApplication
        fields = ['status', 'employer_notes', 'rating']
    
    def update(self, instance, validated_data):
        # Track status changes
        old_status = instance.status
        new_status = validated_data.get('status', old_status)
        
        if old_status != new_status:
            ApplicationStatusHistory.objects.create(
                application=instance,
                old_status=old_status,
                new_status=new_status,
                changed_by=self.context['request'].user,
                notes=validated_data.get('employer_notes', '')
            )
        
        return super().update(instance, validated_data)


class InterviewSerializer(serializers.ModelSerializer):
    application = JobApplicationSerializer(read_only=True)
    interview_type_display = serializers.CharField(source='get_interview_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Interview
        fields = [
            'id', 'application', 'interview_type', 'interview_type_display',
            'scheduled_date', 'duration_minutes', 'location', 'meeting_link',
            'interviewer_name', 'interviewer_email', 'status', 'status_display',
            'notes', 'feedback', 'score', 'created_at', 'updated_at'
        ]


class InterviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interview
        fields = [
            'application', 'interview_type', 'scheduled_date', 'duration_minutes',
            'location', 'meeting_link', 'interviewer_name', 'interviewer_email', 'notes'
        ]
    
    def validate_application(self, value):
        request = self.context.get('request')
        
        # Check if user owns the job
        if value.job.posted_by != request.user:
            raise serializers.ValidationError("لا يمكنك جدولة مقابلة لوظيفة لا تملكها")
        
        return value


class ApplicationMessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    sender_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ApplicationMessage
        fields = [
            'id', 'application', 'sender', 'sender_name', 'message',
            'attachment', 'is_read', 'sent_at'
        ]
        read_only_fields = ['sender', 'sent_at']
    
    def get_sender_name(self, obj):
        return f"{obj.sender.first_name} {obj.sender.last_name}".strip() or obj.sender.username
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['sender'] = request.user
        return super().create(validated_data)


class ApplicationStatusHistorySerializer(serializers.ModelSerializer):
    changed_by = UserSerializer(read_only=True)
    old_status_display = serializers.CharField(source='get_old_status_display', read_only=True)
    new_status_display = serializers.CharField(source='get_new_status_display', read_only=True)
    
    class Meta:
        model = ApplicationStatusHistory
        fields = [
            'id', 'old_status', 'old_status_display', 'new_status', 
            'new_status_display', 'changed_by', 'notes', 'changed_at'
        ]
