from django.shortcuts import render


def index(request):
    if request.method == 'GET':
        if 'message' in request.session:
            data = {'message': request.session['message'], 'status': request.session['status']}
            del request.session['message'], request.session['status']
            return render(request, 'Louisoft/index.html', data)

        return render(request, 'Louisoft/index.html')


def cv(request):
    return render(request, 'Louisoft/resumee.html')
