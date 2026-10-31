from django.core import serializers
from django.http import JsonResponse
from jf3qApp.models import Users
from jf3qApp.utils import md5Util, pageUtil, dateUtil
from django.forms.models import model_to_dict

class UsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = '__all__'


def login(request):
    # get the phone number and upass from user input
    phone = request.POST.get('phone')
    # pwd hashed
    upass = md5Util.calc_md5(request.POST.get('upass'))
    # find user
    lu = Users.objects.filter(phone=phone, upass=upass).first()
    if lu:
        # 1 is available user 0 is deleted user
        if lu.state != '1':
            data = {'status':0,'msg':'Account is not available(' + lu.msg + ')'}
            return JsonResponse(data)
        # orm object to dict
        lu_dict = model_to_dict(lu)
        data = {'status':1,'msg':'Login Success','obj':lu_dict}
        return JsonResponse(data)
    # user not exist or pwd not correct
    else:
        data = {'status':0,'msg':'Account or password is incorrect'}
        return JsonResponse(data)

def page(request):
    query_data = {}
    pageNo = request.POST.get('pageNo')
    pageSize = request.POST.get('pageSize')
    nickname = request.POST.get('nickname')
    phone = request.POST.get('phone')
    state = request.POST.get('state')
    if nickname:
        # like search
        query_data['nickname__icontains'] = nickname
    # precise search
    if phone:
        query_data['phone'] = phone
    if state:
        query_data['state'] = state
    all = Users.objects.filter(**query_data).all().order_by('-id')
    page_info = pageUtil.get_page(all,page_no=pageNo,page_size=pageSize)
    serializer = UsersSerializer(page_info['list'],many=True)
    page_info['list'] = serializer.data
    data = ({'status':1,'msg':'search success', 'obj':page_info})

    return JsonResponse(data)

def add(request):
    nickname = request.POST.get('nickname')
    phone = request.POST.get('phone')
    lu = Users.objects.filter(phone=phone).first()
    if lu:
        data = {'status':0, 'msg':'user already exists, command failed'}
        return JsonResponse(data)
    sex = request.POST.get('sex')
    age = request.POST.get('age')
    if age == '':
        age = None
    school = request.POST.get('school')
    email = request.POST.get('email')
    ulike = request.POST.get('ulike')
    major = request.POST.get('major')
    cts = dateUtil.get_now_ts()
    upass = md5Util.get_default_pwd()
    Users.objects.create(nickname=nickname,
                        phone=phone,
                        sex=sex,
                        age=age,
                        school=school,
                        email=email,
                        ulike=ulike,
                        major=major,
                        cts=cts,
                        upass=upass,)

    data = ({'status':1,'msg':'add success'})

    return JsonResponse(data)