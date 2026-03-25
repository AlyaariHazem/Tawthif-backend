from rest_framework import status, generics, permissions, viewsets
import random
import requests
import base64
from django.utils import timezone
from datetime import timedelta

from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import login, logout
from rest_framework_simplejwt.tokens import RefreshToken
from django.views.decorators.csrf import csrf_exempt

from drf_spectacular.utils import extend_schema, OpenApiResponse

from .models import User, JobSeekerProfile, EmployerProfile, ProfileDocument, DocumentView
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserSerializer,
    JobSeekerProfileSerializer, EmployerProfileSerializer,
    UserProfileUpdateSerializer, PasswordChangeSerializer, PhoneVerificationSerializer, ResendVerificationCodeSerializer,
    RequestPasswordResetSerializer, ResetPasswordConfirmSerializer,
    ProfileDocumentSerializer, ProfileDocumentCreateSerializer, ProfileDocumentUpdateSerializer,
    JobSeekerProfileWithDocumentsSerializer
)

# ✅ Helper function for consistent responses
def data_response(payload, status_code=status.HTTP_200_OK):
    return Response({"data": payload}, status=status_code)


@extend_schema(request=UserRegistrationSerializer, responses={201: UserSerializer})
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register(request):
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        # token, created = Token.objects.get_or_create(user=user)
        refresh = RefreshToken.for_user(user)
        return data_response({
            'message': 'تم إنشاء الحساب بنجاح. تم إرسال كود التحقق إلى رقم هاتفك',
            'user': UserSerializer(user).data,
            # 'token': token.key
            'token': str(refresh.access_token),
            'refresh': str(refresh),
        }, status.HTTP_201_CREATED)
    return data_response(serializer.errors, status.HTTP_400_BAD_REQUEST)


@extend_schema(request=PhoneVerificationSerializer, responses={200: OpenApiResponse(description="تم التحقق من الهاتف بنجاح")})
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def verify_phone(request):
    serializer = PhoneVerificationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        
        # تحديث حالة المستخدم
        user.is_verified = True
        user.verification_code = None 
        user.verification_code_expires_at = None
        user.save()
        
        return data_response({
            'message': 'تم التحقق من رقم الهاتف بنجاح',
            'user': UserSerializer(user).data
        })
    return data_response(serializer.errors, status.HTTP_400_BAD_REQUEST)



