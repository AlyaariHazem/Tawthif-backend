from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, JobSeekerProfile, EmployerProfile, ProfileDocument, DocumentView
import re
# from drf_spectacular.utils import extend_schema_serializer, OpenApiSchema
# 
import random
import requests
import base64
from django.utils import timezone
from datetime import timedelta



class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    phone = serializers.CharField(required=True, allow_blank=False)
    
    class Meta:
        
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'password_confirm', 'user_type', 'phone']
    
    def validate(self, attrs):
        # first_name = validated_data.get('first_name', '')
        # last_name = validated_data.get('last_name', '')
        # validated_data['username'] = first_name+'_'+last_name if first_name and last_name else validated_data['username']

        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("كلمات المرور غير متطابقة")
        if User.objects.filter(phone=attrs['phone']).exists():
            raise serializers.ValidationError("رقم الهاتف هذا مستخدم بالفعل")

        return attrs
   
   
    def _generate_verification_code(self):
        """توليد كود تحقق عشوائي مكون من 6 أرقام"""
        return ''.join([str(random.randint(0, 9)) for _ in range(6)])
    
    
    
    def _send_verification_sms(self, phone_number, verification_code):
        """إرسال رسالة SMS تحتوي على كود التحقق"""
        API_KEY = "CoGSk_vukOIiLflChcdMPM3dsuhW0c8kAvY1"
        PROJECT_ID = "PJafd415db960f868e"
        
        url = f"https://api.telerivet.com/v1/projects/{PROJECT_ID}/messages/send"
        
        # Basic Auth (API_KEY:)
        auth_header = base64.b64encode(f"{API_KEY}:".encode()).decode()
        
        headers = {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/json"
        }
        
        message_content = f"""مرحبا بك في منصة توظيف
كود التحقق الخاص بك هو: {verification_code}"""
        
        data = {
            "to_number": phone_number,
            "content": message_content
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            response.raise_for_status()
            return True
        except Exception as e:
            # يمكن تسجيل الخطأ هنا
            print(f"خطأ في إرسال الرسالة: {str(e)}")
            return False
    
    def create(self, validated_data):
      
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        phone = validated_data.get('phone')
        
        # if phone  not in ['+967776137120','776137120','+967774931701','774931701','+967776644888','776644888','+967771974387','771974387','737165166']:
        #     raise serializers.ValidationError("يجب ان يكون تلفون حازم او قصي او عبد الكريم او منير او احد اعضاء الفريق") 
        
        verification_code = self._generate_verification_code()
        
        sms_sent = self._send_verification_sms(phone, verification_code)
        
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        
        user.verification_code = verification_code
        user.verification_code_expires_at = timezone.now() + timedelta(minutes=10)
        user.save()
       
        
        # Create profile based on user type
        if user.user_type == 'job_seeker':
            JobSeekerProfile.objects.create(user=user)
        elif user.user_type == 'employer':
            EmployerProfile.objects.create(user=user, company_name='')
        
        return user



class UserLoginSerializer(serializers.Serializer):
    phone = serializers.CharField(required=True, allow_blank=True)
    # email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField()

    def validate(self, attrs):
        phone = attrs.get('phone')
        # email = attrs.get('email')
        password = attrs.get('password')

        if not password:
            raise serializers.ValidationError("يجب إدخال كلمة المرور")

        user = None
        if phone:
            try:
                user_obj = User.objects.get(phone=phone)  
                username = user_obj.username
            except User.DoesNotExist:
                raise serializers.ValidationError("خطأ في اسم المستخدم  او كلمة المرور")
        # elif email:
        #     try:
        #         user_obj = User.objects.get(email=email)
        #         username = user_obj.username
        #     except User.DoesNotExist:
        #         raise serializers.ValidationError("البريد الإلكتروني غير صحيح")
        else:
            # أو البريد الإلكتروني
            raise serializers.ValidationError("يجب إدخال رقم الهاتف ")

        
        user = authenticate(username=username, password=password)
        if not user:
            raise serializers.ValidationError("خطأ في اسم المستخدم  او كلمة المرور")
        if not user.is_active:
            raise serializers.ValidationError("الحساب غير مفعل")
        
        if not user.is_verified:
            raise serializers.ValidationError("يجب التحقق من رقم الهاتف أولاً")

        attrs['user'] = user
        return attrs


class PhoneVerificationSerializer(serializers.Serializer):
    phone = serializers.CharField(required=True)
    verification_code = serializers.CharField(required=True, max_length=6, min_length=6)
    
    def validate(self, attrs):
        phone = attrs.get('phone')
        verification_code = attrs.get('verification_code')
        
        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            raise serializers.ValidationError("رقم الهاتف غير موجود")
        
        # التحقق من وجود كود التحقق
        if not user.verification_code:
            raise serializers.ValidationError("لم يتم إرسال كود تحقق لهذا الرقم")
        
        # التحقق من صلاحية الكود
        if user.verification_code_expires_at and timezone.now() > user.verification_code_expires_at:
            raise serializers.ValidationError("انتهت صلاحية كود التحقق. الرجاء طلب كود جديد")
        
        # التحقق من تطابق الكود
        if user.verification_code != verification_code:
            raise serializers.ValidationError("كود التحقق غير صحيح")
        
        attrs['user'] = user
        return attrs



class ResendVerificationCodeSerializer(serializers.Serializer):
    phone = serializers.CharField(required=True)
    
    def validate_phone(self, value):
        try:
            user = User.objects.get(phone=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("رقم الهاتف غير موجود")
        
        if user.is_verified:
            raise serializers.ValidationError("هذا الحساب متحقق منه بالفعل")
       
        # if value  not in ['+967776137120','776137120','+967774931701','774931701','+967776644888','776644888','+967771974387','771974387','737165166']:
        #     raise serializers.ValidationError("يجب ان يكون تلفون حازم او قصي او عبد الكريم او منير او احد اعضاء الفريق") 
        
        return value

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'user_type', 
                 'phone', 'date_of_birth', 'profile_picture', 'bio', 'location', 
                 'is_verified', 'created_at']
        read_only_fields = ['id', 'created_at', 'is_verified']
    
    # def get_profile_picture(self, obj):
    #     request = self.context.get('request')
    #     if obj.profile_picture:
    #         return request.build_absolute_uri(obj.profile_picture.url)
    #     return None

class JobSeekerProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = JobSeekerProfile
        fields = '__all__'


class EmployerProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = EmployerProfile
        fields = '__all__'


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'date_of_birth', 
                 'profile_picture', 'bio', 'location']


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    new_password_confirm = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("كلمات المرور الجديدة غير متطابقة")
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("كلمة المرور القديمة غير صحيحة")
        return value


