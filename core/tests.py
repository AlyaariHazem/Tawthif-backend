from django.test import TestCase
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from core.validators import validate_image_extension, validate_document_extension

class ValidatorTests(TestCase):
    def test_image_validator_valid(self):
        file = SimpleUploadedFile("test.png", b"file_content", content_type="image/png")
        try:
            validate_image_extension(file)
        except ValidationError:
            self.fail("validate_image_extension failed on valid png")

    def test_image_validator_invalid(self):
        file = SimpleUploadedFile("test.pdf", b"file_content", content_type="application/pdf")
        with self.assertRaises(ValidationError):
            validate_image_extension(file)

    def test_document_validator_valid(self):
        file = SimpleUploadedFile("test.pdf", b"file_content", content_type="application/pdf")
        try:
            validate_document_extension(file)
        except ValidationError:
            self.fail("validate_document_extension failed on valid pdf")

    def test_document_validator_invalid(self):
        file = SimpleUploadedFile("test.png", b"file_content", content_type="image/png")
        with self.assertRaises(ValidationError):
            validate_document_extension(file)
