from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Group, Product, Lesson, Permissions


class GetAccessToUser(View):
    def post(self, request, product_id):
        product = get_object_or_404(Product, pk=product_id)

        if product.start_date > timezone.now():
            groups = Group.objects.order_by('min_users').prefetch_related("Users")
            group_to_add = None
            for group in groups:
                if group.users.count() < group.max_users:
                    group_to_add = group
                    break

            group_to_add.users.add(request.user)
            permission = Permissions.objects.create(product=product, user=request.user)
            permission.save()
        else:
            groups = Group.objects.filter(product=product).prefetch_related("Users")
            group_to_add = None
            for group in groups:
                if group.users.count() < group.max_users:
                    group_to_add = group
                    break
            group_to_add.users.add(request.user)
            permission = Permissions.objects.create(product=product, user=request.user)
            permission.save()

        return JsonResponse({'message': 'Пользователь добален в группу'})


class ProductsListAPIView(APIView):
    def get(self, request):
        products = Product.objects.all()
        products_data = []
        for product in products:
            lessons_count = Lesson.objects.filter(product=product).count()
            products_data.append({
                'name': product.name,
                'start_date': product.start_date,
                'price': product.price,
                'lessons_count': lessons_count,
            })
        return Response(products_data)


class ProductLessonsAPIView(APIView):
    def get(self, request, product_id):
        product = get_object_or_404(Product, pk=product_id)
        user = request.user
        if user.is_authenticated:
            if Permissions.objects.filter(product=product, user=user).exists():
                lessons = Lesson.objects.filter(product=product)
                lessons_data = [{
                    'title': lesson.title,
                    'video_link': lesson.video_link,
                } for lesson in lessons]
                return Response(lessons_data)
            else:
                return Response({'message': 'У вас нет доступа к курсу'}, status=403)
        else:
            return Response({'message': 'Вы не авторизованы'}, status=401)