@extend_schema(request=ResendVerificationCodeSerializer, responses={200: OpenApiResponse(description="تم إعادة إرسال كود التحقق")})
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def resend_verification_code(request):
    serializer = ResendVerificationCodeSerializer(data=request.data)
    if serializer.is_valid():
        phone = serializer.validated_data['phone']
        user = User.objects.get(phone=phone)

        # توليد كود تحقق جديد
        verification_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        
        # إرسال الكود عبر SMS
        API_KEY = "CoGSk_vukOIiLflChcdMPM3dsuhW0c8kAvY1"
        PROJECT_ID = "PJafd415db960f868e"
        
        url = f"https://api.telerivet.com/v1/projects/{PROJECT_ID}/messages/send"
        auth_header = base64.b64encode(f"{API_KEY}:".encode()).decode()
        
        headers = {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/json"
        }
        
        message_content = f"""مرحبا بك في منصة توظيف
كود التحقق الخاص بك هو: {verification_code}"""
        
        data = {
            "to_number": phone,
            "content": message_content
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            response.raise_for_status()
            
            # حفظ الكود الجديد في قاعدة البيانات
            user.verification_code = verification_code
            user.verification_code_expires_at = timezone.now() + timedelta(minutes=10)
            user.save()
            
            return data_response({
                'message': 'تم إعادة إرسال كود التحقق إلى رقم هاتفك'
            })
        except Exception as e:
            return data_response({
                'error': 'حدث خطأ أثناء إرسال الرسالة. الرجاء المحاولة لاحقاً'
            }, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return data_response(serializer.errors, status.HTTP_400_BAD_REQUEST)


@extend_schema(request=UserLoginSerializer, responses={200: UserSerializer})
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_view(request):
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        # login(request, user)
        # token, created = Token.objects.get_or_create(user=user)
        # token, created = Token.objects.get_or_create(user=user)
        refresh = RefreshToken.for_user(user)
        response = data_response({
            'message': 'تم تسجيل الدخول بنجاح',
            'user': UserSerializer(user).data,
            # 'token': token.key
            'token': str(refresh.access_token),
            'refresh': str(refresh),
        })
        
        return response
    return data_response(serializer.errors, status.HTTP_400_BAD_REQUEST)

@csrf_exempt
@extend_schema(responses={200: OpenApiResponse(description="Logout successful")})
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    try:
        request.user.auth_token.delete()
    except:
        pass
    logout(request)
    return data_response({'message': 'تم تسجيل الخروج بنجاح'})


@extend_schema(responses={200: UserSerializer})
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def profile(request):
    user = request.user
    user_data = UserSerializer(user).data
    profile_data = None

    if user.user_type == 'job_seeker':
        profile, created = JobSeekerProfile.objects.get_or_create(user=user)
        # استخدام Serializer الجديد الذي يتضمن المرفقات
        profile_data = JobSeekerProfileWithDocumentsSerializer(profile, context={'request': request}).data

    elif user.user_type == 'employer':
        profile, created = EmployerProfile.objects.get_or_create(user=user, defaults={'company_name': ''})
        profile_data = EmployerProfileSerializer(profile).data

    return data_response({
        'user': user_data,
        'profile': profile_data
    })


@extend_schema(request=UserProfileUpdateSerializer, responses={200: UserSerializer})
@api_view(['PUT'])
@permission_classes([permissions.IsAuthenticated])
def update_profile(request):
    user = request.user
    old_phone = user.phone
    serializer = UserProfileUpdateSerializer(user, data=request.data, partial=True)

    if serializer.is_valid():
        new_phone = serializer.validated_data.get('phone')
        
        # Check if phone is being updated and is different
        if new_phone and new_phone != old_phone:
            # 1. Update the user (including new phone)
            user = serializer.save()
            
            # 2. Set as unverified
            user.is_verified = False
            user.save()
            
            # 3. Delete token (Logout)
            try:
                user.auth_token.delete()
            except:
                pass
            
            return data_response({
                'message': 'تم تحديث رقم الهاتف بنجاح. يجب عليك تسجيل الدخول والتحقق من الرقم الجديد.',
            })

        serializer.save()
        return data_response({
            'message': 'تم تحديث الملف الشخصي بنجاح',
            'user': UserSerializer(user).data
        })
    return data_response(serializer.errors, status.HTTP_400_BAD_REQUEST)


@extend_schema(request=JobSeekerProfileSerializer, responses={200: JobSeekerProfileSerializer})
@api_view(['PUT'])
@permission_classes([permissions.IsAuthenticated])
def update_job_seeker_profile(request):
    user = request.user
    if user.user_type != 'job_seeker':
        return data_response({'error': 'هذا الحساب ليس لباحث عن عمل'}, status.HTTP_403_FORBIDDEN)

    profile, created = JobSeekerProfile.objects.get_or_create(user=user)
    serializer = JobSeekerProfileSerializer(profile, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return data_response({
            'message': 'تم تحديث ملف الباحث عن عمل بنجاح',
            'profile': serializer.data
        })
    return data_response(serializer.errors, status.HTTP_400_BAD_REQUEST)

@extend_schema(request=EmployerProfileSerializer, responses={200: EmployerProfileSerializer})
@api_view(['PUT'])
@permission_classes([permissions.IsAuthenticated])
def update_employer_profile(request):
    user = request.user
    if user.user_type != 'employer':
        return data_response({'error': 'هذا الحساب ليس لصاحب عمل'}, status.HTTP_403_FORBIDDEN)

    profile, created = EmployerProfile.objects.get_or_create(user=user, defaults={'company_name': ''})
    serializer = EmployerProfileSerializer(profile, data=request.data, partial=True)

    if serializer.is_valid():
        serializer.save()
        return data_response({
            'message': 'تم تحديث ملف صاحب العمل بنجاح',
            'profile': serializer.data
        })
    return data_response(serializer.errors, status.HTTP_400_BAD_REQUEST)


@extend_schema(request=PasswordChangeSerializer, responses={
    200: OpenApiResponse(description="تم تغيير كلمة المرور بنجاح — new token returned"),
    400: OpenApiResponse(description="Validation error")
})
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def change_password(request):
    serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()

        try:
            user.auth_token.delete()
        except:
            pass
        token = Token.objects.create(user=user)

        return data_response({
            'message': 'تم تغيير كلمة المرور بنجاح',
            'token': token.key
        })
    return data_response(serializer.errors, status.HTTP_400_BAD_REQUEST)


class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]

    @extend_schema(responses=UserSerializer(many=True))
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return data_response(response.data)


class UserDetailView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses=UserSerializer)
    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return data_response(response.data)


def send_verification_sms_helper(phone, verification_code):
    API_KEY = "CoGSk_vukOIiLflChcdMPM3dsuhW0c8kAvY1"
    PROJECT_ID = "PJafd415db960f868e"
    
    url = f"https://api.telerivet.com/v1/projects/{PROJECT_ID}/messages/send"
    auth_header = base64.b64encode(f"{API_KEY}:".encode()).decode()
    
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/json"
    }
    
    message_content = f"""مرحبا بك في منصة توظيف
كود استعادة كلمة المرور الخاص بك هو: {verification_code}"""
    
    data = {
        "to_number": phone,
        "content": message_content
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Error sending SMS: {e}")
        return False


@extend_schema(request=RequestPasswordResetSerializer, responses={200: OpenApiResponse(description="تم إرسال كود التحقق")})
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def request_password_reset(request):
    serializer = RequestPasswordResetSerializer(data=request.data)
    if serializer.is_valid():
        phone = serializer.validated_data['phone']
        user = User.objects.get(phone=phone)
        
        verification_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        
        if send_verification_sms_helper(phone, verification_code):
            user.verification_code = verification_code
            user.verification_code_expires_at = timezone.now() + timedelta(minutes=10)
            user.save()
            
            return data_response({
                'message': 'تم إرسال كود التحقق لتغيير كلمة المرور إلى رقم هاتفك'
            })
        else:
            return data_response({
                'error': 'حدث خطأ أثناء إرسال الرسالة. الرجاء المحاولة لاحقاً'
            }, status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    return data_response(serializer.errors, status.HTTP_400_BAD_REQUEST)


@extend_schema(request=ResetPasswordConfirmSerializer, responses={200: OpenApiResponse(description="تم تغيير كلمة المرور بنجاح")})
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def confirm_password_reset(request):
    serializer = ResetPasswordConfirmSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        new_password = serializer.validated_data['new_password']
        
        user.set_password(new_password)
        user.verification_code = None
        user.verification_code_expires_at = None
        user.save()
        
        # Optional: Delete auth tokens
        try:
            user.auth_token.delete()
        except:
            pass
        
        # Create new token for auto-login
        token = Token.objects.create(user=user)

        return data_response({
            'message': 'تم تغيير كلمة المرور بنجاح',
            'token': token.key,
            'user': UserSerializer(user).data
        })
    return data_response(serializer.errors, status.HTTP_400_BAD_REQUEST)


# ==================== Profile Document Views ====================

class ProfileDocumentViewSet(viewsets.ModelViewSet):
    """ViewSet للباحثين عن عمل لإدارة وثائقهم"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # المستخدم يرى وثائقه فقط في هذا الـ ViewSet الخاص بالإدارة
        return ProfileDocument.objects.filter(job_seeker_profile__user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ProfileDocumentCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ProfileDocumentUpdateSerializer
        return ProfileDocumentSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return data_response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return data_response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return data_response({
                'message': 'تم رفع الوثيقة بنجاح',
                'document': serializer.data
            }, status.HTTP_201_CREATED)
        return data_response(serializer.errors, status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return data_response({
                'message': 'تم تحديث الوثيقة بنجاح',
                'document': serializer.data
            })
        return data_response(serializer.errors, status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return data_response({'message': 'تم حذف الوثيقة بنجاح'}, status.HTTP_204_NO_CONTENT)
