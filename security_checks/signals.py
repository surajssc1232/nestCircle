from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Avg
from django.apps import apps # Import apps

# Removed direct model imports from here:
# from products.models import Product, Category 

@receiver(post_save, sender='products.Product') # Ensure sender is 'products.Product' (capital P)
def check_product_for_fraud(sender, instance, created, **kwargs):
    """
    Signal handler to perform basic fraud checks on product creation/update.
    """
    Product = apps.get_model('products', 'Product') # Get model dynamically
    # Category = apps.get_model('products', 'Category') # Get Category dynamically if needed for direct use

    flag_updated = False
    original_fraud_reason = instance.fraud_detection_reason if instance.fraud_detection_reason else ""

    # Basic Price Check: Flag if price is significantly lower than category average
    if instance.category: # instance.category is already a Category object or its ID
        try:
            category_avg_price = Product.objects.filter(
                category=instance.category,
                approved=True,
                is_flagged_fraud=False
            ).exclude(id=instance.id).aggregate(Avg('price'))['price__avg']

            if category_avg_price is not None and instance.price is not None:
                if instance.price < (category_avg_price * 0.3): 
                    if not instance.is_flagged_fraud or "Price significantly lower" not in original_fraud_reason:
                        instance.is_flagged_fraud = True
                        new_reason = "Price significantly lower than category average."
                        instance.fraud_detection_reason = f"{original_fraud_reason} {new_reason}".strip()
                        flag_updated = True
                        print(f"Product {instance.name} flagged for potential low price fraud.")
            elif instance.price is not None and instance.price < 50: 
                if not instance.is_flagged_fraud or "Price very low" not in original_fraud_reason:
                    instance.is_flagged_fraud = True
                    new_reason = "Price very low (no category average available or product price is zero)."
                    instance.fraud_detection_reason = f"{original_fraud_reason} {new_reason}".strip()
                    flag_updated = True
                    print(f"Product {instance.name} flagged for very low price.")

        except Exception as e:
            print(f"Error during price check for product {instance.name}: {e}")

    # Basic Keyword Check in description
    suspicious_keywords = ["free money", "guaranteed profit", "nigerian prince", "lottery win", "urgent transfer"]
    if instance.description:
        for keyword in suspicious_keywords:
            if keyword.lower() in instance.description.lower():
                if not instance.is_flagged_fraud or f"Contains suspicious keyword: {keyword}" not in original_fraud_reason:
                    instance.is_flagged_fraud = True
                    new_reason = f"Contains suspicious keyword: {keyword}."
                    instance.fraud_detection_reason = f"{original_fraud_reason} {new_reason}".strip()
                    flag_updated = True
                    print(f"Product {instance.name} flagged for suspicious keyword: {keyword}")
                    break 

    if flag_updated:
        Product.objects.filter(pk=instance.pk).update(
            is_flagged_fraud=instance.is_flagged_fraud,
            fraud_detection_reason=instance.fraud_detection_reason
        )
