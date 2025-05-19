from rest_framework import serializers

class TableCreateSerializer(serializers.Serializer):
    Title = serializers.CharField()
    project = serializers.CharField()
    data = serializers.DictField()

class DataSubmitSerializer(serializers.Serializer):
    Title = serializers.CharField()
    data = serializers.ListField(child=serializers.DictField())

class TableStructureSerializer(serializers.Serializer):
    Title = serializers.CharField()
    project = serializers.CharField()
    data = serializers.DictField()

class ProcessDataSerializer(serializers.Serializer):
    Title = serializers.CharField()
    data = serializers.DictField(child=serializers.DictField())

class DataUpdateSerializer(serializers.Serializer):
    Title = serializers.CharField()
    data = serializers.DictField()