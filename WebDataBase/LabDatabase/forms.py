from django import forms
# from .models import UploadedFile

class FileUploadForm(forms.ModelForm):
    class Meta:
        model = UploadedFile
        fields = ['title', 'file', 'description']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '输入文件标题'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '输入文件描述（可选）'
            }),
        }
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # 文件大小限制（10MB）
            max_size = 10 * 1024 * 1024
            if file.size > max_size:
                raise forms.ValidationError(f"文件大小不能超过 {max_size//1024//1024}MB")
            
            # 文件类型限制
            allowed_types = [
                'application/pdf',
                'image/jpeg', 
                'image/png',
                'application/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'application/vnd.ms-excel',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'text/plain'
            ]
            if file.content_type not in allowed_types:
                raise forms.ValidationError("不支持的文件类型")
        
        return file