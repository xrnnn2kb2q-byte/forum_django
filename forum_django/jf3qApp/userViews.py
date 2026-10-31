from django.http import JsonResponse
from jf3qApp.models import Users
from jf3qApp.utils import md5Util
from django.forms.models import model_to_dict


def login(request):
    phone = request.POST.get('phone')
    upass = md5Util.calc_md5(request.POST.get('upass'))
    lu = Users.objects.filter(phone=phone, upass=upass).first()
    if lu:
        if lu.state != '1':
            data = {'status':0,'msg':'Account is not available(' + lu.msg + ')'}
            return JsonResponse(data)
        lu_dict = model_to_dict(lu)
        data = {'status':1,'msg':'Login Success','obj':lu_dict}
        return JsonResponse(data)
    else:
        data = {'status':0,'msg':'Account or password is incorrect'}
        return JsonResponse(data)