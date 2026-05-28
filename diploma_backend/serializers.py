import re

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    displayName = serializers.CharField(write_only=True, max_length=150, trim_whitespace=True)

    def validate_email(self, value):
        normalized_email = value.strip().lower()

        if User.objects.filter(email__iexact=normalized_email).exists():
            raise serializers.ValidationError('A user with this email already exists.')

        return normalized_email

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate_displayName(self, value):
        cleaned_value = value.strip()
        if not cleaned_value:
            raise serializers.ValidationError('displayName is required.')
        return cleaned_value

    def create(self, validated_data):
        email = validated_data['email']
        password = validated_data['password']
        display_name = validated_data['displayName']

        username = self._build_unique_username(email)

        user = User(
            username=username,
            email=email,
            first_name=display_name,
        )
        user.set_password(password)
        user.save()

        return user

    def to_representation(self, instance):
        return {
            'id': instance.id,
            'email': instance.email,
            'displayName': instance.first_name,
        }

    def _build_unique_username(self, email):
        if len(email) <= 150 and not User.objects.filter(username__iexact=email).exists():
            return email

        base_username = email.split('@', 1)[0]
        base_username = re.sub(r'[^a-zA-Z0-9._-]', '', base_username).strip('._-').lower()
        if not base_username:
            base_username = 'user'

        candidate = base_username[:150]
        suffix = 1

        while User.objects.filter(username=candidate).exists():
            suffix_text = f'-{suffix}'
            candidate = f"{base_username[:150 - len(suffix_text)]}{suffix_text}"
            suffix += 1

        return candidate


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        email = attrs.get('email', '').strip().lower()
        password = attrs.get('password', '')

        user = User.objects.filter(email__iexact=email).first()

        if user is None or not user.is_active or not user.check_password(password):
            raise AuthenticationFailed('No active account found with the given credentials.')

        refresh = self.get_token(user)

        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }