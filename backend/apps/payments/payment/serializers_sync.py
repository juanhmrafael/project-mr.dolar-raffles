from rest_framework import serializers

class PaymentMethodLightSerializer(serializers.Serializer):
    """
    Serializer ligero para listar métodos de pago en un select.
    Expone solo los datos mínimos necesarios para la UI.
    """
    id = serializers.IntegerField()
    name = serializers.CharField()
    method_type = serializers.CharField()
