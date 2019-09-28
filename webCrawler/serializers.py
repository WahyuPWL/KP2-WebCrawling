from rest_framework import serializers
from .models import *

class paperSerializer(serializers.ModelSerializer):

    class Meta:
        model = paper
        fields = '__all__'
