from django.shortcuts import render, redirect

from Customer.models import Project


def index(request):
    if request.method == 'GET':
        if 'message' in request.session:
            data = {'message': request.session['message'], 'status': request.session['status']}
            del request.session['message'], request.session['status']
            return render(request, 'Louisoft/index.html', data)

        return render(request, 'Louisoft/index.html')


def cv(request):
    return render(request, 'Louisoft/resumee.html')


def post_job(request):
    if request.method == 'GET':
        if 'message' in request.session:
            context = {'message': request.session['message'], 'status': request.session['status']}
            del request.session['message'], request.session['status']
            return render(request, 'Louisoft/post.html', context)
        else:
            return render(request, 'Louisoft/post.html')
    elif request.method == 'POST':
        try:
            Project.objects.get(project_name=request.POST['project_name'])
            request.session['message'] = 'The Project Proposal already exists'
            request.session['status'] = 'danger'
        except Project.DoesNotExist:
            project = Project()
            project.project_name = request.POST['project_name']
            project.project_desc = request.POST['project_desc']
            project.project_budget = request.POST['project_budget']
            project.client_name = request.POST['client_name']
            project.client_phone = request.POST['client_phone']
            project.client_email = request.POST['client_email']
            project.save()
            request.session['message'] = 'The Project Proposal has been posted.'
            request.session['status'] = 'success'
        return redirect('job_post')

