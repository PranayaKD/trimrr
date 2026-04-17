import razorpay
from django.conf import settings
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from payments.models import PaymentTransaction
from core.tasks import send_welcome_email_task # let's send an upgrade email.

# Initialize razorpay client safely
client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)) if settings.RAZORPAY_KEY_ID else None

@login_required
def create_checkout_session(request):
    """View to initialize razorpay modal for the Pro Plan upgrade."""
    if not client:
        messages.error(request, "Payments are not configured on this server.")
        return redirect('pricing')

    # Trimrr Pro Plan is 399/yr
    amount_inr = 399
    amount_paise = amount_inr * 100 
    
    # Create Razorpay Order
    data = {
        "amount": amount_paise,
        "currency": "INR",
        "receipt": f"receipt_pro_{request.user.id}",
        "payment_capture": "1" # auto capture
    }
    
    try:
        razorpay_order = client.order.create(data=data)
        
        # Keep a track in DB
        PaymentTransaction.objects.create(
            user=request.user,
            razorpay_order_id=razorpay_order['id'],
            amount=amount_inr,
            status='created'
        )
        
        context = {
            'razorpay_order_id': razorpay_order['id'],
            'razorpay_key_id': settings.RAZORPAY_KEY_ID,
            'razorpay_amount': amount_paise,
            'user': request.user,
        }
        return render(request, 'payments/checkout.html', context)
        
    except Exception as e:
        messages.error(request, f"Could not initiate payment: {str(e)}")
        return redirect('pricing')

@csrf_exempt
def razorpay_callback(request):
    """Webhook / Form Callback for razorpay."""
    if request.method == "POST":
        payment_id = request.POST.get('razorpay_payment_id', '')
        order_id = request.POST.get('razorpay_order_id', '')
        signature = request.POST.get('razorpay_signature', '')
        
        try:
            # First, check if transaction exists
            transaction = PaymentTransaction.objects.get(razorpay_order_id=order_id)
            
            # Verify signature
            params_dict = {
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }
            client.utility.verify_payment_signature(params_dict)
            
            # If successful, upgrade the subscription.
            transaction.razorpay_payment_id = payment_id
            transaction.razorpay_signature = signature
            transaction.status = 'paid'
            transaction.save()
            
            # Access user and upgrade their subscription
            subscription = transaction.user.subscription
            subscription.activate_pro()
            
            # Success logic
            messages.success(request, f"Payment successful! Welcome to the Pro tier, {transaction.user.username}.")
            return redirect('dashboard')
            
        except razorpay.errors.SignatureVerificationError:
            messages.error(request, "Payment verification failed. If money was deducted, it will be refunded.")
            if 'transaction' in locals():
                transaction.status = 'failed'
                transaction.save()
            return redirect('pricing')
            
        except PaymentTransaction.DoesNotExist:
            messages.error(request, "Invalid order context returned.")
            return redirect('pricing')
            
    return redirect('home')
