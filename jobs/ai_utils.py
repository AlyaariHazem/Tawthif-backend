from google import genai
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def generate_job_summary(job_title, description, requirements=None, benefits=None, experience=None, salary=None):
    """
    Generates an AI summary for a job using the new Google GenAI API.
    """
    api_key = getattr(settings, 'GEMINI_API_KEY', None)
    if not api_key or api_key == 'your-gemini-api-key-here':
        logger.warning("Gemini API key is not configured.")
        return None

    try:
        client = genai.Client(api_key=api_key)
        
        prompt = f"""
        قم بتلخيص وصف الوظيفة التالي بأسلوب جذاب واحترافي باللغة العربية.
        
        عنوان الوظيفة: {job_title}
        الوصف: {description}
        المتطلبات: {requirements or 'غير محدد'}
        المزايا: {benefits or 'غير محدد'}
        الخبرة المطلوبة: {experience or 'غير محدد'}
        الراتب المتوقع: {salary or 'غير محدد'}
        
        يجب أن يكون التلخيص بتنسيق جذاب ومختصر (فقرة واحدة قصيرة تليها نقاط أساسية).
        
        تعليمات هامة:
        1. استخدم اللغة العربية الفصحى وبأسلوب مهني وجذاب.
        2. لا تدرج أي مقدمات أو عبارات ترحيبية أو ختامية (مثل: "بالتأكيد"، "إليك التلخيص"، "أتمنى أن يكون مفيداً").
        3. التزم بالتنسيق التالي بدقة:
        
        مثال للتنسيق المطلوب:
         هل أنت مستعد للتميز في دور [عنوان الوظيفة] مع [اسم الشركة/نوعها]؟ نبحث عن شخص متمكن للمساهمة في [أهم المهام]، ضمن بيئة عمل [ميزة بيئة العمل].
        - [معلومة هامة للمتقدمين]
        - [نطاق الراتب أو المزايا المالية]
        - [سنوات الخبرة المطلوبة]
        
        ملاحظة: اجعل التلخيص عاماً ومناسباً لطبيعة الوظيفة (سواء كانت تقنية، إدارية، قيادية، أو غيرها).
        """
        
        # In some cases, gemini-1.5-flash might need a different identifier or version
        # We will try the most common ones.
        try:
            response = client.models.generate_content(
                model='models/gemini-2.5-flash',
                contents=prompt
            )
        except Exception as e:
            if "404" in str(e):
                logger.warning(f"gemini-1.5-flash not found, trying gemini-1.5-flash-latest: {str(e)}")
                response = client.models.generate_content(
                    model='models/gemini-1.5-flash-latest',
                    contents=prompt
                )
            else:
                raise e
        
        if response and response.text:
            return response.text.strip()
        return None
    except Exception as e:
        logger.error(f"Error generating AI summary: {str(e)}")
        return None