from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, UserChangeForm, SetPasswordForm
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import UserProfile
import re


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        max_length=254,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Usuário',
            'autofocus': True
        })
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Senha'
        })
    )

    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )


# ============================================
# FORMS DE GERENCIAMENTO DE USUÁRIOS
# ============================================

class UserCreateForm(UserCreationForm):
    """Form para criação de usuário com perfil"""

    # Campos do User
    first_name = forms.CharField(
        label='Nome',
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome'})
    )
    last_name = forms.CharField(
        label='Sobrenome',
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sobrenome'})
    )
    email = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@exemplo.com'})
    )

    # Campos do UserProfile
    role = forms.ChoiceField(
        label='Perfil',
        choices=UserProfile.ROLES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    phone = forms.CharField(
        label='Telefone',
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(21) 99999-9999'})
    )
    department = forms.CharField(
        label='Departamento',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Departamento'})
    )
    cargo = forms.CharField(
        label='Cargo',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cargo'})
    )
    notes = forms.CharField(
        label='Observações',
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Observações...'})
    )
    must_change_password = forms.BooleanField(
        label='Exigir troca de senha no primeiro login',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome de usuário'}),
        }

    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop('request_user', None)
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Senha'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirmar senha'})

        # Admin não pode criar superadmin
        if self.request_user and hasattr(self.request_user, 'profile'):
            if self.request_user.profile.role != 'superadmin':
                self.fields['role'].choices = [
                    (k, v) for k, v in UserProfile.ROLES if k != 'superadmin'
                ]

    def clean_password1(self):
        """Validar senha forte"""
        password = self.cleaned_data.get('password1')

        if len(password) < 8:
            raise ValidationError('Senha deve ter no mínimo 8 caracteres')

        if not re.search(r'[A-Z]', password):
            raise ValidationError('Senha deve conter ao menos uma letra maiúscula')

        if not re.search(r'[a-z]', password):
            raise ValidationError('Senha deve conter ao menos uma letra minúscula')

        if not re.search(r'[0-9]', password):
            raise ValidationError('Senha deve conter ao menos um número')

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError('Senha deve conter ao menos um caractere especial (!@#$%^&*...)')

        return password

    def clean_email(self):
        """Verificar se email já existe"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Este e-mail já está cadastrado')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']

        if commit:
            user.save()
            # Criar ou atualizar profile
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.role = self.cleaned_data['role']
            profile.phone = self.cleaned_data.get('phone', '')
            profile.department = self.cleaned_data.get('department', '')
            profile.cargo = self.cleaned_data.get('cargo', '')
            profile.notes = self.cleaned_data.get('notes', '')
            profile.must_change_password = self.cleaned_data.get('must_change_password', True)
            if self.request_user:
                profile.created_by = self.request_user
            profile.save()

        return user


class UserEditForm(forms.ModelForm):
    """Form para edição de usuário"""

    # Campos do User
    first_name = forms.CharField(
        label='Nome',
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        label='Sobrenome',
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    is_active = forms.BooleanField(
        label='Usuário ativo',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    # Campos do UserProfile
    role = forms.ChoiceField(
        label='Perfil',
        choices=UserProfile.ROLES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    phone = forms.CharField(
        label='Telefone',
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    department = forms.CharField(
        label='Departamento',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    cargo = forms.CharField(
        label='Cargo',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    notes = forms.CharField(
        label='Observações',
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop('request_user', None)
        super().__init__(*args, **kwargs)

        # Carregar dados do profile
        if self.instance and hasattr(self.instance, 'profile'):
            profile = self.instance.profile
            self.fields['role'].initial = profile.role
            self.fields['phone'].initial = profile.phone
            self.fields['department'].initial = profile.department
            self.fields['cargo'].initial = profile.cargo
            self.fields['notes'].initial = profile.notes

        # Admin não pode editar para superadmin
        if self.request_user and hasattr(self.request_user, 'profile'):
            if self.request_user.profile.role != 'superadmin':
                self.fields['role'].choices = [
                    (k, v) for k, v in UserProfile.ROLES if k != 'superadmin'
                ]

    def clean_email(self):
        """Verificar se email já existe (exceto o próprio usuário)"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError('Este e-mail já está cadastrado')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']

        if commit:
            user.save()
            # Atualizar profile
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.role = self.cleaned_data['role']
            profile.phone = self.cleaned_data.get('phone', '')
            profile.department = self.cleaned_data.get('department', '')
            profile.cargo = self.cleaned_data.get('cargo', '')
            profile.notes = self.cleaned_data.get('notes', '')
            profile.save()

        return user


class PasswordChangeForm(SetPasswordForm):
    """Form para alteração de senha"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Nova senha'
        })
        self.fields['new_password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirmar nova senha'
        })

    def clean_new_password1(self):
        """Validar senha forte"""
        password = self.cleaned_data.get('new_password1')

        if len(password) < 8:
            raise ValidationError('Senha deve ter no mínimo 8 caracteres')

        if not re.search(r'[A-Z]', password):
            raise ValidationError('Senha deve conter ao menos uma letra maiúscula')

        if not re.search(r'[a-z]', password):
            raise ValidationError('Senha deve conter ao menos uma letra minúscula')

        if not re.search(r'[0-9]', password):
            raise ValidationError('Senha deve conter ao menos um número')

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError('Senha deve conter ao menos um caractere especial')

        return password


class PasswordResetByAdminForm(forms.Form):
    """Form para admin resetar senha de usuário"""

    new_password1 = forms.CharField(
        label='Nova senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Nova senha'})
    )
    new_password2 = forms.CharField(
        label='Confirmar senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirmar senha'})
    )
    must_change_password = forms.BooleanField(
        label='Exigir troca de senha no próximo login',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def clean_new_password1(self):
        """Validar senha forte"""
        password = self.cleaned_data.get('new_password1')

        if len(password) < 8:
            raise ValidationError('Senha deve ter no mínimo 8 caracteres')

        if not re.search(r'[A-Z]', password):
            raise ValidationError('Senha deve conter ao menos uma letra maiúscula')

        if not re.search(r'[a-z]', password):
            raise ValidationError('Senha deve conter ao menos uma letra minúscula')

        if not re.search(r'[0-9]', password):
            raise ValidationError('Senha deve conter ao menos um número')

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError('Senha deve conter ao menos um caractere especial')

        return password

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')

        if password1 and password2 and password1 != password2:
            raise ValidationError('As senhas não coincidem')

        return cleaned_data