from rest_framework import serializers
from .models import JobForm, JobFormQuestion

class JobFormQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobFormQuestion
        fields = ['id', 'label', 'help_text', 'question_type', 'required', 'options', 'order']

class JobFormSerializer(serializers.ModelSerializer):
    questions = JobFormQuestionSerializer(many=True, required=False)
    questions_count = serializers.IntegerField(source='questions.count', read_only=True)

    class Meta:
        model = JobForm
        fields = ['id', 'company', 'name', 'description', 'is_active', 'questions', 'questions_count', 'created_at']
        extra_kwargs = {
            'company': {'required': False}
        }

    def create(self, validated_data):
        questions_data = validated_data.pop('questions', [])
        # Company is set in the view's perform_create
        form = JobForm.objects.create(**validated_data)
        
        for question_data in questions_data:
            JobFormQuestion.objects.create(form=form, **question_data)
            
        return form

    def update(self, instance, validated_data):
        questions_data = validated_data.pop('questions', None)
        
        # Standard fields update
        instance.name = validated_data.get('name', instance.name)
        instance.description = validated_data.get('description', instance.description)
        instance.is_active = validated_data.get('is_active', instance.is_active)
        instance.save()

        # Update questions if provided (Strategy: Delete old and create new for simplicity, 
        # or more complex sync logic if needed. Let's do a simple sync for now)
        if questions_data is not None:
            # Simple approach: clear and replace
            instance.questions.all().delete()
            for question_data in questions_data:
                JobFormQuestion.objects.create(form=instance, **question_data)

        return instance
