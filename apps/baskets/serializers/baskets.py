# from django.core.exceptions import ValidationError
# from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.baskets.models import Basket, BasketProduct
from apps.users.models import CustomUser

from .basketproducts import BasketProductReadSerializer, BasketProductWriteSerializer

# User = get_user_model()


class BasketReadSerializer(serializers.ModelSerializer):
    """Сериализатор модели Basket. Используется при чтении корзины.

    Для вычисления значения basket_products происходит обращение к данным
    промежуточной модели.

    """

    # TODO: заменить на кастомный сериализатор пользователя
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    basket_products = BasketProductReadSerializer(read_only=True, many=True, source="basket")

    class Meta:
        model = Basket
        fields = ("id", "user", "basket_products")


class BasketWriteSerializer(serializers.ModelSerializer):
    """Сериализатор модели Basket.

    Используется для добавления товаров в корзину.
    """

    # TODO: заменить на кастомный сериализатор пользователя
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    basket_products = BasketProductWriteSerializer(many=True)

    class Meta:
        model = Basket
        fields = "__all__"

    def validate(self, data):
        basket_products = data.get("basket_products", [])
        if basket_products:
            product_id = basket_products[0]["id"]
            self.validate_products(product_id)
        return data

    def validate_products(self, product_id):
        user = CustomUser.objects.get(id=1)
        basket_products = BasketProduct.objects.filter(basket__user=user)
        product_ids = set(basket_products.values_list("product_id", flat=True))

        if product_id in product_ids:
            raise serializers.ValidationError("Product already exists in the basket.")

    def create_or_update_basket(self, user, instance=None):
        user = CustomUser.objects.get(id=1)
        if instance:
            return instance
        basket, created = Basket.objects.get_or_create(user=user)
        return basket

    def create_products_quantity(self, basket_products, basket):
        for product in basket_products:
            BasketProduct.objects.create(
                basket=basket, product_id=product["id"], quantity=product["quantity"]
            )

    def create(self, validated_data):
        basket_products = validated_data.pop("basket_products")
        basket = self.create_or_update_basket(validated_data)
        self.create_products_quantity(basket_products, basket)
        return basket

    def update(self, instance, validated_data):
        basket_products = validated_data.pop("basket_products")
        self.create_products_quantity(basket_products, instance)
        return instance

    def to_representation(self, basket):
        representation = BasketReadSerializer(
            basket, context={"request": self.context.get("request")}
        )
        return representation.data
