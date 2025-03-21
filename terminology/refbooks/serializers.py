from rest_framework import serializers
from .models import Refbook, RefbookItem


class RefbookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Refbook
        fields = ['id', 'code', 'name']


class RefbookItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = RefbookItem
        fields = ['code', 'value']