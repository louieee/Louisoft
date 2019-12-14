from django.shortcuts import render


def index(request):
    return render(request, '../templates/Louisoft/index.html')


def cv(request):
    return render(request, '../templates/Louisoft/resumee.html')
