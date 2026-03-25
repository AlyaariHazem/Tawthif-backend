from rest_framework import serializers
from .models import Company, CompanyReview, CompanyFollower
from django.contrib.auth import get_user_model

User = get_user_model()


class CompanySerializer(serializers.ModelSerializer):
    total_jobs = serializers.ReadOnlyField()
    active_jobs = serializers.ReadOnlyField()
    is_following = serializers.SerializerMethodField()
    followers_count = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    
    class Meta:
        model = Company
        fields = [
            'id', 'name', 'slug', 'description', 'logo', 'cover_image',
            'website', 'email', 'phone', 'address', 'city', 'country',
            'size', 'industry', 'founded_year', 'employees_count',
            'is_verified', 'is_featured', 'total_jobs', 'active_jobs',
            'is_following', 'followers_count', 'average_rating', 'created_at'
        ]
        read_only_fields = ['slug', 'is_verified', 'is_featured', 'created_at']
    
    def get_is_following(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return CompanyFollower.objects.filter(user=request.user, company=obj).exists()
        return False
    
    def get_followers_count(self, obj):
        return obj.followers.count()
    
    def get_average_rating(self, obj):
        reviews = obj.reviews.filter(is_approved=True)
        if reviews.exists():
            return round(sum(review.rating for review in reviews) / reviews.count(), 1)
        return 0


class CompanyCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = [
            'name', 'description', 'logo', 'cover_image', 'website',
            'email', 'phone', 'address', 'city', 'country', 'size',
            'industry', 'founded_year', 'employees_count'
        ]
    
    
    def create(self, validated_data):
        from slugify import slugify
        request = self.context.get('request')
        validated_data['owner'] = request.user

        base_slug = slugify(validated_data['name'], lowercase=True)
        slug = base_slug
        counter = 1
        if Company.objects.filter(slug=slug,owner= request.user).exists():
            raise serializers.ValidationError("  هذه الشركة قد كررتها سابقا يرجى تغيير الاسم ")
       
        while Company.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        validated_data['slug'] = slug

        return super().create(validated_data)


class CompanyReviewSerializer(serializers.ModelSerializer):
    reviewer = serializers.StringRelatedField(read_only=True)
    reviewer_name = serializers.SerializerMethodField()
    
    class Meta:
        model = CompanyReview
        fields = [
            'id', 'rating', 'title', 'review_text', 'pros', 'cons',
            'is_current_employee', 'job_title', 'reviewer', 'reviewer_name',
            'created_at'
        ]
        read_only_fields = ['reviewer', 'is_approved', 'created_at']
    
    def get_reviewer_name(self, obj):
        return f"{obj.reviewer.first_name} {obj.reviewer.last_name}".strip() or obj.reviewer.username
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['reviewer'] = request.user
        return super().create(validated_data)


class CompanyFollowerSerializer(serializers.ModelSerializer):
    company = CompanySerializer(read_only=True)
    
    class Meta:
        model = CompanyFollower
        fields = ['id', 'company', 'followed_at']

