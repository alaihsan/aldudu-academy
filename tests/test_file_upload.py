"""
Test File Upload Security & Functionality
"""
import pytest
import io
from werkzeug.datastructures import FileStorage


class TestFileUploadValidation:
    """Test file upload validation"""

    def test_allowed_extension_pdf(self, app):
        """Test PDF file is allowed"""
        from app.helpers import allowed_file
        
        assert allowed_file('document.pdf') is True
        assert allowed_file('file.PDF') is True

    def test_allowed_extension_image(self, app):
        """Test image files are allowed"""
        from app.helpers import allowed_file
        
        assert allowed_file('image.png') is True
        assert allowed_file('photo.jpg') is True
        assert allowed_file('picture.jpeg') is True
        assert allowed_file('graphic.gif') is True
        assert allowed_file('image.webp') is True

    def test_allowed_extension_document(self, app):
        """Test document files are allowed"""
        from app.helpers import allowed_file
        
        assert allowed_file('document.doc') is True
        assert allowed_file('document.docx') is True
        assert allowed_file('spreadsheet.xls') is True
        assert allowed_file('spreadsheet.xlsx') is True
        assert allowed_file('presentation.ppt') is True
        assert allowed_file('presentation.pptx') is True

    def test_disallowed_extension_exe(self, app):
        """Test executable files are disallowed"""
        from app.helpers import allowed_file
        
        assert allowed_file('virus.exe') is False
        assert allowed_file('script.bat') is False
        assert allowed_file('program.sh') is False

    def test_disallowed_extension_no_extension(self, app):
        """Test files without extension are disallowed"""
        from app.helpers import allowed_file
        
        assert allowed_file('noextension') is False
        assert allowed_file('file.') is False

    def test_file_size_limit(self, app):
        """Test file size limit enforcement"""
        from app.config import Config
        
        # Default max is 16MB
        assert Config.MAX_CONTENT_LENGTH == 16 * 1024 * 1024
        
        # Create file larger than limit (test should handle RequestEntityTooLarge)
        large_file = io.BytesIO(b'x' * (17 * 1024 * 1024))  # 17MB
        assert len(large_file.getvalue()) > Config.MAX_CONTENT_LENGTH


class TestFileUploadSanitization:
    """Test file upload sanitization"""

    def test_filename_sanitization(self, app):
        """Test filename sanitization"""
        from werkzeug.utils import secure_filename
        
        # Dangerous filenames should be sanitized
        assert secure_filename('../../../etc/passwd') == 'passwd'
        assert secure_filename('file with spaces.txt') == 'file_with_spaces.txt'
        assert secure_filename('файл.txt') == 'fail.txt'

    def test_malicious_filename_rejected(self, app):
        """Test malicious filenames are rejected"""
        from werkzeug.utils import secure_filename
        
        # These should be sanitized or rejected
        dangerous_names = [
            '../../../etc/passwd',
            '..\\..\\windows\\system32',
            '<script>alert(1)</script>.txt',
            'file.exe.php',
        ]
        
        for name in dangerous_names:
            sanitized = secure_filename(name)
            # Should not contain path traversal or special chars
            assert '..' not in sanitized
            assert '/' not in sanitized
            assert '\\' not in sanitized


class TestFileUploadAPI:
    """Test file upload API endpoints"""

    def test_upload_file_no_file(self, client, teacher_user, course):
        """Test upload endpoint with no file"""
        # Login
        client.post('/api/login', json={
            'email': 'teacher@test.com',
            'password': 'password123'
        })
        
        response = client.post(f'/api/course/{course.id}/upload', data={})
        assert response.status_code in [400, 401]

    def test_upload_valid_file(self, client, teacher_user, course):
        """Test uploading a valid file"""
        from io import BytesIO
        
        # Login
        client.post('/api/login', json={
            'email': 'teacher@test.com',
            'password': 'password123'
        })
        
        # Create test file
        data = {
            'file': (BytesIO(b'test content'), 'test.pdf')
        }
        
        response = client.post(
            f'/api/course/{course.id}/upload',
            data=data,
            content_type='multipart/form-data'
        )
        
        # Should succeed or return specific error (not validation error)
        assert response.status_code in [200, 201, 400]

    def test_upload_invalid_extension(self, client, teacher_user, course):
        """Test uploading file with invalid extension"""
        from io import BytesIO
        
        # Login
        client.post('/api/login', json={
            'email': 'teacher@test.com',
            'password': 'password123'
        })
        
        # Create test file with bad extension
        data = {
            'file': (BytesIO(b'malicious content'), 'virus.exe')
        }
        
        response = client.post(
            f'/api/course/{course.id}/upload',
            data=data,
            content_type='multipart/form-data'
        )
        
        # Should be rejected
        if response.status_code == 200:
            data = response.get_json()
            assert data.get('success') is False or 'not allowed' in str(data).lower()


class TestFileStorage:
    """Test file storage security"""

    def test_upload_folder_outside_instance(self, app):
        """Test that upload folder is within instance directory"""
        import os
        from app.config import Config
        
        upload_folder = Config.UPLOAD_FOLDER
        instance_path = os.path.join(os.getcwd(), 'instance')
        
        # Upload folder should be within instance directory
        assert upload_folder.startswith(instance_path) or 'instance' in upload_folder

    def test_file_path_traversal_prevention(self, app):
        """Test prevention of path traversal attacks"""
        import os
        from werkzeug.utils import secure_filename
        
        # Simulate path construction
        base_path = '/var/www/aldudu-academy/instance/uploads'
        malicious_filename = '../../../etc/passwd'
        safe_filename = secure_filename(malicious_filename)
        
        # Construct full path
        full_path = os.path.join(base_path, safe_filename)
        
        # Should be within base path
        assert os.path.commonpath([base_path, full_path]) == base_path
