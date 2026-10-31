import secrets
from functools import wraps

from django.contrib.auth.hashers import check_password, make_password
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST
from rest_framework import serializers

from forum_django.jf3qApp.models import Users
from forum_django.jf3qApp.utils import dateUtil, pageUtil, uploadUtil


class UsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        exclude = ('upass',)


def _response(status, msg, obj=None, http_status=200):
    data = {'status': status, 'msg': msg}
    if obj is not None:
        data['obj'] = obj
    return JsonResponse(data, status=http_status)


def _legacy_md5(password):
    import hashlib

    return hashlib.md5(password.encode('utf-8')).hexdigest()


def _valid_password(user, raw_password):
    """Accept old MD5 records once, then upgrade them to Django's hasher."""
    if '$' in user.upass:
        return check_password(raw_password, user.upass)
    if secrets.compare_digest(user.upass, _legacy_md5(raw_password)):
        user.upass = make_password(raw_password)
        user.save(update_fields=('upass',))
        return True
    return False


def _current_admin(request):
    user_id = request.session.get('forum_user_id')
    if not user_id:
        return None
    return Users.objects.filter(id=user_id, state='1', role='admin').first()


def admin_required(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        django_user = getattr(request, 'user', None)
        is_staff = bool(
            django_user
            and django_user.is_authenticated
            and django_user.is_staff
        )
        if not is_staff and _current_admin(request) is None:
            return _response(0, 'Administrator login required', http_status=401)
        return view(request, *args, **kwargs)

    return wrapped


@require_GET
@ensure_csrf_cookie
def csrf_token(request):
    return _response(1, 'CSRF cookie set')


@require_POST
def login(request):
    phone = (request.POST.get('phone') or '').strip()
    raw_password = request.POST.get('upass') or ''
    if not phone or not raw_password:
        return _response(0, 'Phone and password are required', http_status=400)

    user = Users.objects.filter(phone=phone).first()
    if not user or not _valid_password(user, raw_password):
        return _response(0, 'Account or password is incorrect', http_status=401)
    if user.state != '1':
        return _response(0, 'Account is not available (' + (user.msg or '') + ')', http_status=403)

    request.session.cycle_key()
    request.session['forum_user_id'] = user.id
    safe_user = UsersSerializer(user).data
    return _response(1, 'Login Success', safe_user)


@require_POST
@admin_required
def save(request):
    query_data = {}
    nickname = (request.POST.get('nickname') or '').strip()
    phone = (request.POST.get('phone') or '').strip()
    state = request.POST.get('state')
    if nickname:
        query_data['nickname__icontains'] = nickname
    if phone:
        query_data['phone'] = phone
    if state in ('0', '1'):
        query_data['state'] = state

    users = Users.objects.filter(**query_data).order_by('-id')
    try:
        page_info = pageUtil.get_page(
            users,
            page_no=request.POST.get('pageNo'),
            page_size=request.POST.get('pageSize'),
        )
    except ValueError as exc:
        return _response(0, str(exc), http_status=400)
    page_info['list'] = UsersSerializer(page_info['list'], many=True).data
    return _response(1, 'Search success', page_info)


@require_POST
@admin_required
def add(request):
    user_id = request.POST.get('id')
    phone = (request.POST.get('phone') or '').strip()
    nickname = (request.POST.get('nickname') or '').strip()
    if not phone or not nickname:
        return _response(0, 'Phone and nickname are required', http_status=400)
    if user_id:
        try:
            user_id = int(user_id)
        except ValueError:
            return _response(0, 'User id must be an integer', http_status=400)
        if user_id < 1:
            return _response(0, 'User id must be a positive integer', http_status=400)
    if Users.objects.filter(phone=phone).exclude(id=user_id or 0).exists():
        return _response(0, 'Phone number already exists', http_status=409)

    age_raw = request.POST.get('age', '')
    if age_raw == '':
        age = None
    else:
        try:
            age = int(age_raw)
        except (TypeError, ValueError):
            return _response(0, 'Age must be an integer', http_status=400)
        if age < 0 or age > 150:
            return _response(0, 'Age must be between 0 and 150', http_status=400)

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
        if user is None:
            return _response(0, 'User not found', http_status=404)
        Users.objects.filter(id=user_id).update(**fields)
        return _response(1, 'Update success')

    temporary_password = secrets.token_urlsafe(12)
    user = Users.objects.create(
        **fields,
        cts=dateUtil.get_now_ts(),
        upass=make_password(temporary_password),
        state='1',
        msg='',
        role='pt',
    )
    return _response(
        1,
        'Add success; give the temporary password to the user securely',
        {'id': user.id, 'temporary_password': temporary_password},
    )


@require_POST
@admin_required
def upfaceimg(request):
    user_id = request.POST.get('id')
    uploaded_file = request.FILES.get('file')
    if not uploaded_file:
        return _response(0, 'Upload failed: file is required', http_status=400)
    user = None
    if user_id:
        user = Users.objects.filter(id=user_id).first()
        if user is None:
            return _response(0, 'User not found', http_status=404)
    try:
        faceimg = uploadUtil.upload(uploaded_file, 'faceimg')
    except ValueError as exc:
        return _response(0, str(exc), http_status=400)
    if user:
        old_faceimg = user.faceimg
        Users.objects.filter(id=user.id).update(faceimg=faceimg)
        uploadUtil.delfile(old_faceimg)
    return _response(1, 'Upload success', faceimg)


@require_POST
@admin_required
def del_one(request):
    user_id = request.POST.get('id')
    if not user_id:
        return _response(0, 'User id is required', http_status=400)
    user = Users.objects.filter(id=user_id).first()
    if user is None:
        return _response(0, 'User not found', http_status=404)
    Users.objects.filter(id=user.id).delete()
    uploadUtil.delfile(user.faceimg)
    return _response(1, 'Delete success')


@require_POST
@admin_required
def init_pwd(request):
    user_id = request.POST.get('id')
    if not user_id:
        return _response(0, 'User id is required', http_status=400)
    user = Users.objects.filter(id=user_id).first()
    if user is None:
        return _response(0, 'User not found', http_status=404)
    temporary_password = secrets.token_urlsafe(12)
    Users.objects.filter(id=user.id).update(upass=make_password(temporary_password))
    return _response(
        1,
        'Password reset; give the temporary password to the user securely',
        {'temporary_password': temporary_password},
    )


@require_POST
@admin_required
def change_state(request):
    user_id = request.POST.get('id')
    state = request.POST.get('state')
    if not user_id or state not in ('0', '1'):
        return _response(0, 'User id and a valid state (0 or 1) are required', http_status=400)
    user = Users.objects.filter(id=user_id).first()
    if user is None:
        return _response(0, 'User not found', http_status=404)
    Users.objects.filter(id=user.id).update(
        state=state,
        msg=request.POST.get('msg', user.msg),
    )
    return _response(1, 'State changed successfully')
