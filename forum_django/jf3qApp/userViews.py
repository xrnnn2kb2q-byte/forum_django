from django.forms.models import model_to_dict
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST
from rest_framework import serializers

from forum_django.jf3qApp.models import Users
from forum_django.jf3qApp.utils import dateUtil, md5Util, pageUtil, uploadUtil


class UsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        exclude = ('upass',)


def _find_user(user_id):
    try:
        return Users.objects.filter(id=int(user_id)).first()
    except (TypeError, ValueError):
        return None


@require_GET
@ensure_csrf_cookie
def csrf_token(request):
    return JsonResponse({'status': 1, 'msg': 'CSRF cookie set'})


@require_POST
def login(request):
    phone = request.POST.get('phone')
    password = request.POST.get('upass')
    if not phone or not password:
        return JsonResponse({'status': 0, 'msg': 'Phone and password are required'}, status=400)

    user = Users.objects.filter(phone=phone, upass=md5Util.calc_md5(password)).first()
    if not user:
        return JsonResponse({'status': 0, 'msg': 'Account or password is incorrect'})
    if user.state != '1':
        return JsonResponse({'status': 0, 'msg': 'Account is not available (' + (user.msg or '') + ')'})

    return JsonResponse({
        'status': 1,
        'msg': 'Login Success',
        'obj': model_to_dict(user, exclude=('upass',)),
    })


@require_POST
def save(request):
    query_data = {}
    nickname = request.POST.get('nickname')
    phone = request.POST.get('phone')
    state = request.POST.get('state')
    if nickname:
        query_data['nickname__icontains'] = nickname
    if phone:
        query_data['phone'] = phone
    if state:
        query_data['state'] = state

    users = Users.objects.filter(**query_data).order_by('-id')
    try:
        page_info = pageUtil.get_page(
            users,
            page_no=request.POST.get('pageNo'),
            page_size=request.POST.get('pageSize'),
        )
    except ValueError as exc:
        return JsonResponse({'status': 0, 'msg': str(exc)}, status=400)
    page_info['list'] = UsersSerializer(page_info['list'], many=True).data
    return JsonResponse({'status': 1, 'msg': 'search success', 'obj': page_info})


@require_POST
def add(request):
    user_id = request.POST.get('id')
    phone = request.POST.get('phone')
    nickname = request.POST.get('nickname')
    if not phone or not nickname:
        return JsonResponse({'status': 0, 'msg': 'Phone and nickname are required'}, status=400)
    if user_id:
        try:
            user_id = int(user_id)
        except ValueError:
            return JsonResponse({'status': 0, 'msg': 'Invalid user id'}, status=400)
        if user_id < 1:
            return JsonResponse({'status': 0, 'msg': 'Invalid user id'}, status=400)

    existing = Users.objects.filter(phone=phone).exclude(id=user_id or 0).first()
    if existing:
        return JsonResponse({'status': 0, 'msg': 'user already exists, command failed'})

    age = request.POST.get('age') or None
    if age is not None:
        try:
            age = int(age)
        except ValueError:
            return JsonResponse({'status': 0, 'msg': 'Age must be an integer'}, status=400)

    fields = {
        'nickname': nickname,
        'phone': phone,
        'sex': request.POST.get('sex', ''),
        'age': age,
        'school': request.POST.get('school', ''),
        'email': request.POST.get('email', ''),
        'ulike': request.POST.get('ulike', ''),
        'major': request.POST.get('major', ''),
        'faceimg': request.POST.get('faceimg') or uploadUtil.get_default_img(),
    }

    if user_id:
        user = Users.objects.filter(id=user_id).first()
        if not user:
            return JsonResponse({'status': 0, 'msg': 'user not found'}, status=404)
        Users.objects.filter(id=user_id).update(**fields)
        return JsonResponse({'status': 1, 'msg': 'update success'})

    Users.objects.create(
        **fields,
        cts=dateUtil.get_now_ts(),
        upass=md5Util.get_default_pwd(),
        state='1',
        msg='',
        role='pt',
    )
    return JsonResponse({'status': 1, 'msg': 'add success'})


@require_POST
def upfaceimg(request):
    user_id = request.POST.get('id')
    uploaded_file = request.FILES.get('file')
    if not uploaded_file:
        return JsonResponse({'status': 0, 'msg': 'upload failed'}, status=400)
    user = None
    if user_id:
        user = _find_user(user_id)
        if not user:
            return JsonResponse({'status': 0, 'msg': 'user not found'}, status=404)
    try:
        faceimg = uploadUtil.upload(uploaded_file, 'faceimg')
    except ValueError as exc:
        return JsonResponse({'status': 0, 'msg': str(exc)}, status=400)
    if user:
        old_faceimg = user.faceimg
        Users.objects.filter(id=user.id).update(faceimg=faceimg)
        uploadUtil.delfile(old_faceimg)
    return JsonResponse({'status': 1, 'msg': 'upload success', 'obj': faceimg})


@require_POST
def del_one(request):
    user_id = request.POST.get('id')
    if not user_id:
        return JsonResponse({'status': 0, 'msg': 'user id is required'}, status=400)
    user = _find_user(user_id)
    if not user:
        return JsonResponse({'status': 0, 'msg': 'delete failed'}, status=404)
    user.delete()
    uploadUtil.delfile(user.faceimg)
    return JsonResponse({'status': 1, 'msg': 'delete success'})


@require_POST
def init_pwd(request):
    user_id = request.POST.get('id')
    if not user_id:
        return JsonResponse({'status': 0, 'msg': 'init failed'}, status=400)
    user = _find_user(user_id)
    if not user:
        return JsonResponse({'status': 0, 'msg': 'user not found'}, status=404)
    user.upass = md5Util.get_default_pwd()
    user.save(update_fields=('upass',))
    return JsonResponse({'status': 1, 'msg': 'password inited: 123456'})


@require_POST
def change_state(request):
    user_id = request.POST.get('id')
    state = request.POST.get('state')
    if not user_id or state not in ('0', '1'):
        return JsonResponse({'status': 0, 'msg': 'id and valid state are required'}, status=400)
    user = _find_user(user_id)
    if not user:
        return JsonResponse({'status': 0, 'msg': 'user not found'}, status=404)
    user.state = state
    user.msg = request.POST.get('msg', '')
    user.save(update_fields=('state', 'msg'))
    return JsonResponse({'status': 1, 'msg': 'state changed successfully'})