class RequestPasswordResetSerializer(serializers.Serializer):
    phone = serializers.CharField(required=True)
    
    def validate_phone(self, value):
        if not User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("رقم الهاتف غير مسجل لدينا")
        return value


class ResetPasswordConfirmSerializer(serializers.Serializer):
    phone = serializers.CharField(required=True)
    verification_code = serializers.CharField(required=True, max_length=6, min_length=6)
    new_password = serializers.CharField(required=True, min_length=8)
    new_password_confirm = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("كلمات المرور غير متطابقة")
            
        try:
            user = User.objects.get(phone=attrs['phone'])
        except User.DoesNotExist:
             raise serializers.ValidationError("رقم الهاتف غير مسجل لدينا")
        
        # Verify code
        if not user.verification_code or user.verification_code != attrs['verification_code']:
            raise serializers.ValidationError("كود التحقق غير صحيح")
            
        if user.verification_code_expires_at and timezone.now() > user.verification_code_expires_at:
             raise serializers.ValidationError("انتهت صلاحية كود التحقق")
             
        attrs['user'] = user
        return attrs


# ==================== Profile Document Serializers ====================

class ProfileDocumentSerializer(serializers.ModelSerializer):
    """Serializer لعرض وإنشاء وثائق الملف الشخصي"""
    file_url = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()
    file_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ProfileDocument
        fields = [
            'id', 'document_type', 'title', 'description', 'file', 
            'file_url', 'file_size', 'file_name', 'issued_by', 'issue_date', 
            'visibility', 'views_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'views_count', 'created_at', 'updated_at']
    
    def get_file_url(self, obj):
        """الحصول على رابط الملف الكامل"""
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        elif obj.file:
            return obj.file.url
        return None
    
    def get_file_size(self, obj):
        """الحصول على حجم الملف بصيغة قابلة للقراءة"""
        if obj.file:
            try:
                size_bytes = obj.file.size
                if size_bytes < 1024:
                    return f"{size_bytes} B"
                elif size_bytes < 1024 * 1024:
                    return f"{size_bytes / 1024:.2f} KB"
                else:
                    return f"{size_bytes / (1024 * 1024):.2f} MB"
            except (FileNotFoundError, ValueError):
                return "غير متوفر"
        return None
    
    def get_file_name(self, obj):
        """الحصول على اسم الملف"""
        if obj.file:
            return obj.file.name.split('/')[-1]
        return None
    
    def validate_file(self, value):
        """التحقق من حجم الملف"""
        max_size = 10 * 1024 * 1024  # 10 MB
        if value.size > max_size:
            raise serializers.ValidationError("حجم الملف يجب أن لا يتجاوز 10 ميجابايت")
        return value


class ProfileDocumentCreateSerializer(serializers.ModelSerializer):
    """Serializer لإنشاء وثيقة جديدة"""
    
    class Meta:
        model = ProfileDocument
        fields = [
            'document_type', 'title', 'description', 'file',
            'issued_by', 'issue_date', 'visibility'
        ]
    
    def validate_file(self, value):
        """التحقق من حجم الملف"""
        max_size = 10 * 1024 * 1024  # 10 MB
        if value.size > max_size:
            raise serializers.ValidationError("حجم الملف يجب أن لا يتجاوز 10 ميجابايت")
        return value
    
    def create(self, validated_data):
        """إنشاء وثيقة جديدة مرتبطة بالمستخدم الحالي"""
        request = self.context.get('request')
        user = request.user
        
        # التأكد من أن المستخدم لديه ملف باحث عن عمل
        if not hasattr(user, 'job_seeker_profile'):
            raise serializers.ValidationError("يجب أن يكون لديك ملف باحث عن عمل لإضافة وثائق")
        
        validated_data['job_seeker_profile'] = user.job_seeker_profile
        return super().create(validated_data)


class ProfileDocumentUpdateSerializer(serializers.ModelSerializer):
    """Serializer لتحديث وثيقة موجودة"""
    
    class Meta:
        model = ProfileDocument
        fields = [
            'document_type', 'title', 'description', 'file',
            'issued_by', 'issue_date', 'visibility'
        ]
    
    def validate_file(self, value):
        """التحقق من حجم الملف"""
        if value:
            max_size = 10 * 1024 * 1024  # 10 MB
            if value.size > max_size:
                raise serializers.ValidationError("حجم الملف يجب أن لا يتجاوز 10 ميجابايت")
        return value


class DocumentViewSerializer(serializers.ModelSerializer):
    """Serializer لعرض سجلات المشاهدات"""
    viewer_name = serializers.CharField(source='viewer.username', read_only=True)
    document_title = serializers.CharField(source='document.title', read_only=True)
    
    class Meta:
        model = DocumentView
        fields = ['id', 'document', 'document_title', 'viewer', 'viewer_name', 'application', 'viewed_at']
        read_only_fields = ['id', 'viewed_at']


class JobSeekerProfileWithDocumentsSerializer(serializers.ModelSerializer):
    """Serializer لملف الباحث عن عمل مع المرفقات"""
    user = UserSerializer(read_only=True)
    documents = serializers.SerializerMethodField()
    documents_count = serializers.SerializerMethodField()
    
    class Meta:
        model = JobSeekerProfile
        fields = '__all__'
    
    def get_documents(self, obj):
        """الحصول على المرفقات المرئية"""
        request = self.context.get('request')
        
        # إذا كان المستخدم الحالي هو صاحب الملف، عرض جميع المرفقات
        if request and request.user == obj.user:
            documents = obj.documents.all()
        else:
            # عرض المرفقات العامة فقط للآخرين
            documents = obj.documents.filter(visibility__in=['public', 'employers_only'])
        
        return ProfileDocumentSerializer(documents, many=True, context=self.context).data
    
    def get_documents_count(self, obj):
        """عدد المرفقات"""
        request = self.context.get('request')
        
        if request and request.user == obj.user:
            return obj.documents.count()
        else:
            return obj.documents.filter(visibility__in=['public', 'employers_only']).count()
